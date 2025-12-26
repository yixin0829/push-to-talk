from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src import utils


@pytest.fixture
def mock_logger(monkeypatch):
    """Provide a mock logger to capture warnings and errors."""

    logger = MagicMock()
    monkeypatch.setattr(utils, "logger", logger)
    return logger


def test_play_start_feedback_plays_audio(tmp_path, monkeypatch, mock_logger):
    """The start feedback should play when the audio file exists."""

    audio_path = tmp_path / "start.wav"
    audio_path.write_bytes(b"data")

    playsound = MagicMock()
    monkeypatch.setattr(utils, "_START_SOUND_PATH", audio_path)
    monkeypatch.setattr(utils, "playsound", playsound)

    utils.play_start_feedback()

    playsound.assert_called_once_with(str(audio_path), block=False)
    mock_logger.warning.assert_not_called()


def test_play_start_feedback_missing_file_warns(monkeypatch, mock_logger):
    """A missing audio file should emit a warning and not play anything."""

    missing_path = Path("/does/not/exist/start.wav")
    playsound = MagicMock()

    monkeypatch.setattr(utils, "_START_SOUND_PATH", missing_path)
    monkeypatch.setattr(utils, "playsound", playsound)

    utils.play_start_feedback()

    playsound.assert_not_called()
    mock_logger.warning.assert_called_once()


def test_play_stop_feedback_logs_error_on_failure(tmp_path, monkeypatch, mock_logger):
    """Exceptions raised while playing stop feedback should be logged as errors."""

    audio_path = tmp_path / "stop.wav"
    audio_path.write_bytes(b"data")

    def failing_playsound(*_, **__):
        raise RuntimeError("boom")

    monkeypatch.setattr(utils, "_STOP_SOUND_PATH", audio_path)
    monkeypatch.setattr(utils, "playsound", failing_playsound)

    utils.play_stop_feedback()

    mock_logger.error.assert_called_once()


def test_play_start_feedback_logs_error_on_exception(
    tmp_path, monkeypatch, mock_logger
):
    """Exceptions raised while playing start feedback should be logged as errors."""

    audio_path = tmp_path / "start.wav"
    audio_path.write_bytes(b"data")

    def failing_playsound(*_, **__):
        raise RuntimeError("boom")

    monkeypatch.setattr(utils, "_START_SOUND_PATH", audio_path)
    monkeypatch.setattr(utils, "playsound", failing_playsound)

    utils.play_start_feedback()

    mock_logger.error.assert_called_once()


def test_play_stop_feedback_plays_audio(tmp_path, monkeypatch, mock_logger):
    """The stop feedback should play when the audio file exists."""

    audio_path = tmp_path / "stop.wav"
    audio_path.write_bytes(b"data")

    playsound = MagicMock()
    monkeypatch.setattr(utils, "_STOP_SOUND_PATH", audio_path)
    monkeypatch.setattr(utils, "playsound", playsound)

    utils.play_stop_feedback()

    playsound.assert_called_once_with(str(audio_path), block=False)
    mock_logger.warning.assert_not_called()


def test_play_stop_feedback_missing_file_warns(monkeypatch, mock_logger):
    """A missing audio file for stop feedback should emit a warning."""

    missing_path = Path("/does/not/exist/stop.wav")
    playsound = MagicMock()

    monkeypatch.setattr(utils, "_STOP_SOUND_PATH", missing_path)
    monkeypatch.setattr(utils, "playsound", playsound)

    utils.play_stop_feedback()

    playsound.assert_not_called()
    mock_logger.warning.assert_called_once()


def test_validate_audio_file_exists_returns_true(tmp_path, mock_logger):
    """validate_audio_file_exists should return True when file exists."""

    audio_file = tmp_path / "test.wav"
    audio_file.write_bytes(b"audio data")

    result = utils.validate_audio_file_exists(str(audio_file))

    assert result is True
    mock_logger.error.assert_not_called()


def test_validate_audio_file_exists_returns_false(mock_logger):
    """validate_audio_file_exists should return False when file doesn't exist."""

    result = utils.validate_audio_file_exists("/nonexistent/path/audio.wav")

    assert result is False
    mock_logger.error.assert_called_once()


def test_validate_audio_duration_accepts_valid_duration(tmp_path, mock_logger):
    """validate_audio_duration should return True for audio longer than threshold."""
    import wave
    import struct

    # Create a valid WAV file with sufficient duration (1 second)
    audio_file = tmp_path / "valid.wav"
    sample_rate = 16000
    duration_seconds = 1.0
    num_samples = int(sample_rate * duration_seconds)

    with wave.open(str(audio_file), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        # Write silent audio data
        wf.writeframes(struct.pack("<" + "h" * num_samples, *([0] * num_samples)))

    result = utils.validate_audio_duration(str(audio_file))

    assert result is True


def test_validate_audio_duration_rejects_short_audio(tmp_path, mock_logger):
    """validate_audio_duration should return False for audio shorter than threshold."""
    import wave
    import struct

    # Create a valid WAV file with very short duration (0.05 seconds < 0.3 threshold)
    audio_file = tmp_path / "short.wav"
    sample_rate = 16000
    duration_seconds = 0.05
    num_samples = int(sample_rate * duration_seconds)

    with wave.open(str(audio_file), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack("<" + "h" * num_samples, *([0] * num_samples)))

    result = utils.validate_audio_duration(str(audio_file))

    assert result is False
    mock_logger.info.assert_called_once()


def test_validate_audio_duration_returns_true_on_invalid_file(tmp_path, mock_logger):
    """validate_audio_duration should return True when file cannot be read as WAV."""

    # Create an invalid WAV file (just some random bytes)
    invalid_file = tmp_path / "invalid.wav"
    invalid_file.write_bytes(b"this is not a valid wav file")

    result = utils.validate_audio_duration(str(invalid_file))

    # Should return True to allow transcription attempt
    assert result is True
    mock_logger.debug.assert_called_once()


def test_validate_audio_duration_with_custom_threshold(tmp_path):
    """validate_audio_duration should respect custom min_duration parameter."""
    import wave
    import struct

    # Create a 0.5 second audio file
    audio_file = tmp_path / "medium.wav"
    sample_rate = 16000
    duration_seconds = 0.5
    num_samples = int(sample_rate * duration_seconds)

    with wave.open(str(audio_file), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack("<" + "h" * num_samples, *([0] * num_samples)))

    # Should pass with lower threshold
    assert utils.validate_audio_duration(str(audio_file), min_duration=0.3) is True

    # Should fail with higher threshold
    assert utils.validate_audio_duration(str(audio_file), min_duration=1.0) is False
