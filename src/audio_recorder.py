import pyaudio
import wave
import threading
import tempfile
from typing import Optional
from loguru import logger


class AudioRecorder:
    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
        channels: int = 1,
        audio_format: int = pyaudio.paInt16,
    ):
        """
        Initialize the audio recorder.

        Args:
            sample_rate: Sample rate in Hz (16kHz is optimal for Whisper)
            chunk_size: Size of audio chunks
            channels: Number of audio channels (1 for mono)
            audio_format: Audio format (16-bit is optimal for Whisper)
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.audio_format = audio_format

        self.is_recording = False
        self.audio_data = []
        self.recording_thread: Optional[threading.Thread] = None
        self.audio_interface = None
        self.stream = None

    def start_recording(self) -> bool:
        """Start recording audio."""
        if self.is_recording:
            logger.warning("Recording is already in progress")
            return False

        try:
            self.audio_interface = pyaudio.PyAudio()
            self.stream = self.audio_interface.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
            )

            self.is_recording = True
            self.audio_data = []

            self.recording_thread = threading.Thread(target=self._record_audio)
            self.recording_thread.start()

            logger.info("Audio recording started")
            return True

        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self._cleanup()
            return False

    def stop_recording(self) -> Optional[str]:
        """
        Stop recording and save audio to a temporary file.

        Returns:
            Path to the temporary audio file, or None if recording failed
        """
        if not self.is_recording:
            logger.warning("No recording in progress")
            return None

        self.is_recording = False

        # Wait for recording thread to finish
        if self.recording_thread:
            self.recording_thread.join(timeout=5.0)

        # Get sample width before cleanup
        sample_width = None
        if self.audio_interface:
            try:
                sample_width = self.audio_interface.get_sample_size(self.audio_format)
            except Exception as e:
                logger.warning(f"Could not get sample size from audio interface: {e}")
                # Fallback: calculate sample width from format
                if self.audio_format == pyaudio.paInt16:
                    sample_width = 2
                elif self.audio_format == pyaudio.paInt32:
                    sample_width = 4
                elif self.audio_format == pyaudio.paFloat32:
                    sample_width = 4
                else:
                    sample_width = 2  # Default to 16-bit

        self._cleanup()

        if not self.audio_data:
            logger.warning("No audio data recorded")
            return None

        if sample_width is None:
            logger.error("Could not determine sample width")
            return None

        # Save audio to temporary file
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_filename = temp_file.name
            temp_file.close()

            with wave.open(temp_filename, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(sample_width)
                wf.setframerate(self.sample_rate)
                wf.writeframes(b"".join(self.audio_data))

            logger.info(f"Audio saved to {temp_filename}")
            return temp_filename

        except Exception as e:
            logger.error(f"Failed to save audio: {e}")
            return None

    def _record_audio(self):
        """Internal method to record audio in a separate thread."""
        try:
            while self.is_recording and self.stream:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                self.audio_data.append(data)
        except Exception as e:
            logger.error(f"Error during recording: {e}")
            self.is_recording = False

    def _cleanup(self):
        """Clean up audio resources."""
        try:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None

            if self.audio_interface:
                self.audio_interface.terminate()
                self.audio_interface = None

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def __del__(self):
        """Destructor to ensure cleanup."""
        self._cleanup()
