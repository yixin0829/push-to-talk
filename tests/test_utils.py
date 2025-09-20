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


def test_play_stop_feedback_missing_file_warns(monkeypatch, mock_logger):
    """Test stop feedback with missing file warns and doesn't crash."""
    missing_path = Path("/does/not/exist/stop.wav")
    playsound = MagicMock()

    monkeypatch.setattr(utils, "_STOP_SOUND_PATH", missing_path)
    monkeypatch.setattr(utils, "playsound", playsound)

    utils.play_stop_feedback()

    playsound.assert_not_called()
    mock_logger.warning.assert_called_once()


def test_play_start_feedback_logs_error_on_failure(tmp_path, monkeypatch, mock_logger):
    """Test start feedback logs error when playsound fails."""
    audio_path = tmp_path / "start.wav"
    audio_path.write_bytes(b"data")

    def failing_playsound(*_, **__):
        raise Exception("Playback failed")

    monkeypatch.setattr(utils, "_START_SOUND_PATH", audio_path)
    monkeypatch.setattr(utils, "playsound", failing_playsound)

    utils.play_start_feedback()

    mock_logger.error.assert_called_once()
