import os
import sys
import time
from loguru import logger
import threading
import signal
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict, field
import json

from src.audio_recorder import AudioRecorder
from src.audio_processor import AudioProcessor
from src.transcription import Transcriber
from src.text_refiner import TextRefiner
from src.text_inserter import TextInserter
from src.hotkey_service import HotkeyService
from src.utils import play_start_feedback, play_stop_feedback


@dataclass
class PushToTalkConfig:
    """Configuration class for PushToTalk application."""

    # OpenAI settings
    openai_api_key: str = ""
    stt_model: str = "gpt-4o-mini-transcribe"
    refinement_model: str = "gpt-4.1-nano"

    # Audio settings
    sample_rate: int = 16000
    chunk_size: int = 1024
    channels: int = 1

    # Hotkey settings - will use platform-specific defaults if empty
    hotkey: str = field(
        default_factory=lambda: (
            f"{'cmd' if sys.platform == 'darwin' else 'ctrl'}+shift+space"
        )
    )
    toggle_hotkey: str = field(
        default_factory=lambda: (
            f"{'cmd' if sys.platform == 'darwin' else 'ctrl'}+shift+^"
        )
    )

    # Text insertion settings
    insertion_method: str = "clipboard"  # "clipboard" or "sendkeys"
    insertion_delay: float = 0.005

    # Feature flags
    enable_text_refinement: bool = True
    enable_logging: bool = True
    enable_audio_feedback: bool = True
    enable_audio_processing: bool = True
    debug_mode: bool = False

    # Audio processing settings (pydub-compatible)
    silence_threshold: float = -16.0  # dBFS threshold for pydub (negative value)
    min_silence_duration: float = 400.0  # milliseconds for pydub
    speed_factor: float = 1.5

    # Custom glossary for transcription refinement
    custom_glossary: list[str] = field(default_factory=list)

    def save_to_file(self, filepath: str):
        """Save configuration to JSON file."""
        with open(filepath, "w") as f:
            json.dump(asdict(self), f, indent=2)

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


class PushToTalkApp:
    def __init__(self, config: Optional[PushToTalkConfig] = None):
        """
        Initialize the PushToTalk application.

        Args:
            config: Configuration object. If None, default config is used.
        """
        self.config = config or PushToTalkConfig()

        # Validate OpenAI API key
        if not self.config.openai_api_key:
            self.config.openai_api_key = os.getenv("OPENAI_API_KEY")
            if not self.config.openai_api_key:
                raise ValueError(
                    "OpenAI API key is required. Set OPENAI_API_KEY environment variable or provide in config."
                )

        # Initialize components - this will be called by _initialize_components
        self.audio_recorder = None
        self.audio_processor = None
        self.transcriber = None
        self.text_refiner = None
        self.text_inserter = None
        self.hotkey_service = None

        # State management
        self.is_running = False
        self.processing_lock = threading.Lock()

        # Initialize all components
        self._initialize_components()

        logger.info("PushToTalk application initialized")

    def _initialize_components(self):
        """Initialize or reinitialize all components with current configuration."""
        # Clean up existing components if they exist
        if self.hotkey_service:
            self.hotkey_service.stop()

        # Initialize components
        self.audio_recorder = AudioRecorder(
            sample_rate=self.config.sample_rate,
            chunk_size=self.config.chunk_size,
            channels=self.config.channels,
        )

        self.audio_processor = (
            AudioProcessor(
                silence_threshold=self.config.silence_threshold,  # dBFS threshold for pydub
                min_silence_duration=self.config.min_silence_duration,  # milliseconds for pydub
                speed_factor=self.config.speed_factor,
                keep_silence=80,  # Keep 80ms of silence at chunk boundaries
                debug_mode=self.config.debug_mode,
            )
            if self.config.enable_audio_processing
            else None
        )

        self.transcriber = Transcriber(
            api_key=self.config.openai_api_key, model=self.config.stt_model
        )

        self.text_refiner = (
            TextRefiner(
                api_key=self.config.openai_api_key, model=self.config.refinement_model
            )
            if self.config.enable_text_refinement
            else None
        )

        # Set glossary if text refiner is enabled
        if self.text_refiner and self.config.custom_glossary:
            self.text_refiner.set_glossary(self.config.custom_glossary)

        self.text_inserter = TextInserter(insertion_delay=self.config.insertion_delay)

        self.hotkey_service = HotkeyService(
            hotkey=self.config.hotkey or None,
            toggle_hotkey=self.config.toggle_hotkey or None,
        )

        # Setup hotkey callbacks
        self.hotkey_service.set_callbacks(
            on_start_recording=self._on_start_recording,
            on_stop_recording=self._on_stop_recording,
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
        needs_reinit = (
            old_config.openai_api_key != new_config.openai_api_key
            or old_config.stt_model != new_config.stt_model
            or old_config.refinement_model != new_config.refinement_model
            or old_config.sample_rate != new_config.sample_rate
            or old_config.chunk_size != new_config.chunk_size
            or old_config.channels != new_config.channels
            or old_config.hotkey != new_config.hotkey
            or old_config.toggle_hotkey != new_config.toggle_hotkey
            or old_config.insertion_delay != new_config.insertion_delay
            or old_config.enable_text_refinement != new_config.enable_text_refinement
            or old_config.enable_audio_processing != new_config.enable_audio_processing
            or old_config.debug_mode != new_config.debug_mode
            or old_config.silence_threshold != new_config.silence_threshold
            or old_config.min_silence_duration != new_config.min_silence_duration
            or old_config.speed_factor != new_config.speed_factor
            or old_config.custom_glossary != new_config.custom_glossary
        )

        if needs_reinit:
            logger.info("Configuration changes require component reinitialization")
            self._initialize_components()
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

    def _on_start_recording(self):
        """Callback for when recording starts."""
        with self.processing_lock:
            # Play audio feedback if enabled
            if self.config.enable_audio_feedback:
                play_start_feedback()

            if not self.audio_recorder.start_recording():
                logger.error("Failed to start audio recording")

    def _on_stop_recording(self):
        """Callback for when recording stops."""
        # Play audio feedback immediately when hotkey is released
        if self.config.enable_audio_feedback:
            play_stop_feedback()

        def process_recording():
            with self.processing_lock:
                self._process_recorded_audio()

        # Process in a separate thread to avoid blocking the hotkey service
        processing_thread = threading.Thread(target=process_recording, daemon=True)
        processing_thread.start()

    def _process_recorded_audio(self):
        """Process the recorded audio through the full pipeline."""
        try:
            # Stop recording and get audio file
            logger.info("Processing recorded audio...")
            audio_file = self.audio_recorder.stop_recording()

            if not audio_file:
                logger.warning("No audio file to process")
                return

            # Get active window info for logging
            window_title = self.text_inserter.get_active_window_title()
            if window_title:
                logger.info(f"Target window: {window_title}")

            # Process audio if enabled (silence detection and speed-up)
            processed_audio_file = audio_file
            if self.audio_processor and self.config.enable_audio_processing:
                logger.info("Processing audio (silence detection and speed-up)...")
                processed_audio_file = self.audio_processor.process_audio_file(
                    audio_file
                )
                if not processed_audio_file:
                    logger.warning("Audio processing failed, using original audio")

            # Transcribe audio
            logger.info("Transcribing audio...")
            transcribed_text = self.transcriber.transcribe_audio(processed_audio_file)
            logger.info(f"Transcribed: {transcribed_text}")

            # Clean up temporary files (both original and processed if exists)
            logger.warning(
                "Transcription failed or returned empty text due to short audio"
            )
            for temp_file in set([audio_file, processed_audio_file]):
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                        logger.debug(f"Cleaned up temporary file: {temp_file}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up {temp_file}: {e}")

            if transcribed_text is None:
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
            success = self.text_inserter.insert_text(
                final_text, method=self.config.insertion_method
            )

            if success:
                logger.info("Text insertion successful")
            else:
                logger.error("Text insertion failed")

            # Clean up temporary files
            try:
                if processed_audio_file != audio_file and os.path.exists(
                    processed_audio_file
                ):
                    os.unlink(processed_audio_file)
                    logger.debug(
                        f"Cleaned up processed audio file: {processed_audio_file}"
                    )
                if os.path.exists(audio_file):
                    os.unlink(audio_file)
                    logger.debug(f"Cleaned up original audio file: {audio_file}")
            except Exception as cleanup_error:
                logger.warning(f"Error cleaning up audio files: {cleanup_error}")

        except Exception as e:
            logger.error(f"Error processing recorded audio: {e}")
            # Clean up temporary files even on error
            try:
                if (
                    "processed_audio_file" in locals()
                    and processed_audio_file != audio_file
                    and os.path.exists(processed_audio_file)
                ):
                    os.unlink(processed_audio_file)
                if "audio_file" in locals() and os.path.exists(audio_file):
                    os.unlink(audio_file)
            except Exception:
                pass  # Ignore cleanup errors during error handling

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
            self.text_refiner = (
                TextRefiner(
                    api_key=self.config.openai_api_key,
                    model=self.config.refinement_model,
                )
                if self.config.enable_text_refinement
                else None
            )

            # Set glossary if text refiner is enabled
            if self.text_refiner and self.config.custom_glossary:
                self.text_refiner.set_glossary(self.config.custom_glossary)

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
