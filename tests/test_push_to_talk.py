from collections import defaultdict
from dataclasses import replace
import sys
import types

import pytest

pyautogui_stub = types.SimpleNamespace(
    hotkey=lambda *_, **__: None,
    write=lambda *_, **__: None,
    getActiveWindow=lambda: None,
)

sys.modules.setdefault("mouseinfo", types.SimpleNamespace())
sys.modules.setdefault("pyautogui", pyautogui_stub)

from src import push_to_talk


class InstanceTracker(defaultdict):
    """Helper to capture created dependency instances."""

    def __init__(self):
        super().__init__(list)

    def last(self, key):
        return self[key][-1]


@pytest.fixture
def dependency_stubs(monkeypatch):
    """Patch push_to_talk dependencies with controllable fakes."""

    tracker = InstanceTracker()

    class StubAudioRecorder:
        def __init__(self, sample_rate, chunk_size, channels):
            self.sample_rate = sample_rate
            self.chunk_size = chunk_size
            self.channels = channels
            self.start_calls = 0
            self.stop_calls = 0
            self.should_start = True
            self.audio_file = None
            tracker["audio_recorder"].append(self)

        def start_recording(self):
            self.start_calls += 1
            return self.should_start

        def stop_recording(self):
            self.stop_calls += 1
            return self.audio_file

    class StubAudioProcessor:
        def __init__(
            self,
            silence_threshold,
            min_silence_duration,
            speed_factor,
            keep_silence,
            debug_mode,
        ):
            self.silence_threshold = silence_threshold
            self.min_silence_duration = min_silence_duration
            self.speed_factor = speed_factor
            self.keep_silence = keep_silence
            self.debug_mode = debug_mode
            self.last_input = None
            self.next_result = None
            tracker["audio_processor"].append(self)

        def process_audio_file(self, audio_file):
            self.last_input = audio_file
            return self.next_result

    class StubTranscriber:
        def __init__(self, api_key, model):
            self.api_key = api_key
            self.model = model
            self.last_path = None
            self.result = "transcribed text"
            tracker["transcriber"].append(self)

        def transcribe_audio(self, audio_path):
            self.last_path = audio_path
            return self.result

    class StubTextRefiner:
        def __init__(self, api_key, model):
            self.api_key = api_key
            self.model = model
            self.glossary = None
            self.last_input = None
            self.result = "refined text"
            self.calls = 0
            tracker["text_refiner"].append(self)

        def set_glossary(self, glossary):
            self.glossary = glossary

        def refine_text(self, text):
            self.calls += 1
            self.last_input = text
            return self.result

    class StubTextInserter:
        def __init__(self, insertion_delay):
            self.insertion_delay = insertion_delay
            self.last_text = None
            self.last_method = None
            self.insert_calls = 0
            self.should_succeed = True
            self.window_title = "TestWindow"
            tracker["text_inserter"].append(self)

        def insert_text(self, text, method):
            self.insert_calls += 1
            self.last_text = text
            self.last_method = method
            return self.should_succeed

        def get_active_window_title(self):
            return self.window_title

    class StubHotkeyService:
        def __init__(self, hotkey=None, toggle_hotkey=None):
            self.hotkey = hotkey
            self.toggle_hotkey = toggle_hotkey
            self.callbacks = None
            self.start_calls = 0
            self.stop_service_calls = 0
            self.stop_calls = 0
            self.should_start = True
            self.recording_state = "idle"
            tracker["hotkey_service"].append(self)

        def set_callbacks(self, on_start_recording, on_stop_recording):
            self.callbacks = (on_start_recording, on_stop_recording)

        def start_service(self):
            self.start_calls += 1
            return self.should_start

        def stop_service(self):
            self.stop_service_calls += 1

        def stop(self):
            self.stop_calls += 1

    monkeypatch.setattr(push_to_talk, "AudioRecorder", StubAudioRecorder)
    monkeypatch.setattr(push_to_talk, "AudioProcessor", StubAudioProcessor)
    monkeypatch.setattr(push_to_talk, "Transcriber", StubTranscriber)
    monkeypatch.setattr(push_to_talk, "TextRefiner", StubTextRefiner)
    monkeypatch.setattr(push_to_talk, "TextInserter", StubTextInserter)
    monkeypatch.setattr(push_to_talk, "HotkeyService", StubHotkeyService)

    return tracker


@pytest.fixture
def make_app(dependency_stubs):
    """Factory to create PushToTalkApp instances with the stubbed dependencies."""

    def factory(config=None):
        config = config or push_to_talk.PushToTalkConfig(openai_api_key="test-key")
        return push_to_talk.PushToTalkApp(config)

    return factory


@pytest.fixture
def feedback_spy(monkeypatch):
    """Track calls to the audio feedback helpers."""

    calls = {"start": 0, "stop": 0}

    def fake_start():
        calls["start"] += 1

    def fake_stop():
        calls["stop"] += 1

    monkeypatch.setattr(push_to_talk, "play_start_feedback", fake_start)
    monkeypatch.setattr(push_to_talk, "play_stop_feedback", fake_stop)

    return calls


@pytest.fixture
def immediate_thread(monkeypatch):
    """Run thread targets immediately to simplify testing."""

    class ImmediateThread:
        def __init__(self, target, daemon=None):
            self.target = target
            self.daemon = daemon
            self.started = False

        def start(self):
            self.started = True
            self.target()

    monkeypatch.setattr(push_to_talk.threading, "Thread", ImmediateThread)


def test_config_save_and_load_roundtrip(tmp_path):
    config = push_to_talk.PushToTalkConfig(
        openai_api_key="key",
        stt_model="model-a",
        refinement_model="model-b",
        sample_rate=44100,
        chunk_size=2048,
        channels=2,
        hotkey="ctrl+alt+s",
        toggle_hotkey="ctrl+alt+t",
        insertion_method="sendkeys",
        insertion_delay=0.01,
        enable_text_refinement=False,
        enable_logging=False,
        enable_audio_feedback=False,
        enable_audio_processing=False,
        debug_mode=True,
        silence_threshold=-20.0,
        min_silence_duration=300.0,
        speed_factor=1.2,
        custom_glossary=["term1", "term2"],
    )

    path = tmp_path / "config.json"
    config.save_to_file(path)

    loaded = push_to_talk.PushToTalkConfig.load_from_file(path)

    assert loaded == config


def test_load_config_failure_returns_default(tmp_path):
    broken_path = tmp_path / "broken.json"
    broken_path.write_text("{")

    loaded = push_to_talk.PushToTalkConfig.load_from_file(broken_path)

    assert isinstance(loaded, push_to_talk.PushToTalkConfig)
    assert loaded.hotkey  # default values are preserved


def test_initialization_wires_dependencies(make_app, dependency_stubs):
    config = push_to_talk.PushToTalkConfig(
        openai_api_key="key",
        custom_glossary=["ChatGPT"],
    )

    app = make_app(config)

    recorder = dependency_stubs.last("audio_recorder")
    processor = dependency_stubs.last("audio_processor")
    transcriber = dependency_stubs.last("transcriber")
    refiner = dependency_stubs.last("text_refiner")
    inserter = dependency_stubs.last("text_inserter")
    hotkey_service = dependency_stubs.last("hotkey_service")

    assert recorder.sample_rate == config.sample_rate
    assert processor.silence_threshold == config.silence_threshold
    assert transcriber.api_key == config.openai_api_key
    assert refiner.glossary == config.custom_glossary
    assert inserter.insertion_delay == config.insertion_delay
    assert hotkey_service.hotkey == config.hotkey
    assert hotkey_service.callbacks == (app._on_start_recording, app._on_stop_recording)


def test_start_and_stop_application(make_app, dependency_stubs):
    app = make_app()
    hotkey_service = dependency_stubs.last("hotkey_service")

    app.start(setup_signals=False)

    assert app.is_running is True
    assert hotkey_service.start_calls == 1

    app.stop()

    assert app.is_running is False
    assert hotkey_service.stop_service_calls == 1

    app.stop()  # second stop should be a no-op
    assert hotkey_service.stop_service_calls == 1


def test_process_recorded_audio_pipeline(
    make_app,
    dependency_stubs,
    feedback_spy,
    immediate_thread,
    tmp_path,
):
    app = make_app()

    recorder = dependency_stubs.last("audio_recorder")
    processor = dependency_stubs.last("audio_processor")
    transcriber = dependency_stubs.last("transcriber")
    refiner = dependency_stubs.last("text_refiner")
    inserter = dependency_stubs.last("text_inserter")

    audio_path = tmp_path / "audio.wav"
    processed_path = tmp_path / "processed.wav"
    audio_path.write_bytes(b"audio")
    processed_path.write_bytes(b"processed")

    recorder.audio_file = str(audio_path)
    processor.next_result = str(processed_path)
    transcriber.result = "hello"
    refiner.result = "hello refined"
    inserter.window_title = "Editor"

    app._on_start_recording()
    app._on_stop_recording()

    assert recorder.start_calls == 1
    assert recorder.stop_calls == 1
    assert processor.last_input == str(audio_path)
    assert transcriber.last_path == str(processed_path)
    assert refiner.last_input == "hello"
    assert inserter.last_text == "hello refined"
    assert inserter.last_method == app.config.insertion_method
    assert feedback_spy["start"] == 1
    assert feedback_spy["stop"] == 1
    assert not audio_path.exists()
    assert not processed_path.exists()


def test_process_recorded_audio_without_text(make_app, dependency_stubs, feedback_spy, immediate_thread, tmp_path):
    app = make_app()
    app.config.enable_audio_feedback = False

    recorder = dependency_stubs.last("audio_recorder")
    processor = dependency_stubs.last("audio_processor")
    transcriber = dependency_stubs.last("transcriber")
    refiner = dependency_stubs.last("text_refiner")
    inserter = dependency_stubs.last("text_inserter")

    audio_path = tmp_path / "audio.wav"
    audio_path.write_bytes(b"audio")

    recorder.audio_file = str(audio_path)
    processor.next_result = str(audio_path)
    transcriber.result = None

    app._on_start_recording()
    app._on_stop_recording()

    assert feedback_spy["start"] == 0
    assert feedback_spy["stop"] == 0
    assert refiner.calls == 0
    assert inserter.insert_calls == 0
    assert not audio_path.exists()


def test_process_recorded_audio_handles_processor_failure(
    make_app,
    dependency_stubs,
    feedback_spy,
    immediate_thread,
    tmp_path,
):
    app = make_app()

    recorder = dependency_stubs.last("audio_recorder")
    processor = dependency_stubs.last("audio_processor")
    transcriber = dependency_stubs.last("transcriber")
    refiner = dependency_stubs.last("text_refiner")
    inserter = dependency_stubs.last("text_inserter")

    audio_path = tmp_path / "audio.wav"
    audio_path.write_bytes(b"audio")

    recorder.audio_file = str(audio_path)
    processor.next_result = None
    transcriber.result = "draft"
    refiner.result = ""  # force fallback to raw transcription
    inserter.should_succeed = False

    app._on_start_recording()
    app._on_stop_recording()

    assert processor.last_input == str(audio_path)
    assert transcriber.last_path is None
    assert refiner.last_input == "draft"
    assert inserter.insert_calls == 1
    assert inserter.last_text == "draft"
    assert feedback_spy["start"] == 1
    assert feedback_spy["stop"] == 1
    assert not audio_path.exists()


def test_update_configuration_reinitializes(make_app, dependency_stubs):
    app = make_app()

    initial_recorder = dependency_stubs.last("audio_recorder")
    initial_service = dependency_stubs.last("hotkey_service")

    new_config = replace(app.config, chunk_size=app.config.chunk_size + 1)

    app.update_configuration(new_config)

    assert dependency_stubs.last("audio_recorder") is not initial_recorder
    assert initial_service.stop_calls == 1
    assert app.config == new_config


def test_update_configuration_skips_reinit_when_unchanged(make_app, dependency_stubs):
    app = make_app()

    initial_recorder = dependency_stubs.last("audio_recorder")
    initial_service = dependency_stubs.last("hotkey_service")

    duplicate_config = replace(app.config)

    app.update_configuration(duplicate_config)

    assert dependency_stubs.last("audio_recorder") is initial_recorder
    assert initial_service.stop_calls == 0


def test_toggle_text_refinement_recreates_refiner(make_app, dependency_stubs):
    config = push_to_talk.PushToTalkConfig(
        openai_api_key="key",
        custom_glossary=["api"],
    )
    app = make_app(config)

    original_refiner = dependency_stubs.last("text_refiner")

    assert app.toggle_text_refinement() is False
    assert app.text_refiner is None

    assert app.toggle_text_refinement() is True
    assert dependency_stubs.last("text_refiner") is not original_refiner
    assert app.text_refiner.glossary == config.custom_glossary


def test_toggle_audio_feedback(make_app):
    app = make_app()

    assert app.toggle_audio_feedback() is False
    assert app.toggle_audio_feedback() is True


def test_on_start_recording_failure(make_app, dependency_stubs, feedback_spy):
    app = make_app()
    recorder = dependency_stubs.last("audio_recorder")
    recorder.should_start = False

    app._on_start_recording()

    assert recorder.start_calls == 1
    assert feedback_spy["start"] == 1


def test_get_status_reports_state(make_app, dependency_stubs):
    app = make_app()
    hotkey_service = dependency_stubs.last("hotkey_service")

    status = app.get_status()
    assert status["recording_mode"] == "idle"

    app.is_running = True
    hotkey_service.recording_state = "push_to_talk"
    assert app.get_status()["recording_mode"] == "push-to-talk"

    hotkey_service.recording_state = "toggle"
    assert app.get_status()["recording_mode"] == "toggle"

    hotkey_service.recording_state = "other"
    assert app.get_status()["recording_mode"] == "idle"


def test_change_hotkey_replaces_service(make_app, dependency_stubs):
    app = make_app()

    original_service = dependency_stubs.last("hotkey_service")

    assert app.change_hotkey("ctrl+alt+n") is True

    new_service = dependency_stubs.last("hotkey_service")
    assert new_service is not original_service
    assert original_service.stop_calls == 1
    assert new_service.hotkey == "ctrl+alt+n"
    assert new_service.callbacks == (app._on_start_recording, app._on_stop_recording)


def test_change_toggle_hotkey_replaces_service(make_app, dependency_stubs):
    app = make_app()

    original_service = dependency_stubs.last("hotkey_service")

    assert app.change_toggle_hotkey("ctrl+alt+y") is True

    new_service = dependency_stubs.last("hotkey_service")
    assert new_service is not original_service
    assert original_service.stop_calls == 1
    assert new_service.toggle_hotkey == "ctrl+alt+y"
    assert new_service.callbacks == (app._on_start_recording, app._on_stop_recording)
