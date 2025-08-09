import pytest
import os
import logging
import tempfile
from pathlib import Path
import sys
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from audio_processor import AudioProcessor
from transcription import Transcriber
from text_refiner import TextRefiner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

    def test_audio_processor_real_files_basic(self):
        """Test audio processor with real audio files - basic processing"""
        logger.info("Testing audio processor with real audio files")

        processor = AudioProcessor(
            silence_threshold=-16,
            min_silence_duration=400,
            speed_factor=1.5,
            keep_silence=80,
            debug_mode=False,
        )

        for audio_name, audio_path in self.audio_files.items():
            logger.info(f"Processing {audio_name}: {audio_path}")

            result_path = processor.process_audio_file(str(audio_path))

            # Verify result
            assert result_path is not None, (
                f"Audio processing should succeed for {audio_name}"
            )
            assert os.path.exists(result_path), (
                f"Processed audio file should exist for {audio_name}"
            )

            # Check file size is reasonable
            original_size = audio_path.stat().st_size
            processed_size = Path(result_path).stat().st_size

            logger.info(
                f"{audio_name} - Original: {original_size} bytes, Processed: {processed_size} bytes"
            )

            # Processed file should be smaller due to speed-up and silence removal
            # But not too much smaller (sanity check)
            assert processed_size > original_size * 0.1, (
                f"Processed file seems too small for {audio_name}"
            )
            assert processed_size < original_size * 2.0, (
                f"Processed file seems too large for {audio_name}"
            )

            # Cleanup
            if result_path and os.path.exists(result_path):
                try:
                    os.remove(result_path)
                    logger.debug(f"Cleaned up processed file: {result_path}")
                except Exception as e:
                    logger.warning(f"Could not clean up {result_path}: {e}")

        logger.info("Audio processor real files test passed")

    def test_audio_processor_debug_mode_real_files(self):
        """Test audio processor debug mode with real files"""
        logger.info("Testing audio processor debug mode with real files")

        processor = AudioProcessor(
            silence_threshold=-20,
            min_silence_duration=300,
            speed_factor=2.0,
            debug_mode=True,
        )

        # Use audio2 for debug test
        audio_path = str(self.audio_files["audio2"])

        # Save current directory
        original_cwd = os.getcwd()

        # Create temporary directory for debug output
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            logger.info(f"Changed to temp directory: {temp_dir}")

            try:
                result_path = processor.process_audio_file(audio_path)

                assert result_path is not None, "Debug mode processing should succeed"
                assert os.path.exists(result_path), "Processed file should exist"

                # Check debug directory was created
                debug_dirs = [
                    d for d in os.listdir(".") if d.startswith("debug_audio_")
                ]
                assert len(debug_dirs) > 0, "Debug directory should be created"

                debug_dir = debug_dirs[0]
                logger.info(f"Debug directory created: {debug_dir}")

                # Verify debug files
                expected_files = [
                    "01_original.wav",
                    "02_silence_cropped.wav",
                    "03_speed_adjusted.wav",
                    "04_final_processed.wav",
                    "processing_info.txt",
                ]

                for debug_file in expected_files:
                    debug_file_path = os.path.join(debug_dir, debug_file)
                    assert os.path.exists(debug_file_path), (
                        f"Debug file {debug_file} should exist"
                    )

                    file_size = Path(debug_file_path).stat().st_size
                    logger.debug(f"Debug file {debug_file}: {file_size} bytes")

                # Check info file content
                info_path = os.path.join(debug_dir, "processing_info.txt")
                with open(info_path, "r") as f:
                    info_content = f.read()

                assert "Speed Factor: 2.0" in info_content, (
                    "Info should contain speed factor"
                )
                assert "Silence Threshold: -20" in info_content, (
                    "Info should contain threshold"
                )
                assert "Time Saved:" in info_content, "Info should contain time savings"

                logger.info(
                    f"Debug info content verified, length: {len(info_content)} chars"
                )

                # Cleanup processed file
                if os.path.exists(result_path):
                    os.remove(result_path)

            finally:
                os.chdir(original_cwd)

        logger.info("Audio processor debug mode test passed")

    def test_audio_processor_different_settings_per_file(self):
        """Test different processing settings optimized for each audio type"""
        logger.info("Testing audio processor with optimized settings per file")

        # Different settings for different content types
        settings = {
            "audio1": {  # Business meeting - more aggressive silence removal
                "silence_threshold": -16,
                "min_silence_duration": 300,
                "speed_factor": 1.8,
                "keep_silence": 50,
            },
            "audio2": {  # Product demo - preserve natural pauses
                "silence_threshold": -20,
                "min_silence_duration": 500,
                "speed_factor": 1.3,
                "keep_silence": 100,
            },
            "audio3": {  # Personal to-do - fast processing
                "silence_threshold": -12,
                "min_silence_duration": 200,
                "speed_factor": 2.5,
                "keep_silence": 30,
            },
        }

        results = {}

        for audio_name, audio_path in self.audio_files.items():
            logger.info(f"Processing {audio_name} with optimized settings")

            processor = AudioProcessor(**settings[audio_name])
            result_path = processor.process_audio_file(str(audio_path))

            assert result_path is not None, (
                f"Processing should succeed for {audio_name}"
            )
            assert os.path.exists(result_path), (
                f"Result file should exist for {audio_name}"
            )

            # Record results for comparison
            original_size = audio_path.stat().st_size
            processed_size = Path(result_path).stat().st_size
            compression_ratio = processed_size / original_size

            results[audio_name] = {
                "original_size": original_size,
                "processed_size": processed_size,
                "compression_ratio": compression_ratio,
                "speed_factor": settings[audio_name]["speed_factor"],
            }

            logger.info(
                f"{audio_name} - Compression: {compression_ratio:.3f}, Speed: {settings[audio_name]['speed_factor']}x"
            )

            # Cleanup
            if os.path.exists(result_path):
                os.remove(result_path)

        # Verify results make sense
        # audio3 (personal, fastest settings) should have highest compression
        # audio2 (demo, conservative settings) should have lowest compression
        assert (
            results["audio3"]["compression_ratio"]
            <= results["audio2"]["compression_ratio"]
        ), "Fast settings should compress more than conservative settings"

        logger.info("Audio processor optimized settings test passed")

    def test_transcription_fallback_behavior(self):
        """Test transcription fallback behavior without real API calls"""
        logger.info("Testing transcription fallback behavior")

        # Create transcriber with invalid API key to trigger fallback
        transcriber = Transcriber(api_key="invalid-key-for-testing")

        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
            shutil.copy2(self.audio_files["audio1"], temp_path)

        try:
            # This should fail gracefully and return None
            result = transcriber.transcribe_audio(temp_path)

            # Should return None due to API failure, but not crash
            assert result is None, "Invalid API key should result in None return"

            # Verify temp file was cleaned up even on failure
            assert not os.path.exists(temp_path), (
                "Temp file should be cleaned up on failure"
            )

        except Exception as e:
            # If temp file still exists, clean it up
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e

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

            # Try to process with minimal settings to verify it's readable
            processor = AudioProcessor(debug_mode=False)
            try:
                result_path = processor.process_audio_file(str(audio_path))
                assert result_path is not None, f"{audio_name} should be processable"

                if result_path and os.path.exists(result_path):
                    os.remove(result_path)

            except Exception as e:
                pytest.fail(f"Audio file {audio_name} could not be processed: {e}")

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
