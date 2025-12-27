import os
import sys
import time
from loguru import logger
import threading
import signal
import queue
from typing import Optional, Dict, Any
import json

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

from src.audio_recorder import AudioRecorder
from src.transcriber_factory import TranscriberFactory
from src.transcription_base import TranscriberBase
from src.text_refiner_base import TextRefinerBase
from src.text_refiner_factory import TextRefinerFactory
from src.text_inserter import TextInserter
from src.hotkey_service import HotkeyService
from src.utils import play_start_feedback, play_stop_feedback


def _get_default_hotkey() -> str:
    """Get platform-specific default hotkey."""
    return f"{'cmd' if sys.platform == 'darwin' else 'ctrl'}+shift+^"


def _get_default_toggle_hotkey() -> str:
    """Get platform-specific default toggle hotkey."""
    return f"{'cmd' if sys.platform == 'darwin' else 'ctrl'}+shift+space"


class PushToTalkConfig(BaseModel):
    """Configuration class for PushToTalk application with Pydantic validation."""

    model_config = ConfigDict(validate_assignment=True)

    # Transcription provider settings
    stt_provider: str = Field(
        default="deepgram", description="STT provider: 'openai' or 'deepgram'"
    )
    openai_api_key: str = Field(default="", description="OpenAI API key")
    deepgram_api_key: str = Field(default="", description="Deepgram API key")
    stt_model: str = Field(default="nova-3", description="STT model name")

    # Text refinement settings
    refinement_provider: str = Field(
        default="cerebras",
        description="Text refinement provider: 'openai', 'cerebras', or 'gemini'",
    )
    refinement_model: str = Field(
        default="llama-3.3-70b", description="Model for text refinement"
    )
    cerebras_api_key: str = Field(default="", description="Cerebras API key")
    gemini_api_key: str = Field(default="", description="Gemini API key")
    custom_endpoint: str = Field(
        default="",
        description="Custom API endpoint URL for OpenAI-compatible APIs",
    )

    # Audio settings
    sample_rate: int = Field(default=16000, gt=0, description="Audio sample rate in Hz")
    chunk_size: int = Field(default=1024, gt=0, description="Audio chunk size")
    channels: int = Field(default=1, gt=0, le=2, description="Audio channels (1 or 2)")

    # Hotkey settings - will use platform-specific defaults
    hotkey: str = Field(
        default_factory=_get_default_hotkey, description="Push-to-talk hotkey"
    )
    toggle_hotkey: str = Field(
        default_factory=_get_default_toggle_hotkey, description="Toggle hotkey"
    )

    # Feature flags
    enable_text_refinement: bool = Field(
        default=True, description="Enable text refinement"
    )
    enable_logging: bool = Field(default=True, description="Enable logging")
    enable_audio_feedback: bool = Field(
        default=True, description="Enable audio feedback"
    )
    debug_mode: bool = Field(default=False, description="Enable debug mode")

    # Custom glossary for transcription refinement
    custom_glossary: list[str] = Field(
        default_factory=list, description="Custom glossary terms"
    )

    # Custom refinement prompt
    custom_refinement_prompt: str = Field(
        default="",
        description="Custom text refinement prompt. Use {custom_glossary} placeholder for glossary terms.",
    )

    @field_validator("stt_provider")
    @classmethod
    def validate_stt_provider(cls, v: str) -> str:
        """Validate STT provider is either 'openai' or 'deepgram'."""
        if v not in ["openai", "deepgram"]:
            raise ValueError(f"stt_provider must be 'openai' or 'deepgram', got '{v}'")
        return v

    @field_validator("refinement_provider")
    @classmethod
    def validate_refinement_provider(cls, v: str) -> str:
        """Validate refinement provider is either 'openai' or 'cerebras'."""
        if v not in ["openai", "cerebras"]:
            raise ValueError(
                f"refinement_provider must be 'openai' or 'cerebras', got '{v}'"
            )
        return v

    @model_validator(mode="after")
    def validate_hotkeys_different(self) -> "PushToTalkConfig":
        """Validate that push-to-talk and toggle hotkeys are different."""
        if self.hotkey == self.toggle_hotkey:
            raise ValueError("Push-to-talk and toggle hotkeys must be different")
        return self

    def save_to_file(self, filepath: str):
        """Save configuration to JSON file."""
        with open(filepath, "w") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def load_from_file(cls, filepath: str) -> "PushToTalkConfig":
        """Load configuration from JSON file."""
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            return cls(**data)
        except Exception as e:
            logger.warning(f"Failed to load config from {filepath}: {e}")
            return cls()

    def requires_component_reinitialization(self, other: "PushToTalkConfig") -> bool:
        """
        Check if component reinitialization is required when comparing with another config.

        This method implements smart component reinitialization by categorizing fields
        as either "critical" (requiring expensive component recreation) or "non-critical"
        (runtime-only settings that can be updated without reinitialization).

        Critical Fields (require reinitialization):
        - API keys, model settings (transcriber/refiner must be recreated)
        - Audio parameters (audio recorder must be recreated)
        - Hotkeys (hotkey service must be recreated)
        - Processing settings (audio processor must be recreated)
        - Custom glossary (text refiner must be updated)

        Non-Critical Fields (runtime-only changes):
        - enable_logging: Runtime logging toggle
        - enable_audio_feedback: Runtime audio feedback toggle

        Args:
            other: The other configuration to compare against

        Returns:
            True if component reinitialization is needed, False otherwise
        """
        # Fields that do NOT require component reinitialization when changed
        # These are UI-only or runtime-only settings that don't affect core components
        non_critical_fields = {
            "enable_logging",  # Logging toggle (runtime setting)
            "enable_audio_feedback",  # Audio feedback toggle (runtime setting)
        }

        # Get all fields from the Pydantic model
        all_fields = set(self.__class__.model_fields.keys())

        # Compare all fields except the non-critical ones
        critical_fields = all_fields - non_critical_fields

        for field_name in critical_fields:
            if getattr(self, field_name) != getattr(other, field_name):
                return True

        return False


class PushToTalkApp:
    def __init__(
        self,
        config: Optional[PushToTalkConfig] = None,
        audio_recorder: Optional[AudioRecorder] = None,
        transcriber: Optional["TranscriberBase"] = None,
        text_refiner: Optional[TextRefinerBase] = None,
        text_inserter: Optional[TextInserter] = None,
        hotkey_service: Optional[HotkeyService] = None,
    ):
        """
        Initialize the PushToTalk application.

        Supports dependency injection for testing and customization. If dependencies
        are not provided, default instances will be created based on configuration.

        Args:
            config: Configuration object. If None, default config is used.
            audio_recorder: Optional AudioRecorder instance. If None, created from config.
            transcriber: Optional TranscriberBase instance. If None, created from config.
            text_refiner: Optional TextRefiner instance. If None, created from config.
            text_inserter: Optional TextInserter instance. If None, created from config.
            hotkey_service: Optional HotkeyService instance. If None, created from config.
        """
        self.config = config or PushToTalkConfig()

        # Validate API key based on selected provider
        if self.config.stt_provider == "openai":
            if not self.config.openai_api_key:
                self.config.openai_api_key = os.getenv("OPENAI_API_KEY")
                if not self.config.openai_api_key:
                    raise ValueError(
                        "OpenAI API key is required. Set OPENAI_API_KEY environment variable or provide in config."
                    )
        elif self.config.stt_provider == "deepgram":
            if not self.config.deepgram_api_key:
                self.config.deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
                if not self.config.deepgram_api_key:
                    raise ValueError(
                        "Deepgram API key is required. Set DEEPGRAM_API_KEY environment variable or provide in config."
                    )
        else:
            raise ValueError(f"Unknown STT provider: {self.config.stt_provider}")

        # Use injected dependencies or initialize to None (will be created in _initialize_components)
        self.audio_recorder = audio_recorder
        self.transcriber = transcriber
        self.text_refiner = text_refiner
        self.text_inserter = text_inserter
        self.hotkey_service = hotkey_service

        # Track which components were injected (to preserve them during reinitialization)
        self._injected_audio_recorder = audio_recorder is not None
        self._injected_transcriber = transcriber is not None
        self._injected_text_refiner = text_refiner is not None
        self._injected_text_inserter = text_inserter is not None
        self._injected_hotkey_service = hotkey_service is not None

        # State management
        self.is_running = False
        self.processing_lock = threading.Lock()

        # Command queue for handling hotkey events
        self.command_queue = queue.Queue()
        self.worker_thread = None

        # Initialize all components (only creates components that are None)
        self._initialize_components()

        logger.info("PushToTalk application initialized")

    def _initialize_components(self, force_recreate: bool = False):
        """Initialize or reinitialize all components with current configuration.

        Args:
            force_recreate: If True, recreate all components even if they exist.
                           If False, only create components that are None (injected dependencies).

        When force_recreate=False, injected dependencies are preserved (for testing).
        When force_recreate=True, all components are recreated (for configuration updates).
        """
        # Store whether hotkey service was running before cleanup
        hotkey_service_was_running = (
            self.hotkey_service and self.hotkey_service.is_service_running()
        )

        # Clean up existing components if they exist
        if self.hotkey_service:
            self.hotkey_service.stop_service()

        # Clean up audio recorder before recreating (PyAudio resources must be explicitly released)
        if self.audio_recorder and not self._injected_audio_recorder and force_recreate:
            self.audio_recorder.shutdown()

        # Determine which components to recreate
        # Never recreate injected components (preserves mocks for testing)
        # For non-injected components: recreate if force_recreate=True or if None
        recreate_audio_recorder = not self._injected_audio_recorder and (
            force_recreate or self.audio_recorder is None
        )
        recreate_transcriber = not self._injected_transcriber and (
            force_recreate or self.transcriber is None
        )
        recreate_text_refiner = not self._injected_text_refiner and (
            force_recreate or self.text_refiner is None
        )
        recreate_text_inserter = not self._injected_text_inserter and (
            force_recreate or self.text_inserter is None
        )
        recreate_hotkey_service = not self._injected_hotkey_service and (
            force_recreate or self.hotkey_service is None
        )

        # Initialize audio recorder
        if recreate_audio_recorder:
            self.audio_recorder = self._create_default_audio_recorder()

        # Initialize transcriber
        if recreate_transcriber:
            self.transcriber = self._create_default_transcriber()

        # Initialize text refiner
        if recreate_text_refiner:
            self.text_refiner = self._create_default_text_refiner()

        # Set glossary and custom prompt if text refiner is enabled
        if self.text_refiner:
            if self.config.custom_glossary:
                self.text_refiner.set_glossary(self.config.custom_glossary)
            if self.config.custom_refinement_prompt:
                self.text_refiner.set_custom_prompt(
                    self.config.custom_refinement_prompt
                )

        # Set glossary for transcriber if enabled
        if self.transcriber:
            self.transcriber.set_glossary(self.config.custom_glossary)

        # Initialize text inserter
        if recreate_text_inserter:
            self.text_inserter = self._create_default_text_inserter()

        # Initialize hotkey service
        if recreate_hotkey_service:
            self.hotkey_service = self._create_default_hotkey_service()

        # Setup hotkey callbacks
        self.hotkey_service.set_callbacks(
            on_start_recording=self._on_start_recording,
            on_stop_recording=self._on_stop_recording,
        )

        # Restart hotkey service if it was running before and application is still running
        if hotkey_service_was_running and self.is_running:
            self.hotkey_service.start_service()

    def _create_default_audio_recorder(self) -> AudioRecorder:
        """Create default AudioRecorder instance from configuration."""
        return AudioRecorder(
            sample_rate=self.config.sample_rate,
            chunk_size=self.config.chunk_size,
            channels=self.config.channels,
        )

    def _create_default_transcriber(self) -> TranscriberBase:
        """Create default TranscriberBase instance from configuration."""
        # Get the appropriate API key based on provider
        if self.config.stt_provider == "openai":
            api_key = self.config.openai_api_key or os.getenv("OPENAI_API_KEY")
        elif self.config.stt_provider == "deepgram":
            api_key = self.config.deepgram_api_key or os.getenv("DEEPGRAM_API_KEY")
        else:
            raise ValueError(f"Unknown STT provider: {self.config.stt_provider}")

        # Create transcriber using factory with glossary
        return TranscriberFactory.create_transcriber(
            provider=self.config.stt_provider,
            api_key=api_key,
            model=self.config.stt_model,
            glossary=self.config.custom_glossary,
        )

    def _create_default_text_refiner(self) -> Optional[TextRefinerBase]:
        """Create default TextRefiner instance from configuration."""
        if self.config.enable_text_refinement:
            # Get the appropriate API key based on provider
            if self.config.refinement_provider == "openai":
                api_key = self.config.openai_api_key or os.getenv("OPENAI_API_KEY")
            elif self.config.refinement_provider == "cerebras":
                api_key = self.config.cerebras_api_key or os.getenv("CEREBRAS_API_KEY")
            elif self.config.refinement_provider == "gemini":
                api_key = self.config.gemini_api_key or os.getenv("GOOGLE_API_KEY")
            else:
                raise ValueError(
                    f"Unknown refinement provider: {self.config.refinement_provider}"
                )

            if not api_key:
                raise ValueError(
                    f"{self.config.refinement_provider.upper()} API key is required for text refinement. "
                    f"Set {self.config.refinement_provider.upper()}_API_KEY environment variable or provide in config."
                )

            return TextRefinerFactory.create_refiner(
                provider=self.config.refinement_provider,
                api_key=api_key,
                model=self.config.refinement_model,
                glossary=self.config.custom_glossary,
                base_url=self.config.custom_endpoint or None,
            )
        return None

    def _create_default_text_inserter(self) -> TextInserter:
        """Create default TextInserter instance from configuration."""
        return TextInserter()

    def _create_default_hotkey_service(self) -> HotkeyService:
        """Create default HotkeyService instance from configuration."""
        return HotkeyService(
            hotkey=self.config.hotkey or None,
            toggle_hotkey=self.config.toggle_hotkey or None,
        )

    def update_configuration(self, new_config: PushToTalkConfig):
        """
        Update the application configuration and reinitialize components.

        Args:
            new_config: New configuration object
        """
        logger.info("Updating application configuration")

        # Store old config for comparison
        old_config = self.config
        self.config = new_config

        # Check if we need to reinitialize components
        if new_config.requires_component_reinitialization(old_config):
            logger.info("Configuration changes require component reinitialization")
            self._initialize_components(force_recreate=True)
        else:
            logger.info("Configuration updated without requiring component changes")

    def get_configuration(self) -> PushToTalkConfig:
        """Get the current configuration."""
        return self.config

    def save_configuration(self, filepath: str = "push_to_talk_config.json"):
        """Save current configuration to file."""
        self.config.save_to_file(filepath)
        logger.info(f"Configuration saved to {filepath}")

    def start(self, setup_signals=True):
        """Start the PushToTalk application.

        Args:
            setup_signals: Whether to setup signal handlers (only works in main thread)
        """
        if self.is_running:
            logger.warning("Application is already running")
            return

        logger.info("Starting PushToTalk application...")

        self.is_running = True

        # Start command processing worker thread
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

        self.hotkey_service.start_service()

        logger.info("PushToTalk is running.")
        logger.info(f"Push-to-talk: Press and hold '{self.config.hotkey}' to record.")
        logger.info(
            f"Toggle mode: Press '{self.config.toggle_hotkey}' to start/stop recording."
        )

        # Setup signal handlers for graceful shutdown (only in main thread)
        if setup_signals:
            try:
                signal.signal(signal.SIGINT, self._signal_handler)
                signal.signal(signal.SIGTERM, self._signal_handler)
            except ValueError as e:
                # This happens when not in main thread - just log and continue
                logger.debug(f"Could not setup signal handlers: {e}")

    def stop(self):
        """Stop the PushToTalk application."""
        if not self.is_running:
            logger.warning("Application is not running")
            return

        logger.info("Stopping PushToTalk application...")

        self.is_running = False
        self.hotkey_service.stop_service()

        # Signal worker thread to stop
        self.command_queue.put("QUIT")
        if self.worker_thread:
            self.worker_thread.join(timeout=2.0)
            self.worker_thread = None

        if self.audio_recorder:
            self.audio_recorder.shutdown()

        # No cleanup needed for audio feedback utility functions

        logger.info("PushToTalk application stopped")

    def run(self):
        """Run the application until stopped."""
        self.start()

        try:
            # Keep the main thread alive
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.stop()

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)

    def _worker_loop(self):
        """Worker loop to process commands from the queue."""
        logger.info("Worker thread started")
        while True:
            try:
                command = self.command_queue.get(timeout=0.5)
                if command == "QUIT":
                    break
                elif command == "START_RECORDING":
                    self._do_start_recording()
                elif command == "STOP_RECORDING":
                    self._do_stop_recording()
                else:
                    logger.warning(f"Unknown command received: {command}")

                self.command_queue.task_done()
            except queue.Empty:
                if not self.is_running:
                    break
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")

    def _on_start_recording(self):
        """Callback for when recording starts (called from hotkey thread)."""
        # Push command to queue to avoid blocking hotkey listener
        self.command_queue.put("START_RECORDING")

    def _on_stop_recording(self):
        """Callback for when recording stops (called from hotkey thread)."""
        # Push command to queue to avoid blocking hotkey listener
        self.command_queue.put("STOP_RECORDING")

    def _do_start_recording(self):
        """Internal method to perform start recording actions."""
        with self.processing_lock:
            # Play audio feedback if enabled
            if self.config.enable_audio_feedback:
                play_start_feedback()

            if not self.audio_recorder.start_recording():
                logger.error("Failed to start audio recording")

    def _do_stop_recording(self):
        """Internal method to perform stop recording actions."""
        # Play audio feedback immediately when hotkey is released
        if self.config.enable_audio_feedback:
            play_stop_feedback()

        # Process recording
        with self.processing_lock:
            self._process_recorded_audio()

    def _process_recorded_audio(self):
        """Process the recorded audio through the full pipeline."""
        try:
            # Stop recording and get audio file
            logger.info("Processing recorded audio...")
            audio_file = self.audio_recorder.stop_recording()

            if not audio_file:
                logger.warning("No audio file to process")
                return

            # Save audio file in debug mode before processing
            if self.config.debug_mode:
                self._save_debug_audio(audio_file)

            # Get active window info for logging
            window_title = self.text_inserter.get_active_window_title()
            if window_title:
                logger.info(f"Target window: {window_title}")

            # Transcribe audio
            logger.info("Transcribing audio...")
            transcribed_text = self.transcriber.transcribe_audio(audio_file)
            logger.info(f"Transcribed text: {transcribed_text}")

            # Clean up temporary audio file
            try:
                if os.path.exists(audio_file):
                    os.unlink(audio_file)
                    logger.debug(f"Cleaned up audio file: {audio_file}")
            except Exception as cleanup_error:
                logger.warning(f"Error cleaning up audio file: {cleanup_error}")

            if transcribed_text is None:
                logger.warning("Transcribed text is None, skipping refinement")
                return

            # Refine text if enabled (if failed, fallback to the original transcription)
            final_text = transcribed_text
            if self.text_refiner and self.config.enable_text_refinement:
                logger.info("Refining transcribed text...")
                refined_text = self.text_refiner.refine_text(transcribed_text)
                if refined_text:
                    final_text = refined_text
                    logger.info(f"Refined: {final_text}")

            # Insert text into active window
            logger.info("Inserting text into active window...")
            success = self.text_inserter.insert_text(final_text)

            if success:
                logger.info("Text insertion successful")
            else:
                logger.error("Text insertion failed")

        except Exception as e:
            logger.error(f"Error processing recorded audio: {e}")
            # Clean up temporary audio file even on error
            try:
                logger.debug(f"Cleaning up audio file: {audio_file}")
                if "audio_file" in locals() and os.path.exists(audio_file):
                    os.unlink(audio_file)
            except Exception:
                # Ignore cleanup errors during error handling
                logger.error(f"Error cleaning up audio file {audio_file}: {e}")

    def _save_debug_audio(self, audio_file: str):
        """
        Save recorded audio file to debug directory when debug mode is enabled.

        Args:
            audio_file: Path to the recorded audio file
        """
        try:
            import shutil
            from datetime import datetime

            # Create debug directory with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[
                :-3
            ]  # Remove last 3 digits of microseconds
            debug_dir = f"debug_audio_{timestamp}"
            os.makedirs(debug_dir, exist_ok=True)

            # Copy audio file to debug directory
            debug_audio_path = os.path.join(debug_dir, "recorded_audio.wav")
            shutil.copy2(audio_file, debug_audio_path)

            logger.info(f"Debug: Saved recorded audio to {debug_audio_path}")

            # Create info file with recording details
            info_path = os.path.join(debug_dir, "recording_info.txt")
            with open(info_path, "w") as f:
                f.write("Audio Recording Debug Information\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write("Settings:\n")
                f.write(f"  Sample Rate: {self.config.sample_rate} Hz\n")
                f.write(f"  Channels: {self.config.channels}\n")
                f.write(f"  Chunk Size: {self.config.chunk_size}\n")
                f.write("Configuration:\n")
                f.write(f"  STT Model: {self.config.stt_model}\n")
                f.write(
                    f"  Text Refinement: {'Enabled' if self.config.enable_text_refinement else 'Disabled'}\n"
                )
                if self.config.enable_text_refinement:
                    f.write(f"  Refinement Model: {self.config.refinement_model}\n")

            logger.info(f"Debug: Saved recording info to {info_path}")
            logger.info(f"Debug files saved to directory: {debug_dir}")

        except Exception as e:
            logger.error(f"Failed to save debug audio: {e}")

    def change_hotkey(self, new_hotkey: str) -> bool:
        """
        Change the push-to-talk hotkey combination.

        Args:
            new_hotkey: New push-to-talk hotkey combination

        Returns:
            True if hotkey was changed successfully
        """
        logger.info(
            f"Changing push-to-talk hotkey from '{self.config.hotkey}' to '{new_hotkey}'"
        )
        self.config.hotkey = new_hotkey

        # Reinitialize hotkey service with new hotkey
        if self.hotkey_service:
            self.hotkey_service.stop()

        self.hotkey_service = HotkeyService(
            hotkey=self.config.hotkey, toggle_hotkey=self.config.toggle_hotkey
        )
        self.hotkey_service.set_callbacks(
            on_start_recording=self._on_start_recording,
            on_stop_recording=self._on_stop_recording,
        )
        return True

    def change_toggle_hotkey(self, new_toggle_hotkey: str) -> bool:
        """
        Change the toggle hotkey combination.

        Args:
            new_toggle_hotkey: New toggle hotkey combination

        Returns:
            True if toggle hotkey was changed successfully
        """
        logger.info(
            f"Changing toggle hotkey from '{self.config.toggle_hotkey}' to '{new_toggle_hotkey}'"
        )
        self.config.toggle_hotkey = new_toggle_hotkey

        # Reinitialize hotkey service with new toggle hotkey
        if self.hotkey_service:
            self.hotkey_service.stop()

        self.hotkey_service = HotkeyService(
            hotkey=self.config.hotkey, toggle_hotkey=self.config.toggle_hotkey
        )
        self.hotkey_service.set_callbacks(
            on_start_recording=self._on_start_recording,
            on_stop_recording=self._on_stop_recording,
        )
        return True

    def toggle_text_refinement(self) -> bool:
        """
        Toggle text refinement on/off.

        Returns:
            New state of text refinement (True if enabled)
        """
        old_value = self.config.enable_text_refinement
        self.config.enable_text_refinement = not self.config.enable_text_refinement

        # Reinitialize text refiner if needed
        if old_value != self.config.enable_text_refinement:
            if self.config.enable_text_refinement:
                # Get the appropriate API key based on provider
                if self.config.refinement_provider == "openai":
                    api_key = self.config.openai_api_key or os.getenv("OPENAI_API_KEY")
                elif self.config.refinement_provider == "cerebras":
                    api_key = self.config.cerebras_api_key or os.getenv(
                        "CEREBRAS_API_KEY"
                    )
                elif self.config.refinement_provider == "gemini":
                    api_key = self.config.gemini_api_key or os.getenv("GOOGLE_API_KEY")
                else:
                    raise ValueError(
                        f"Unknown refinement provider: {self.config.refinement_provider}"
                    )

                self.text_refiner = TextRefinerFactory.create_refiner(
                    provider=self.config.refinement_provider,
                    api_key=api_key,
                    model=self.config.refinement_model,
                    glossary=self.config.custom_glossary,
                    base_url=self.config.custom_endpoint or None,
                )
            else:
                self.text_refiner = None

            # Set glossary for transcriber if enabled
            if self.transcriber:
                self.transcriber.set_glossary(self.config.custom_glossary)

        logger.info(
            f"Text refinement {'enabled' if self.config.enable_text_refinement else 'disabled'}"
        )
        return self.config.enable_text_refinement

    def toggle_audio_feedback(self) -> bool:
        """
        Toggle audio feedback on/off.

        Returns:
            New state of audio feedback (True if enabled)
        """
        self.config.enable_audio_feedback = not self.config.enable_audio_feedback

        # Audio feedback is now handled via utility functions - no service to manage

        logger.info(
            f"Audio feedback {'enabled' if self.config.enable_audio_feedback else 'disabled'}"
        )
        return self.config.enable_audio_feedback

    def get_status(self) -> Dict[str, Any]:
        """
        Get current application status.

        Returns:
            Dictionary containing status information
        """
        recording_mode = "idle"
        if hasattr(self.hotkey_service, "recording_state"):
            if self.hotkey_service.recording_state == "push_to_talk":
                recording_mode = "push-to-talk"
            elif self.hotkey_service.recording_state == "toggle":
                recording_mode = "toggle"

        return {
            "is_running": self.is_running,
            "hotkey": self.config.hotkey,
            "toggle_hotkey": self.config.toggle_hotkey,
            "recording_mode": recording_mode,
            "audio_feedback_enabled": self.config.enable_audio_feedback,
            "text_refinement_enabled": self.config.enable_text_refinement,
            "logging_enabled": self.config.enable_logging,
        }
