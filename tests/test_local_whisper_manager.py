from unittest.mock import Mock, patch, MagicMock
import threading

from src.local_whisper_manager import LocalWhisperManager


class TestLocalWhisperManager:
    """Test suite for LocalWhisperManager."""

    def test_model_info_structure(self):
        """Test that MODEL_INFO has correct structure."""
        assert isinstance(LocalWhisperManager.MODEL_INFO, dict)
        assert len(LocalWhisperManager.MODEL_INFO) > 0

        for model_name, info in LocalWhisperManager.MODEL_INFO.items():
            assert isinstance(model_name, str)
            assert isinstance(info, dict)
            assert "size_mb" in info
            assert "description" in info
            assert "parameters" in info
            assert "multilingual" in info
            assert isinstance(info["size_mb"], int)
            assert isinstance(info["description"], str)
            assert isinstance(info["parameters"], str)
            assert isinstance(info["multilingual"], bool)

    @patch("src.local_whisper_manager.PYWHISPERCPP_AVAILABLE", True)
    def test_is_model_downloaded_true(self):
        """Test model download detection when model is available in cache."""
        with patch("pathlib.Path") as mock_path:
            # Mock a model file that exists
            mock_model_file = MagicMock()
            mock_model_file.exists.return_value = True
            mock_model_file.is_file.return_value = True

            # Mock home() and cwd() to return paths that lead to the model file
            mock_home_path = MagicMock()
            mock_cwd_path = MagicMock()

            # Set up path construction: Path.home() / ".cache" / "whisper" / "base.bin"
            mock_cache_path = MagicMock()
            mock_whisper_path = MagicMock()
            mock_home_path.__truediv__.return_value = mock_cache_path
            mock_cache_path.__truediv__.return_value = mock_whisper_path
            mock_whisper_path.__truediv__.return_value = mock_model_file

            mock_path.home.return_value = mock_home_path
            mock_path.cwd.return_value = mock_cwd_path

            result = LocalWhisperManager.is_model_downloaded("base")
            assert result is True

    @patch("src.local_whisper_manager.PYWHISPERCPP_AVAILABLE", True)
    @patch("src.local_whisper_manager.LocalWhisperManager.get_cache_directory")
    def test_is_model_downloaded_false(self, mock_get_cache_directory):
        """Test model download detection when model is not in cache."""
        with patch("pathlib.Path") as mock_path:
            # Mock a model file that doesn't exist
            mock_model_file = MagicMock()
            mock_model_file.exists.return_value = False
            mock_model_file.is_file.return_value = False

            # Mock cache directory
            mock_cache_dir = MagicMock()
            mock_cache_dir.__truediv__.return_value = mock_model_file
            mock_get_cache_directory.return_value = mock_cache_dir

            # Mock cwd() to return paths that lead to non-existent model files
            mock_cwd_path = MagicMock()
            mock_models_path = MagicMock()
            mock_cwd_path.__truediv__.return_value = mock_models_path
            mock_models_path.__truediv__.return_value = mock_model_file

            mock_path.cwd.return_value = mock_cwd_path

            result = LocalWhisperManager.is_model_downloaded("base")
            assert result is False

    @patch("src.local_whisper_manager.PYWHISPERCPP_AVAILABLE", False)
    def test_is_model_downloaded_no_pywhispercpp(self):
        """Test model download detection when pywhispercpp is not available."""
        result = LocalWhisperManager.is_model_downloaded("base")
        assert result is False

    @patch("src.local_whisper_manager.PYWHISPERCPP_AVAILABLE", True)
    @patch("src.local_whisper_manager.WhisperModel")
    def test_download_model_success(self, mock_whisper_model):
        """Test successful model download."""
        mock_instance = Mock()
        mock_whisper_model.return_value = mock_instance

        progress_callback = Mock()
        result = LocalWhisperManager.download_model("base", progress_callback)

        assert result is True
        mock_whisper_model.assert_called_once_with(
            model="base", n_threads=4, print_realtime=False, print_progress=True
        )
        progress_callback.assert_any_call("Downloading base model...")
        progress_callback.assert_any_call("Model base downloaded successfully!")

    @patch("src.local_whisper_manager.PYWHISPERCPP_AVAILABLE", True)
    @patch("src.local_whisper_manager.WhisperModel")
    def test_download_model_failure(self, mock_whisper_model):
        """Test model download failure."""
        mock_whisper_model.side_effect = Exception("Download failed")

        progress_callback = Mock()
        result = LocalWhisperManager.download_model("base", progress_callback)

        assert result is False
        progress_callback.assert_any_call("Downloading base model...")
        progress_callback.assert_any_call(
            "ERROR: Failed to download base: Download failed"
        )

    @patch("src.local_whisper_manager.PYWHISPERCPP_AVAILABLE", False)
    def test_download_model_no_pywhispercpp(self):
        """Test model download when pywhispercpp is not available."""
        progress_callback = Mock()
        result = LocalWhisperManager.download_model("base", progress_callback)

        assert result is False
        progress_callback.assert_called_once_with("ERROR: pywhispercpp not available")

    @patch("src.local_whisper_manager.LocalWhisperManager.download_model")
    def test_download_model_async(self, mock_download_model):
        """Test asynchronous model download."""
        mock_download_model.return_value = True

        progress_callback = Mock()
        completion_callback = Mock()

        thread = LocalWhisperManager.download_model_async(
            "base", progress_callback, completion_callback
        )

        assert isinstance(thread, threading.Thread)
        assert thread.daemon is True

        # Wait for thread to complete
        thread.join(timeout=1.0)

        mock_download_model.assert_called_once_with("base", progress_callback)
        completion_callback.assert_called_once_with(
            True, "Download completed successfully"
        )

    @patch("src.local_whisper_manager.LocalWhisperManager.download_model")
    def test_download_model_async_failure(self, mock_download_model):
        """Test asynchronous model download failure."""
        mock_download_model.return_value = False

        progress_callback = Mock()
        completion_callback = Mock()

        thread = LocalWhisperManager.download_model_async(
            "base", progress_callback, completion_callback
        )

        # Wait for thread to complete
        thread.join(timeout=1.0)

        completion_callback.assert_called_once_with(False, "Download failed")

    @patch("src.local_whisper_manager.LocalWhisperManager.is_model_downloaded")
    def test_get_model_info(self, mock_is_downloaded):
        """Test getting model information."""
        mock_is_downloaded.return_value = True

        info = LocalWhisperManager.get_model_info("base")

        assert isinstance(info, dict)
        assert info["name"] == "base"
        assert info["downloaded"] is True
        assert "size_mb" in info
        assert "description" in info
        assert "parameters" in info
        assert "multilingual" in info

    @patch("src.local_whisper_manager.LocalWhisperManager.is_model_downloaded")
    def test_get_model_info_unknown_model(self, mock_is_downloaded):
        """Test getting information for unknown model."""
        mock_is_downloaded.return_value = False

        info = LocalWhisperManager.get_model_info("unknown-model")

        assert info["name"] == "unknown-model"
        assert info["downloaded"] is False
        assert info["size_mb"] == 0
        assert info["description"] == "Unknown model"

    @patch("src.local_whisper_manager.LocalWhisperManager.get_model_info")
    def test_get_all_models_info(self, mock_get_model_info):
        """Test getting all models information."""
        mock_get_model_info.return_value = {"name": "test", "downloaded": True}

        all_info = LocalWhisperManager.get_all_models_info()

        assert isinstance(all_info, dict)
        assert len(all_info) == len(LocalWhisperManager.MODEL_INFO)

        # Check that get_model_info was called for each model
        for model_name in LocalWhisperManager.MODEL_INFO:
            mock_get_model_info.assert_any_call(model_name)

    @patch("subprocess.check_output")
    def test_get_gpu_info_subprocess_error(self, mock_subprocess):
        """Test GPU info when nvidia-smi returns an error."""
        # Mock nvidia-smi command to raise CalledProcessError
        import subprocess

        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "nvidia-smi")

        gpu_info = LocalWhisperManager.get_gpu_info(force_refresh=True)

        assert gpu_info["available"] is False
        assert gpu_info["device_count"] == 0
        assert gpu_info["device_names"] == []
        assert gpu_info["cuda_version"] is None
        assert gpu_info["recommended_compute_type"] == "int8"

    @patch("subprocess.check_output")
    def test_get_gpu_info_with_cuda(self, mock_subprocess):
        """Test GPU info with CUDA available."""

        # Mock nvidia-smi commands
        def mock_command(cmd, **kwargs):
            if "--query-gpu=count" in cmd:
                return "2\n"
            elif "-L" in cmd:
                return "GPU 0: Tesla V100\nGPU 1: Tesla V100\n"
            elif "--query-gpu=name" in cmd:
                return "Tesla V100\nTesla V100\n"
            elif "--query-gpu=driver_version" in cmd:
                return "470.82.01\n"
            return ""

        mock_subprocess.side_effect = mock_command
        # Force refresh to bypass cache and test actual GPU detection
        gpu_info = LocalWhisperManager.get_gpu_info(force_refresh=True)

        assert gpu_info["available"] is True
        assert gpu_info["device_count"] == 2
        assert gpu_info["device_names"] == ["Tesla V100", "Tesla V100"]
        assert gpu_info["cuda_version"] == "470.82.01"
        assert gpu_info["recommended_compute_type"] == "float16"

    @patch("subprocess.check_output")
    def test_get_gpu_info_no_cuda(self, mock_subprocess):
        """Test GPU info when nvidia-smi is not available or fails."""
        # Mock nvidia-smi command to raise FileNotFoundError (nvidia-smi not found)
        mock_subprocess.side_effect = FileNotFoundError("nvidia-smi not found")

        gpu_info = LocalWhisperManager.get_gpu_info(force_refresh=True)

        assert gpu_info["available"] is False
        assert gpu_info["device_count"] == 0
        assert gpu_info["device_names"] == []
        assert gpu_info["cuda_version"] is None
        assert gpu_info["recommended_compute_type"] == "int8"

    @patch("src.local_whisper_manager.LocalWhisperManager.get_gpu_info")
    @patch("src.local_whisper_manager.LocalWhisperManager.get_all_models_info")
    @patch("src.local_whisper_manager.PYWHISPERCPP_AVAILABLE", True)
    def test_get_status_summary(self, mock_get_all_models, mock_get_gpu_info):
        """Test getting system status summary."""
        mock_gpu_info = {
            "available": True,
            "device_count": 1,
            "device_names": ["Test GPU"],
            "recommended_compute_type": "float16",
        }
        mock_get_gpu_info.return_value = mock_gpu_info

        mock_models_info = {
            "base": {"downloaded": True},
            "small": {"downloaded": False},
            "medium": {"downloaded": True},
        }
        mock_get_all_models.return_value = mock_models_info

        status = LocalWhisperManager.get_status_summary()

        assert status["pywhispercpp_available"] is True
        assert status["gpu_available"] is True
        assert status["gpu_count"] == 1
        assert status["gpu_names"] == ["Test GPU"]
        assert status["downloaded_models"] == ["base", "medium"]
        assert status["total_models"] == 3
        assert status["recommended_device"] == "cuda"

    @patch("src.local_whisper_manager.PYWHISPERCPP_AVAILABLE", True)
    def test_validate_model_name_valid(self):
        """Test model name validation for valid model."""
        is_valid, error = LocalWhisperManager.validate_model_name("base")

        assert is_valid is True
        assert error == ""

    @patch("src.local_whisper_manager.PYWHISPERCPP_AVAILABLE", False)
    def test_validate_model_name_no_pywhispercpp(self):
        """Test model name validation when pywhispercpp not available."""
        is_valid, error = LocalWhisperManager.validate_model_name("base")

        assert is_valid is False
        assert "pywhispercpp is not available" in error

    @patch("src.local_whisper_manager.PYWHISPERCPP_AVAILABLE", True)
    def test_validate_model_name_invalid(self):
        """Test model name validation for invalid model."""
        is_valid, error = LocalWhisperManager.validate_model_name("invalid-model")

        assert is_valid is False
        assert "Unknown model" in error
        assert "invalid-model" in error

    @patch("src.local_whisper_manager.LocalWhisperManager.get_gpu_info")
    def test_get_recommended_model_with_gpu(self, mock_get_gpu_info):
        """Test recommended model selection with GPU available."""
        mock_get_gpu_info.return_value = {"available": True}

        recommended = LocalWhisperManager.get_recommended_model()

        assert recommended == "large-v3"

    @patch("src.local_whisper_manager.LocalWhisperManager.get_gpu_info")
    def test_get_recommended_model_without_gpu(self, mock_get_gpu_info):
        """Test recommended model selection without GPU."""
        mock_get_gpu_info.return_value = {"available": False}

        recommended = LocalWhisperManager.get_recommended_model()

        assert recommended == "base"


class TestLocalWhisperManagerErrorHandling:
    """Test simple error handling and edge cases in LocalWhisperManager."""

    def test_create_instance_without_pywhispercpp(self):
        """Test that LocalWhisperManager can be instantiated even without pywhispercpp."""
        # This tests the import error handling at module level
        manager = LocalWhisperManager()
        assert manager is not None

    def test_get_model_info_for_unknown_model(self):
        """Test getting model info for unknown model."""
        info = LocalWhisperManager.get_model_info("unknown-model")
        # Unknown models get a default info structure
        assert isinstance(info, dict)
        assert info["description"] == "Unknown model"
