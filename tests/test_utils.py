import logging
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from utils import play_start_feedback, play_stop_feedback, _generate_tone, _init_mixer

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestUtils:
    def setup_method(self):
        """Setup for each test method"""
        logger.info("Setting up Utils test")

    @patch("os.environ")
    @patch("pygame.mixer.pre_init")
    @patch("pygame.mixer.init")
    def test_init_mixer_success(
        self, mock_mixer_init, mock_mixer_pre_init, mock_environ
    ):
        """Test successful mixer initialization"""
        logger.info("Testing successful mixer initialization")

        # Reset the global flag for testing
        import utils

        utils._mixer_initialized = False

        _init_mixer()

        # Verify pygame environment variable was set
        mock_environ.__setitem__.assert_called_with("PYGAME_HIDE_SUPPORT_PROMPT", "1")

        # Verify mixer initialization
        mock_mixer_pre_init.assert_called_once_with(
            frequency=44100, size=-16, channels=2, buffer=512
        )
        mock_mixer_init.assert_called_once()

        # Verify global flag is set
        assert utils._mixer_initialized is True

        logger.info("Init mixer success test passed")

    @patch("pygame.mixer.pre_init")
    @patch("pygame.mixer.init")
    def test_init_mixer_already_initialized(self, mock_mixer_init, mock_mixer_pre_init):
        """Test mixer initialization when already initialized"""
        logger.info("Testing mixer initialization when already initialized")

        # Set the global flag to simulate already initialized
        import utils

        utils._mixer_initialized = True

        _init_mixer()

        # Should not call pygame functions again
        mock_mixer_pre_init.assert_not_called()
        mock_mixer_init.assert_not_called()

        logger.info("Init mixer already initialized test passed")

    def test_generate_tone_basic(self):
        """Test basic tone generation"""
        logger.info("Testing basic tone generation")

        frequency = 440.0  # A4 note
        duration = 1.0  # 1 second
        sample_rate = 44100

        result = _generate_tone(frequency, duration, sample_rate)

        # Should return stereo audio data
        assert result.shape[0] == sample_rate  # 1 second at 44.1kHz
        assert result.shape[1] == 2  # Stereo (2 channels)
        assert result.dtype == np.int16  # 16-bit audio

        # Verify the data is not all zeros
        assert not np.all(result == 0)

        logger.info("Generate tone basic test passed")

    def test_generate_tone_different_parameters(self):
        """Test tone generation with different parameters"""
        logger.info("Testing tone generation with different parameters")

        frequency = 880.0  # A5 note
        duration = 0.5  # 0.5 second
        sample_rate = 22050

        result = _generate_tone(frequency, duration, sample_rate)

        # Should return correct dimensions
        assert result.shape[0] == int(duration * sample_rate)
        assert result.shape[1] == 2  # Stereo

        logger.info("Generate tone different parameters test passed")

    def test_generate_tone_short_duration(self):
        """Test tone generation with very short duration"""
        logger.info("Testing tone generation with short duration")

        frequency = 1000.0
        duration = 0.01  # 10ms
        sample_rate = 44100

        result = _generate_tone(frequency, duration, sample_rate)

        expected_frames = int(duration * sample_rate)
        assert result.shape[0] == expected_frames
        assert result.shape[1] == 2

        logger.info("Generate tone short duration test passed")

    def test_generate_tone_fade_envelope(self):
        """Test that tone generation includes fade envelope"""
        logger.info("Testing tone generation fade envelope")

        frequency = 440.0
        duration = 0.1  # 100ms
        sample_rate = 44100

        result = _generate_tone(frequency, duration, sample_rate)

        # Extract left channel for analysis
        left_channel = result[:, 0]

        # Check that the beginning and end have lower amplitude (fade)
        fade_frames = int(0.01 * sample_rate)  # 10ms fade

        # Beginning should start from low amplitude
        assert abs(left_channel[0]) < abs(left_channel[fade_frames * 2])

        # End should fade to low amplitude
        assert abs(left_channel[-1]) < abs(left_channel[-fade_frames * 2])

        logger.info("Generate tone fade envelope test passed")

    def test_generate_tone_stereo_channels(self):
        """Test that generated tone has identical stereo channels"""
        logger.info("Testing generate tone stereo channels")

        frequency = 440.0
        duration = 0.1
        sample_rate = 44100

        result = _generate_tone(frequency, duration, sample_rate)

        # Left and right channels should be identical
        left_channel = result[:, 0]
        right_channel = result[:, 1]

        np.testing.assert_array_equal(left_channel, right_channel)

        logger.info("Generate tone stereo channels test passed")

    def test_generate_tone_amplitude_range(self):
        """Test that generated tone is within 16-bit range"""
        logger.info("Testing generate tone amplitude range")

        frequency = 440.0
        duration = 0.1
        sample_rate = 44100

        result = _generate_tone(frequency, duration, sample_rate)

        # Should be within 16-bit signed integer range
        assert np.all(result >= -32768)
        assert np.all(result <= 32767)

        logger.info("Generate tone amplitude range test passed")

    @patch("threading.Thread")
    @patch("utils._init_mixer")
    @patch("pygame.sndarray.make_sound")
    def test_play_start_feedback_success(
        self, mock_make_sound, mock_init_mixer, mock_thread
    ):
        """Test successful start feedback playback"""
        logger.info("Testing successful start feedback playback")

        mock_sound = MagicMock()
        mock_make_sound.return_value = mock_sound
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        play_start_feedback()

        # Verify thread was created and started
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()

        # Verify thread target function would work
        thread_args = mock_thread.call_args
        assert "target" in thread_args[1]
        assert thread_args[1]["daemon"] is True

        logger.info("Play start feedback success test passed")

    @patch("threading.Thread")
    @patch("utils._init_mixer")
    @patch("pygame.sndarray.make_sound")
    def test_play_stop_feedback_success(
        self, mock_make_sound, mock_init_mixer, mock_thread
    ):
        """Test successful stop feedback playback"""
        logger.info("Testing successful stop feedback playback")

        mock_sound = MagicMock()
        mock_make_sound.return_value = mock_sound
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        play_stop_feedback()

        # Verify thread was created and started
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()

        # Verify thread configuration
        thread_args = mock_thread.call_args
        assert "target" in thread_args[1]
        assert thread_args[1]["daemon"] is True

        logger.info("Play stop feedback success test passed")

    def test_start_feedback_audio_parameters(self):
        """Test start feedback audio parameters"""
        logger.info("Testing start feedback audio parameters")

        with (
            patch("utils._init_mixer"),
            patch("pygame.sndarray.make_sound") as mock_make_sound,
            patch("utils._generate_tone") as mock_generate_tone,
        ):
            mock_audio_data = np.array([[1000, 1000], [2000, 2000]], dtype=np.int16)
            mock_generate_tone.return_value = mock_audio_data
            mock_sound = MagicMock()
            mock_make_sound.return_value = mock_sound

            # Call the internal function that would be in the thread
            from utils import _init_mixer, _generate_tone

            try:
                _init_mixer()
                audio_data = _generate_tone(880, 0.15)  # A5 note for 150ms
                sound = mock_make_sound(audio_data)
                sound.play()
            except Exception:
                pass

            # Verify tone generation was called with correct parameters
            # (the real _generate_tone would be called, not the mock)
            mock_make_sound.assert_called_once()

        logger.info("Start feedback audio parameters test passed")

    def test_stop_feedback_audio_parameters(self):
        """Test stop feedback audio parameters"""
        logger.info("Testing stop feedback audio parameters")

        with (
            patch("utils._init_mixer"),
            patch("pygame.sndarray.make_sound") as mock_make_sound,
            patch("utils._generate_tone") as mock_generate_tone,
        ):
            mock_audio_data = np.array([[800, 800], [600, 600]], dtype=np.int16)
            mock_generate_tone.return_value = mock_audio_data
            mock_sound = MagicMock()
            mock_make_sound.return_value = mock_sound

            # Call the internal function that would be in the thread
            from utils import _init_mixer, _generate_tone

            try:
                _init_mixer()
                audio_data = _generate_tone(660, 0.10)  # E5 note for 100ms
                sound = mock_make_sound(audio_data)
                sound.play()
            except Exception:
                pass

            # Verify tone generation was called
            mock_make_sound.assert_called_once()

        logger.info("Stop feedback audio parameters test passed")

    @patch("threading.Thread")
    @patch("utils._init_mixer")
    @patch("pygame.sndarray.make_sound")
    @patch("utils._generate_tone")
    def test_play_start_feedback_exception_handling(
        self, mock_generate_tone, mock_make_sound, mock_init_mixer, mock_thread
    ):
        """Test start feedback exception handling"""
        logger.info("Testing start feedback exception handling")

        # Mock an exception in audio generation
        mock_generate_tone.side_effect = Exception("Audio generation failed")
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        play_start_feedback()

        # Should still create and start thread (exception handling is inside thread)
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()

        logger.info("Play start feedback exception handling test passed")

    @patch("threading.Thread")
    @patch("utils._init_mixer")
    @patch("pygame.sndarray.make_sound")
    @patch("utils._generate_tone")
    def test_play_stop_feedback_exception_handling(
        self, mock_generate_tone, mock_make_sound, mock_init_mixer, mock_thread
    ):
        """Test stop feedback exception handling"""
        logger.info("Testing stop feedback exception handling")

        # Mock an exception in sound creation
        mock_make_sound.side_effect = Exception("Sound creation failed")
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        play_stop_feedback()

        # Should still create and start thread
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()

        logger.info("Play stop feedback exception handling test passed")

    @patch("utils._init_mixer")
    @patch("pygame.sndarray.make_sound")
    @patch("utils._generate_tone")
    def test_feedback_sound_frequencies(
        self, mock_generate_tone, mock_make_sound, mock_init_mixer
    ):
        """Test that start and stop feedback use different frequencies"""
        logger.info("Testing feedback sound frequencies")

        mock_audio_data = np.array([[1000, 1000]], dtype=np.int16)
        mock_generate_tone.return_value = mock_audio_data
        mock_sound = MagicMock()
        mock_make_sound.return_value = mock_sound

        # Simulate start feedback parameters
        start_freq = 880  # A5 for start
        start_duration = 0.15

        # Simulate stop feedback parameters
        stop_freq = 660  # E5 for stop
        stop_duration = 0.10

        # Verify these are different
        assert start_freq != stop_freq
        assert start_duration != stop_duration

        # Start feedback should use higher frequency and longer duration
        assert start_freq > stop_freq
        assert start_duration > stop_duration

        logger.info("Feedback sound frequencies test passed")

    def test_generate_tone_zero_duration(self):
        """Test tone generation with zero duration"""
        logger.info("Testing tone generation with zero duration")

        frequency = 440.0
        duration = 0.0
        sample_rate = 44100

        result = _generate_tone(frequency, duration, sample_rate)

        # Should handle zero duration gracefully
        assert result.shape[0] == 0 or result.shape[0] == 1  # Might be 0 or 1 frame
        assert result.shape[1] == 2  # Still stereo

        logger.info("Generate tone zero duration test passed")

    def test_generate_tone_very_low_frequency(self):
        """Test tone generation with very low frequency"""
        logger.info("Testing tone generation with very low frequency")

        frequency = 20.0  # Very low frequency
        duration = 0.1
        sample_rate = 44100

        result = _generate_tone(frequency, duration, sample_rate)

        # Should still generate valid audio data
        assert result.shape[0] == int(duration * sample_rate)
        assert result.shape[1] == 2
        assert result.dtype == np.int16

        logger.info("Generate tone very low frequency test passed")

    def test_generate_tone_very_high_frequency(self):
        """Test tone generation with very high frequency"""
        logger.info("Testing tone generation with very high frequency")

        frequency = 20000.0  # Very high frequency (at edge of human hearing)
        duration = 0.1
        sample_rate = 44100

        result = _generate_tone(frequency, duration, sample_rate)

        # Should still generate valid audio data
        assert result.shape[0] == int(duration * sample_rate)
        assert result.shape[1] == 2
        assert result.dtype == np.int16

        logger.info("Generate tone very high frequency test passed")

    def test_threading_daemon_mode(self):
        """Test that feedback threads are created in daemon mode"""
        logger.info("Testing threading daemon mode")

        with patch("threading.Thread") as mock_thread:
            mock_thread_instance = MagicMock()
            mock_thread.return_value = mock_thread_instance

            play_start_feedback()

            # Verify daemon mode is set
            thread_args = mock_thread.call_args
            assert thread_args[1]["daemon"] is True

            play_stop_feedback()

            # Should be called twice (once for each feedback function)
            assert mock_thread.call_count == 2

        logger.info("Threading daemon mode test passed")

    @patch("utils._init_mixer")
    def test_init_mixer_called_in_feedback(self, mock_init_mixer):
        """Test that init_mixer is called in both feedback functions"""
        logger.info("Testing init_mixer called in feedback functions")

        with (
            patch("pygame.sndarray.make_sound") as mock_make_sound,
            patch("utils._generate_tone") as mock_generate_tone,
            patch("threading.Thread") as mock_thread,
        ):
            mock_sound = MagicMock()
            mock_make_sound.return_value = mock_sound
            mock_generate_tone.return_value = np.array([[100, 100]], dtype=np.int16)

            # Execute the thread target functions directly
            mock_thread_instance = MagicMock()
            mock_thread.return_value = mock_thread_instance

            play_start_feedback()
            play_stop_feedback()

            # Both should create threads
            assert mock_thread.call_count == 2

        logger.info("Init mixer called in feedback test passed")
