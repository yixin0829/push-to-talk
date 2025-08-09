import os
import logging
from unittest.mock import patch
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from audio_processor import AudioProcessor

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestAudioProcessorSimple:
    def setup_method(self):
        """Setup for each test method"""
        logger.info("Setting up AudioProcessor simple test")
        self.processor = AudioProcessor()

    def test_initialization(self):
        """Test AudioProcessor initialization"""
        logger.info("Testing AudioProcessor initialization")

        assert self.processor.silence_threshold == -16
        assert self.processor.min_silence_duration == 400
        assert self.processor.speed_factor == 1.5
        assert self.processor.keep_silence == 80
        assert self.processor.debug_mode is False

        logger.info("AudioProcessor initialization test passed")

    @patch("pydub.AudioSegment.from_file")
    def test_process_audio_file_load_failure(self, mock_from_file):
        """Test audio file processing with load failure"""
        logger.info("Testing audio file processing with load failure")

        mock_from_file.side_effect = Exception("Failed to load audio file")

        result = self.processor.process_audio_file("nonexistent.wav")

        assert result is None
        logger.info("Process audio file load failure test passed")

    def test_custom_initialization(self):
        """Test AudioProcessor with custom parameters"""
        logger.info("Testing AudioProcessor custom initialization")

        custom_processor = AudioProcessor(
            silence_threshold=-20,
            min_silence_duration=300,
            speed_factor=2.0,
            keep_silence=100,
            debug_mode=True,
        )

        assert custom_processor.silence_threshold == -20
        assert custom_processor.min_silence_duration == 300
        assert custom_processor.speed_factor == 2.0
        assert custom_processor.keep_silence == 100
        assert custom_processor.debug_mode is True

        logger.info("AudioProcessor custom initialization test passed")
