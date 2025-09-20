import pytest
from unittest.mock import Mock, patch

from src.local_whisper_transcriber import LocalWhisperTranscriber


class TestLocalWhisperTranscriber:
    """Test suite for LocalWhisperTranscriber."""

    @patch("src.local_whisper_transcriber.PYWHISPERCPP_AVAILABLE", False)
    def test_init_without_pywhispercpp(self):
        """Test initialization when pywhispercpp is not available."""
        with pytest.raises(RuntimeError, match="pywhispercpp is not installed"):
            LocalWhisperTranscriber()

    @patch("src.local_whisper_transcriber.PYWHISPERCPP_AVAILABLE", True)
    def test_init_success(self):
        """Test successful initialization."""
        with (
            patch.object(
                LocalWhisperTranscriber, "_determine_device", return_value="cpu"
            ),
            patch.object(
                LocalWhisperTranscriber, "_determine_compute_type", return_value="int8"
            ),
        ):
            transcriber = LocalWhisperTranscriber("base", "cpu", "int8")

            assert transcriber.model_name == "base"
            assert transcriber.device == "cpu"
            assert transcriber.compute_type == "int8"
            assert (
                transcriber.model is None
            )  # Lazy loading means model is None initially

    @patch("src.local_whisper_transcriber.PYWHISPERCPP_AVAILABLE", True)
    def test_init_model_loading_deferred(self):
        """Test that model loading is deferred until first use."""
        with (
            patch.object(
                LocalWhisperTranscriber, "_determine_device", return_value="cpu"
            ),
            patch.object(
                LocalWhisperTranscriber, "_determine_compute_type", return_value="int8"
            ),
        ):
            # With lazy loading, initialization errors don't occur until first transcription
            transcriber = LocalWhisperTranscriber("base", "cpu", "int8")
            assert transcriber.model is None

    @patch("subprocess.check_output")
    def test_determine_device_auto_with_cuda(self, mock_subprocess):
        """Test device determination with CUDA available."""
        # Mock nvidia-smi -L command to show 1 GPU
        mock_subprocess.return_value = "GPU 0: Tesla V100\n"

        transcriber = LocalWhisperTranscriber.__new__(LocalWhisperTranscriber)
        result = transcriber._determine_device("auto")

        assert result == "cuda"

    @patch("subprocess.check_output")
    def test_determine_device_auto_without_cuda(self, mock_subprocess):
        """Test device determination when nvidia-smi fails."""
        import subprocess

        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "nvidia-smi")

        transcriber = LocalWhisperTranscriber.__new__(LocalWhisperTranscriber)
        result = transcriber._determine_device("auto")

        assert result == "cpu"

    @patch("subprocess.check_output")
    def test_determine_device_auto_no_nvidia_smi(self, mock_subprocess):
        """Test device determination when nvidia-smi is not available."""
        mock_subprocess.side_effect = FileNotFoundError("nvidia-smi not found")

        transcriber = LocalWhisperTranscriber.__new__(LocalWhisperTranscriber)
        result = transcriber._determine_device("auto")

        assert result == "cpu"

    def test_determine_device_explicit(self):
        """Test explicit device specification."""
        transcriber = LocalWhisperTranscriber.__new__(LocalWhisperTranscriber)
        result = transcriber._determine_device("cuda")

        assert result == "cuda"

    def test_determine_compute_type_auto_cuda(self):
        """Test compute type determination for CUDA."""
        transcriber = LocalWhisperTranscriber.__new__(LocalWhisperTranscriber)
        transcriber.device = "cuda"
        result = transcriber._determine_compute_type("auto")

        assert result == "float16"

    def test_determine_compute_type_auto_cpu(self):
        """Test compute type determination for CPU."""
        transcriber = LocalWhisperTranscriber.__new__(LocalWhisperTranscriber)
        transcriber.device = "cpu"
        result = transcriber._determine_compute_type("auto")

        assert result == "int8"

    def test_determine_compute_type_explicit(self):
        """Test explicit compute type specification."""
        transcriber = LocalWhisperTranscriber.__new__(LocalWhisperTranscriber)
        result = transcriber._determine_compute_type("float32")

        assert result == "float32"

    @patch("src.local_whisper_transcriber.PYWHISPERCPP_AVAILABLE", True)
    def test_transcribe_audio_no_model(self):
        """Test transcription when model initialization fails."""
        transcriber = LocalWhisperTranscriber.__new__(LocalWhisperTranscriber)
        transcriber.model = None

        # Mock the _initialize_model method to raise an exception
        with patch.object(
            transcriber,
            "_initialize_model",
            side_effect=Exception("Model loading failed"),
        ):
            result = transcriber.transcribe_audio("test.wav")

        assert result is None

    @patch("src.local_whisper_transcriber.PYWHISPERCPP_AVAILABLE", True)
    def test_transcribe_audio_file_not_found(self):
        """Test transcription with non-existent file."""
        transcriber = LocalWhisperTranscriber.__new__(LocalWhisperTranscriber)
        transcriber.model = Mock()

        result = transcriber.transcribe_audio("nonexistent.wav")

        assert result is None

    @patch("src.local_whisper_transcriber.PYWHISPERCPP_AVAILABLE", True)
    @patch("src.local_whisper_transcriber.wave.open")
    def test_transcribe_audio_too_short(self, mock_wave_open):
        """Test transcription with audio too short."""
        # Mock wave file that's too short
        mock_wave_file = Mock()
        mock_wave_file.getnframes.return_value = 1000
        mock_wave_file.getframerate.return_value = 16000  # 1000/16000 = 0.0625s < 0.5s
        mock_wave_open.return_value.__enter__.return_value = mock_wave_file

        transcriber = LocalWhisperTranscriber.__new__(LocalWhisperTranscriber)
        transcriber.model = Mock()

        with patch("os.path.exists", return_value=True):
            result = transcriber.transcribe_audio("short.wav")

        assert result is None

    @patch("src.local_whisper_transcriber.PYWHISPERCPP_AVAILABLE", True)
    @patch("src.local_whisper_transcriber.wave.open")
    @patch("os.path.exists")
    def test_transcribe_audio_success(self, mock_exists, mock_wave_open):
        """Test successful transcription."""
        # Mock wave file analysis
        mock_wave_file = Mock()
        mock_wave_file.getnframes.return_value = 16000  # 1 second at 16kHz
        mock_wave_file.getframerate.return_value = 16000
        mock_wave_open.return_value.__enter__.return_value = mock_wave_file
        mock_exists.return_value = True

        # Mock model and segments for pywhispercpp API
        mock_segment1 = Mock()
        mock_segment1.text = "Hello "
        mock_segment2 = Mock()
        mock_segment2.text = "world!"

        mock_model = Mock()
        # pywhispercpp returns an iterable of segments directly
        mock_model.transcribe.return_value = [mock_segment1, mock_segment2]

        transcriber = LocalWhisperTranscriber.__new__(LocalWhisperTranscriber)
        transcriber.model = mock_model

        result = transcriber.transcribe_audio("test.wav", language="en")

        assert result == "Hello world!"
        mock_model.transcribe.assert_called_once_with("test.wav", language="en")

    @patch("src.local_whisper_transcriber.PYWHISPERCPP_AVAILABLE", True)
    @patch("src.local_whisper_transcriber.wave.open")
    @patch("os.path.exists")
    def test_transcribe_audio_empty_result(self, mock_exists, mock_wave_open):
        """Test transcription with empty result."""
        # Mock wave file analysis
        mock_wave_file = Mock()
        mock_wave_file.getnframes.return_value = 16000
        mock_wave_file.getframerate.return_value = 16000
        mock_wave_open.return_value.__enter__.return_value = mock_wave_file
        mock_exists.return_value = True

        # Mock model with empty segments
        mock_info = Mock()
        mock_model = Mock()
        mock_model.transcribe.return_value = ([], mock_info)

        transcriber = LocalWhisperTranscriber.__new__(LocalWhisperTranscriber)
        transcriber.model = mock_model

        result = transcriber.transcribe_audio("test.wav")

        assert result is None

    @patch("src.local_whisper_transcriber.PYWHISPERCPP_AVAILABLE", True)
    @patch("src.local_whisper_transcriber.wave.open")
    @patch("os.path.exists")
    def test_transcribe_audio_exception(self, mock_exists, mock_wave_open):
        """Test transcription with exception during processing."""
        # Mock wave file analysis
        mock_wave_file = Mock()
        mock_wave_file.getnframes.return_value = 16000
        mock_wave_file.getframerate.return_value = 16000
        mock_wave_open.return_value.__enter__.return_value = mock_wave_file
        mock_exists.return_value = True

        # Mock model that raises exception
        mock_model = Mock()
        mock_model.transcribe.side_effect = Exception("Transcription failed")

        transcriber = LocalWhisperTranscriber.__new__(LocalWhisperTranscriber)
        transcriber.model = mock_model

        result = transcriber.transcribe_audio("test.wav")

        assert result is None

    @patch("src.local_whisper_transcriber.PYWHISPERCPP_AVAILABLE", True)
    def test_get_model_info(self):
        """Test getting model information."""
        transcriber = LocalWhisperTranscriber.__new__(LocalWhisperTranscriber)
        transcriber.model_name = "base"
        transcriber.device = "cpu"
        transcriber.compute_type = "int8"
        transcriber.model = Mock()

        info = transcriber.get_model_info()

        assert info["model_name"] == "base"
        assert info["device"] == "cpu"
        assert info["compute_type"] == "int8"
        assert info["is_loaded"] is True

    @patch("src.local_whisper_transcriber.PYWHISPERCPP_AVAILABLE", True)
    def test_get_model_info_no_model(self):
        """Test getting model information when model is not loaded."""
        transcriber = LocalWhisperTranscriber.__new__(LocalWhisperTranscriber)
        transcriber.model_name = "base"
        transcriber.device = "cpu"
        transcriber.compute_type = "int8"
        transcriber.model = None

        info = transcriber.get_model_info()

        assert info["is_loaded"] is False

    @patch("src.local_whisper_transcriber.PYWHISPERCPP_AVAILABLE", True)
    def test_is_available_true(self):
        """Test availability check when pywhispercpp is available."""
        assert LocalWhisperTranscriber.is_available() is True

    @patch("src.local_whisper_transcriber.PYWHISPERCPP_AVAILABLE", False)
    def test_is_available_false(self):
        """Test availability check when pywhispercpp is not available."""
        assert LocalWhisperTranscriber.is_available() is False

    @patch("subprocess.check_output")
    def test_get_gpu_info_with_cuda(self, mock_subprocess):
        """Test GPU info retrieval with CUDA available."""

        # Mock nvidia-smi commands
        def mock_command(cmd, **kwargs):
            if "--query-gpu=count" in cmd:
                return "2\n"
            elif "-L" in cmd:
                return "GPU 0: GeForce RTX 3080\nGPU 1: GeForce RTX 3090\n"
            elif "--query-gpu=name" in cmd:
                return "GeForce RTX 3080\nGeForce RTX 3090\n"
            elif "--query-gpu=driver_version" in cmd:
                return "470.82.01\n"
            return ""

        mock_subprocess.side_effect = mock_command
        gpu_info = LocalWhisperTranscriber.get_gpu_info()

        assert gpu_info["available"] is True
        assert gpu_info["device_count"] == 2
        assert gpu_info["device_names"] == ["GeForce RTX 3080", "GeForce RTX 3090"]
        assert gpu_info["cuda_version"] == "470.82.01"

    @patch("subprocess.check_output")
    def test_get_gpu_info_without_cuda(self, mock_subprocess):
        """Test GPU info retrieval when nvidia-smi fails."""
        import subprocess

        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "nvidia-smi")

        gpu_info = LocalWhisperTranscriber.get_gpu_info()

        assert gpu_info["available"] is False
        assert gpu_info["device_count"] == 0
        assert gpu_info["device_names"] == []
        assert gpu_info["cuda_version"] is None

    @patch("subprocess.check_output")
    def test_get_gpu_info_no_nvidia_smi(self, mock_subprocess):
        """Test GPU info retrieval when nvidia-smi is not available."""
        mock_subprocess.side_effect = FileNotFoundError("nvidia-smi not found")

        gpu_info = LocalWhisperTranscriber.get_gpu_info()

        assert gpu_info["available"] is False
        assert gpu_info["device_count"] == 0
        assert gpu_info["device_names"] == []
        assert gpu_info["cuda_version"] is None
