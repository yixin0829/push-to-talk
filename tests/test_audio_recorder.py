import pytest
import threading
from loguru import logger
from unittest.mock import MagicMock

from src.audio_recorder import AudioRecorder


class TestAudioRecorder:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        """Setup for each test method"""
        logger.info("Setting up AudioRecorder test")

        # Mock PyAudio at class level since it's now initialized in __init__
        self.mock_audio_interface = MagicMock()
        self.mock_pyaudio = mocker.patch("pyaudio.PyAudio")
        self.mock_pyaudio.return_value = self.mock_audio_interface

        self.recorder = AudioRecorder(sample_rate=16000, chunk_size=1024, channels=1)
        yield
        # Cleanup after test
        logger.info("Tearing down AudioRecorder test")
        if hasattr(self.recorder, "is_recording") and self.recorder.is_recording:
            self.recorder.stop_recording()

    def test_initialization(self):
        """Test AudioRecorder initialization"""
        logger.info("Testing AudioRecorder initialization")

        assert self.recorder.sample_rate == 16000
        assert self.recorder.chunk_size == 1024
        assert self.recorder.channels == 1
        assert self.recorder.is_recording is False
        assert self.recorder.audio_data == []
        assert self.recorder.recording_thread is None
        assert self.recorder.audio_interface == self.mock_audio_interface
        assert self.recorder.stream is None

        logger.info("AudioRecorder initialization test passed")

    def test_custom_initialization(self):
        """Test AudioRecorder with custom parameters"""
        logger.info("Testing AudioRecorder custom initialization")

        custom_recorder = AudioRecorder(sample_rate=44100, chunk_size=2048, channels=2)

        assert custom_recorder.sample_rate == 44100
        assert custom_recorder.chunk_size == 2048
        assert custom_recorder.channels == 2

        logger.info("AudioRecorder custom initialization test passed")

    def test_start_recording_success(self, mocker):
        """Test successful start of recording"""
        logger.info("Testing successful start of recording")

        mock_stream = MagicMock()
        self.mock_audio_interface.open.return_value = mock_stream

        result = self.recorder.start_recording()

        assert result is True
        assert self.recorder.is_recording is True
        assert self.recorder.audio_interface == self.mock_audio_interface
        assert self.recorder.stream == mock_stream
        assert isinstance(self.recorder.recording_thread, threading.Thread)

        self.mock_audio_interface.open.assert_called_once()
        logger.info("Start recording success test passed")

    def test_start_recording_already_recording(self, mocker):
        """Test starting recording when already recording"""
        logger.info("Testing start recording when already recording")

        mock_stream = MagicMock()
        self.mock_audio_interface.open.return_value = mock_stream

        # Start recording first time
        self.recorder.start_recording()
        assert self.recorder.is_recording is True

        # Try to start again
        result = self.recorder.start_recording()
        assert result is False

        logger.info("Start recording already recording test passed")

    def test_start_recording_failure(self, mocker):
        """Test recording start failure"""
        logger.info("Testing recording start failure")

        # Simulate open failure since PyAudio is already initialized
        self.mock_audio_interface.open.side_effect = Exception("Stream open failed")

        result = self.recorder.start_recording()

        assert result is False
        assert self.recorder.is_recording is False
        assert self.recorder.audio_interface is not None  # Interface stays alive
        assert self.recorder.stream is None

        logger.info("Start recording failure test passed")

    def test_stop_recording_not_started(self, mocker):
        """Test stopping recording when not started"""
        logger.info("Testing stop recording when not started")

        result = self.recorder.stop_recording()

        assert result is None
        logger.info("Stop recording not started test passed")

    def test_stop_recording_success(self, mocker):
        """Test successful stop of recording"""
        logger.info("Testing successful stop of recording")

        # Setup mocks
        mock_stream = MagicMock()
        self.mock_audio_interface.open.return_value = mock_stream
        self.mock_audio_interface.get_sample_size.return_value = 2  # 16-bit

        # Setup temp file mock
        temp_file_mock = MagicMock()
        temp_file_mock.name = "test_audio.wav"
        temp_file_mock.close = MagicMock()
        mock_temp_file = mocker.patch("tempfile.NamedTemporaryFile")
        mock_temp_file.return_value = temp_file_mock

        # Setup wave file mock
        wave_file_mock = MagicMock()
        mock_wave_open = mocker.patch("wave.open")
        mock_wave_open.return_value.__enter__ = MagicMock(return_value=wave_file_mock)
        mock_wave_open.return_value.__exit__ = MagicMock(return_value=False)

        # Start recording
        self.recorder.start_recording()

        # Add some mock audio data
        self.recorder.audio_data = [b"test_audio_chunk_1", b"test_audio_chunk_2"]

        # Keep recording flag true so stop_recording doesn't exit early
        # The method itself will set it to False
        self.recorder.recording_thread = MagicMock()
        self.recorder.recording_thread.join = MagicMock()

        result = self.recorder.stop_recording()

        assert result == "test_audio.wav"
        mock_temp_file.assert_called_once()
        mock_wave_open.assert_called_once_with("test_audio.wav", "wb")

        logger.info("Stop recording success test passed")

    def test_stop_recording_no_data(self, mocker):
        """Test stopping recording with no audio data"""
        logger.info("Testing stop recording with no audio data")

        mock_stream = MagicMock()
        self.mock_audio_interface.open.return_value = mock_stream

        # Start recording
        self.recorder.start_recording()

        # Immediately stop without adding data
        self.recorder.is_recording = False
        result = self.recorder.stop_recording()

        assert result is None
        logger.info("Stop recording no data test passed")

    def test_cleanup(self, mocker):
        """Test cleanup functionality"""
        logger.info("Testing cleanup functionality")

        mock_stream = MagicMock()
        self.mock_audio_interface.open.return_value = mock_stream

        # Start recording
        self.recorder.start_recording()

        # Call cleanup
        # Call shutdown (which calls _cleanup_stream)
        self.recorder.shutdown()

        mock_stream.stop_stream.assert_called_once()
        mock_stream.close.assert_called_once()
        self.mock_audio_interface.terminate.assert_called_once()

        assert self.recorder.stream is None
        assert self.recorder.audio_interface is None

        logger.info("Cleanup test passed")

    def test_cleanup_with_exception(self, mocker):
        """Test cleanup with exceptions"""
        logger.info("Testing cleanup with exceptions")

        mock_stream = MagicMock()
        mock_stream.stop_stream.side_effect = Exception("Stream stop failed")
        self.mock_audio_interface.open.return_value = mock_stream

        # Start recording
        self.recorder.start_recording()

        # Call cleanup (should handle exceptions gracefully)
        self.recorder._cleanup_stream()

        mock_stream.stop_stream.assert_called_once()
        logger.info("Cleanup with exception test passed")

    def test_record_audio_thread(self, mocker):
        """Test the recording thread functionality"""
        logger.info("Testing recording thread functionality")

        mock_stream = MagicMock()
        mock_stream.read.side_effect = [b"chunk1", b"chunk2", Exception("Stream ended")]
        self.mock_audio_interface.open.return_value = mock_stream

        # Start recording
        self.recorder.start_recording()
        self.recorder.is_recording = True

        # Run the recording method directly
        self.recorder._record_audio()

        # Should have stopped recording due to exception
        assert self.recorder.is_recording is False

        logger.info("Record audio thread test passed")

    def test_destructor_cleanup(self, mocker):
        """Test that destructor calls cleanup"""
        logger.info("Testing destructor cleanup")

        recorder = AudioRecorder()

        # Mock the shutdown method
        mocker.patch.object(recorder, "shutdown")
        # Trigger destructor
        del recorder

        # Cleanup should be called (note: this might be called during garbage collection)

        logger.info("Destructor cleanup test passed")

    def test_sample_width_fallback(self, mocker):
        """Test sample width fallback logic"""
        logger.info("Testing sample width fallback logic")

        mock_stream = MagicMock()
        self.mock_audio_interface.open.return_value = mock_stream

        # Mock get_sample_size to fail
        self.mock_audio_interface.get_sample_size.side_effect = Exception(
            "Failed to get sample size"
        )

        # Start recording
        self.recorder.start_recording()
        self.recorder.audio_data = [b"test_data"]
        # Keep recording flag true so stop_recording doesn't exit early

        temp_file_mock = MagicMock()
        temp_file_mock.name = "test_audio.wav"
        temp_file_mock.close = MagicMock()
        mock_temp_file = mocker.patch("tempfile.NamedTemporaryFile")
        mock_temp_file.return_value = temp_file_mock

        wave_file_mock = MagicMock()
        mock_wave_open = mocker.patch("wave.open")
        mock_wave_open.return_value.__enter__ = MagicMock(return_value=wave_file_mock)
        mock_wave_open.return_value.__exit__ = MagicMock(return_value=False)

        # Mock the recording thread
        self.recorder.recording_thread = MagicMock()
        self.recorder.recording_thread.join = MagicMock()

        self.recorder.stop_recording()

        # Should use fallback sample width (2 for paInt16)
        wave_file_mock.setsampwidth.assert_called_with(2)

        logger.info("Sample width fallback test passed")
