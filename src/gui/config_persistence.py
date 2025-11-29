"""Configuration file persistence for PushToTalk."""

import json
import threading
from dataclasses import asdict
from loguru import logger
from src.push_to_talk import PushToTalkConfig


class ConfigurationPersistence:
    """Handles saving and loading configuration files with async support."""

    def __init__(self):
        """Initialize the persistence manager."""
        self._save_lock = threading.Lock()
        self._save_pending = False

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
        - Deduplication: skips save if another save is already in progress
        - Error handling with logging but no GUI interruption

        Args:
            config: Configuration object to save
            filepath: Path to save the configuration JSON file
        """

        def _save_worker():
            """Background worker for saving configuration."""
            try:
                with self._save_lock:
                    if not self._save_pending:
                        return  # Another thread already completed the save

                    # Perform the actual save
                    config_data = asdict(config)
                    with open(filepath, "w") as f:
                        json.dump(config_data, f, indent=2)

                    logger.debug(f"Configuration auto-saved to {filepath}")
                    self._save_pending = False

            except Exception as error:
                logger.error(
                    f"Failed to auto-save configuration to {filepath}: {error}"
                )
                self._save_pending = False

        # Thread-safe check and mark save as pending
        with self._save_lock:
            if self._save_pending:
                # Save already in progress, skip this request
                return

            self._save_pending = True

        # Start background save
        save_thread = threading.Thread(target=_save_worker, daemon=True)
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
        config_data = asdict(config)
        with open(filepath, "w") as f:
            json.dump(config_data, f, indent=2)
        logger.info(f"Configuration saved to {filepath}")
