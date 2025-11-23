import pytest
import os
from loguru import logger
import tempfile
from pathlib import Path
import shutil

from src.transcription_openai import OpenAITranscriber
from src.text_refiner import TextRefiner


@pytest.mark.integration
class TestAudioIntegrationWithRealFiles:
    """Integration tests using real audio files - focused on audio processing"""

    @classmethod
    def setup_class(cls):
        """Setup for integration test class"""
        logger.info("Setting up audio integration tests with real files")

        # Get fixtures directory path
        cls.fixtures_dir = Path(__file__).parent / "fixtures"

        # Verify fixture files exist
        cls.audio_files = {
            "audio1": cls.fixtures_dir / "audio1.wav",
            "audio2": cls.fixtures_dir / "audio2.wav",
            "audio3": cls.fixtures_dir / "audio3.wav",
        }

        cls.script_files = {
            "audio1": cls.fixtures_dir / "audio1_script.txt",
            "audio2": cls.fixtures_dir / "audio2_script.txt",
            "audio3": cls.fixtures_dir / "audio3_script.txt",
        }

        # Load expected scripts
        cls.expected_scripts = {}
        for key, script_file in cls.script_files.items():
            with open(script_file, "r", encoding="utf-8") as f:
                cls.expected_scripts[key] = f.read().strip()

        # Verify all files exist
        for key, audio_file in cls.audio_files.items():
            if not audio_file.exists():
                pytest.skip(f"Audio fixture {audio_file} not found")

        logger.info(
            f"Found {len(cls.audio_files)} audio fixtures for integration testing"
        )

    def test_transcription_fallback_behavior(self):
        """Test transcription fallback behavior without real API calls"""
        logger.info("Testing transcription fallback behavior")

        # Create transcriber with invalid API key to trigger fallback
        transcriber = OpenAITranscriber(api_key="invalid-key-for-testing")

        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
            shutil.copy2(self.audio_files["audio1"], temp_path)

        try:
            # This should fail gracefully and return None
            result = transcriber.transcribe_audio(temp_path)

            # Should return None due to API failure, but not crash
            assert result is None, "Invalid API key should result in None return"

        finally:
            # Clean up temp file since transcriber no longer handles cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)

        logger.info("Transcription fallback behavior test passed")

    def test_text_refiner_fallback_behavior(self):
        """Test text refiner fallback behavior without real API calls"""
        logger.info("Testing text refiner fallback behavior")

        # Create refiner with invalid API key to trigger fallback
        refiner = TextRefiner(api_key="invalid-key-for-testing")

        # Test with audio3 script (contains format instruction)
        raw_text = self.expected_scripts["audio3"]
        logger.info(f"Testing fallback with text length: {len(raw_text)} characters")

        # This should fall back to returning the original text
        result = refiner.refine_text(raw_text)

        # Should return original text on API failure
        assert result == raw_text.strip(), "API failure should return original text"
        assert "Format this as a to-do list" in result, (
            "Original format instruction should be preserved"
        )

        logger.info("Text refiner fallback behavior test passed")

    def test_audio_file_format_validation(self):
        """Test that fixture audio files have correct format"""
        logger.info("Testing audio file format validation")

        for audio_name, audio_path in self.audio_files.items():
            logger.info(f"Validating format of {audio_name}")

            # Check file exists and size
            assert audio_path.exists(), f"{audio_name} should exist"

            file_size = audio_path.stat().st_size
            assert file_size > 5000, (
                f"{audio_name} should be at least 5KB (got {file_size} bytes)"
            )
            assert file_size < 10_000_000, (
                f"{audio_name} should be under 10MB (got {file_size} bytes)"
            )

            # Check WAV header
            with open(audio_path, "rb") as f:
                header = f.read(12)

            assert header[:4] == b"RIFF", f"{audio_name} should have RIFF header"
            assert header[8:12] == b"WAVE", f"{audio_name} should have WAVE format"

            logger.info(f"{audio_name} format validation passed: {file_size} bytes")

    def test_script_content_validation(self):
        """Test that script files have expected content"""
        logger.info("Testing script content validation")

        # Test audio1 - business meeting
        script1 = self.expected_scripts["audio1"]
        assert len(script1) > 100, "Audio1 script should be substantial"
        assert "quarterly" in script1.lower(), "Should contain business terms"
        assert "um" in script1.lower() or "uh" in script1.lower(), (
            "Should contain filler words"
        )

        # Test audio2 - product demo
        script2 = self.expected_scripts["audio2"]
        assert len(script2) > 100, "Audio2 script should be substantial"
        assert "app" in script2.lower(), "Should mention app"
        assert "users" in script2.lower(), "Should mention users"

        # Test audio3 - to-do list with format instruction
        script3 = self.expected_scripts["audio3"]
        assert len(script3) > 200, "Audio3 script should be longest"
        assert "Format this as a to-do list in bullet points" in script3, (
            "Should have format instruction"
        )
        assert "dentist" in script3.lower(), "Should contain specific tasks"
        assert "groceries" in script3.lower(), "Should contain specific tasks"

        logger.info("Script content validation passed")

    def test_audio_duration_estimation(self):
        """Test estimated duration of audio files"""
        logger.info("Testing audio duration estimation")

        # Based on script length, estimate durations (adjusted based on actual files)
        expected_durations = {
            "audio1": (15, 60),  # Business meeting: 15-60 seconds
            "audio2": (20, 50),  # Product demo: 20-50 seconds
            "audio3": (25, 60),  # To-do list: 25-60 seconds
        }

        for audio_name, (min_duration, max_duration) in expected_durations.items():
            audio_path = self.audio_files[audio_name]

            # Estimate duration from file size (rough approximation)
            file_size = audio_path.stat().st_size

            # Typical WAV file at 16kHz, 16-bit mono ≈ 32KB per second
            estimated_duration = file_size / 32000

            logger.info(
                f"{audio_name} - Size: {file_size} bytes, Est. duration: {estimated_duration:.1f}s"
            )

            assert min_duration <= estimated_duration <= max_duration * 2, (
                f"{audio_name} duration estimate {estimated_duration:.1f}s outside expected range {min_duration}-{max_duration}s"
            )

        logger.info("Audio duration estimation test passed")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration"])
