"""Configuration file persistence for PushToTalk."""

import json
import threading
from typing import Optional, Tuple
from loguru import logger
from src.push_to_talk import PushToTalkConfig


class ConfigurationPersistence:
    """Handles saving and loading configuration files with async support."""

    def __init__(self):
        """Initialize the persistence manager."""
        self._save_lock = threading.Lock()
        self._save_in_progress = False
        self._queued_save: Optional[Tuple[PushToTalkConfig, str]] = None

    def save_async(
        self, config: PushToTalkConfig, filepath: str = "push_to_talk_config.json"
    ):
        """
        Save configuration to JSON file asynchronously.

        This method provides non-blocking save functionality during runtime updates,
        ensuring configuration changes are persisted without affecting GUI responsiveness.

        Features:
        - Thread-safe with lock to prevent concurrent save operations
        - Non-blocking background save using daemon thread
        - Deduplication: queues latest config when save is in progress (doesn't discard)
        - Error handling with logging but no GUI interruption

        Args:
            config: Configuration object to save
            filepath: Path to save the configuration JSON file
        """

        def _save_worker(cfg: PushToTalkConfig, path: str):
            """Background worker for saving configuration."""
            while True:
                try:
                    # Perform the actual save
                    config_data = cfg.model_dump()
                    with open(path, "w") as f:
                        json.dump(config_data, f, indent=2)

                    logger.debug(f"Configuration auto-saved to {path}")

                except Exception as error:
                    logger.error(
                        f"Failed to auto-save configuration to {path}: {error}"
                    )

                # Check if there's a queued save to process
                with self._save_lock:
                    if self._queued_save is not None:
                        # Process the queued save
                        cfg, path = self._queued_save
                        self._queued_save = None
                        # Continue the loop to save the queued config
                    else:
                        # No more saves queued, mark as complete and exit
                        self._save_in_progress = False
                        break

        # Thread-safe check and either start save or queue
        with self._save_lock:
            if self._save_in_progress:
                # Save already in progress, queue this config (overwrites any previous queue)
                self._queued_save = (config, filepath)
                return

            self._save_in_progress = True

        # Start background save
        save_thread = threading.Thread(
            target=_save_worker, args=(config, filepath), daemon=True
        )
        save_thread.start()

    def save_sync(
        self, config: PushToTalkConfig, filepath: str = "push_to_talk_config.json"
    ):
        """
        Save configuration to JSON file synchronously.

        Args:
            config: Configuration object to save
            filepath: Path to save the configuration JSON file

        Raises:
            Exception: If save operation fails
        """
        config_data = config.model_dump()
        with open(filepath, "w") as f:
            json.dump(config_data, f, indent=2)
        logger.info(f"Configuration saved to {filepath}")
