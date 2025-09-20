import os
import threading
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Callable, Optional
from loguru import logger

try:
    from pywhispercpp.model import Model as WhisperModel

    PYWHISPERCPP_AVAILABLE = True
except ImportError:
    PYWHISPERCPP_AVAILABLE = False


class LocalWhisperManager:
    """Manager for local Whisper model downloads and status."""

    # Class-level cache for GPU information (static during session)
    _gpu_info_cache = None

    # Model information with sizes (approximate)
    MODEL_INFO = {
        "tiny.en": {
            "size_mb": 39,
            "description": "Smallest English-only model",
            "parameters": "39M",
            "multilingual": False,
        },
        "tiny": {
            "size_mb": 39,
            "description": "Smallest multilingual model",
            "parameters": "39M",
            "multilingual": True,
        },
        "base.en": {
            "size_mb": 142,
            "description": "Fast English-only model",
            "parameters": "74M",
            "multilingual": False,
        },
        "base": {
            "size_mb": 142,
            "description": "Fast multilingual model",
            "parameters": "74M",
            "multilingual": True,
        },
        "small.en": {
            "size_mb": 466,
            "description": "Good balance English-only model",
            "parameters": "244M",
            "multilingual": False,
        },
        "small": {
            "size_mb": 466,
            "description": "Good balance multilingual model",
            "parameters": "244M",
            "multilingual": True,
        },
        "medium.en": {
            "size_mb": 1500,
            "description": "Better accuracy English-only model",
            "parameters": "769M",
            "multilingual": False,
        },
        "medium": {
            "size_mb": 1500,
            "description": "Better accuracy multilingual model",
            "parameters": "769M",
            "multilingual": True,
        },
        "large-v1": {
            "size_mb": 2900,
            "description": "Legacy large model",
            "parameters": "1550M",
            "multilingual": True,
        },
        "large-v2": {
            "size_mb": 2900,
            "description": "Improved large model",
            "parameters": "1550M",
            "multilingual": True,
        },
        "large-v3": {
            "size_mb": 2900,
            "description": "Latest large model",
            "parameters": "1550M",
            "multilingual": True,
        },
        "large-v3-turbo": {
            "size_mb": 800,
            "description": "Faster version of large-v3",
            "parameters": "809M",
            "multilingual": True,
        },
    }

    @staticmethod
    def is_model_downloaded(model_name: str) -> bool:
        """
        Check if a model is already downloaded by examining the whisper.cpp model directory.

        Args:
            model_name: Name of the model to check

        Returns:
            True if model is downloaded, False otherwise
        """
        if not PYWHISPERCPP_AVAILABLE:
            return False

        try:
            from pathlib import Path

            # Get the platform-specific cache directory
            cache_dir = LocalWhisperManager.get_cache_directory()

            # Check common whisper.cpp model file patterns
            possible_model_paths = [
                cache_dir / f"{model_name}.bin",
                cache_dir / f"ggml-{model_name}.bin",
                cache_dir / f"{model_name}.ggml",
                # Also check working directory models/ folder as fallback
                Path.cwd() / "models" / f"{model_name}.bin",
                Path.cwd() / "models" / f"ggml-{model_name}.bin",
            ]

            for model_path in possible_model_paths:
                if model_path.exists() and model_path.is_file():
                    logger.debug(f"Model {model_name} found at {model_path}")
                    return True

            logger.debug(
                f"Model {model_name} not found in {cache_dir} or fallback locations"
            )
            return False
        except Exception as e:
            logger.debug(f"Could not check model cache for {model_name}: {e}")
            # Fallback: assume not downloaded to be safe
            return False

    @classmethod
    def _get_model_size_info(cls, model_name: str) -> str:
        """Get user-friendly size information for a model."""
        if model_name in cls.MODEL_INFO:
            size_mb = cls.MODEL_INFO[model_name]["size_mb"]
            if size_mb < 100:
                return f"~{size_mb}MB"
            elif size_mb < 1000:
                return f"~{size_mb}MB"
            else:
                size_gb = size_mb / 1000
                return f"~{size_gb:.1f}GB"
        return "size unknown"

    @classmethod
    def download_model(
        cls, model_name: str, progress_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        Download a Whisper model using pywhispercpp.

        Args:
            model_name: Name of the model to download
            progress_callback: Optional callback for progress updates

        Returns:
            True if download was successful, False otherwise
        """
        if not PYWHISPERCPP_AVAILABLE:
            if progress_callback:
                progress_callback("ERROR: pywhispercpp not available")
            return False

        try:
            download_start = time.time()
            model_size_info = cls._get_model_size_info(model_name)

            if progress_callback:
                progress_callback(
                    f"Downloading {model_name} model ({model_size_info})..."
                )

            logger.info(f"Starting download of model: {model_name} ({model_size_info})")
            logger.info(
                "This may take several minutes depending on your internet connection..."
            )

            # Create model instance - this triggers the download in pywhispercpp
            # Use correct API: Model(model, n_threads, print_realtime, print_progress)
            WhisperModel(
                model=model_name,
                n_threads=4,
                print_realtime=False,
                print_progress=True,  # Show progress during download
            )

            download_time = time.time() - download_start

            if progress_callback:
                progress_callback(
                    f"Model {model_name} downloaded successfully in {download_time:.1f}s!"
                )

            logger.info(
                f"Successfully downloaded model: {model_name} in {download_time:.2f}s"
            )
            return True

        except Exception as e:
            download_time = time.time() - download_start
            error_msg = (
                f"Failed to download {model_name} after {download_time:.1f}s: {e}"
            )
            logger.error(error_msg)

            # Provide helpful download troubleshooting
            if "network" in str(e).lower() or "connection" in str(e).lower():
                logger.error(
                    "Network error detected. Check internet connectivity and try again."
                )
            elif "space" in str(e).lower() or "disk" in str(e).lower():
                logger.error("Disk space error. Free up storage space and try again.")
            elif "permission" in str(e).lower():
                logger.error(
                    "Permission error. Try running with administrator privileges."
                )

            if progress_callback:
                progress_callback(f"ERROR: {error_msg}")
            return False

    @staticmethod
    def download_model_async(
        model_name: str,
        progress_callback: Optional[Callable[[str], None]] = None,
        completion_callback: Optional[Callable[[bool, str], None]] = None,
    ) -> threading.Thread:
        """
        Download a model asynchronously.

        Args:
            model_name: Name of the model to download
            progress_callback: Optional callback for progress updates
            completion_callback: Optional callback when download completes (success, message)

        Returns:
            Thread object for the download operation
        """

        def download_worker():
            try:
                success = LocalWhisperManager.download_model(
                    model_name, progress_callback
                )
                if completion_callback:
                    message = (
                        "Download completed successfully"
                        if success
                        else "Download failed"
                    )
                    completion_callback(success, message)
            except Exception as e:
                logger.error(f"Download worker failed: {e}")
                if completion_callback:
                    completion_callback(False, str(e))

        thread = threading.Thread(target=download_worker, daemon=True)
        thread.start()
        return thread

    @staticmethod
    def get_model_info(model_name: str) -> Dict:
        """
        Get information about a model.

        Args:
            model_name: Name of the model

        Returns:
            Dictionary with model information
        """
        base_info = LocalWhisperManager.MODEL_INFO.get(
            model_name,
            {
                "size_mb": 0,
                "description": "Unknown model",
                "parameters": "Unknown",
                "multilingual": True,
            },
        )

        info = base_info.copy()
        info["name"] = model_name
        info["downloaded"] = LocalWhisperManager.is_model_downloaded(model_name)
        info["available"] = PYWHISPERCPP_AVAILABLE

        return info

    @staticmethod
    def get_all_models_info() -> Dict[str, Dict]:
        """
        Get information about all available models.

        Returns:
            Dictionary mapping model names to their information
        """
        return {
            model_name: LocalWhisperManager.get_model_info(model_name)
            for model_name in LocalWhisperManager.MODEL_INFO.keys()
        }

    @staticmethod
    def get_gpu_info(force_refresh: bool = False) -> Dict:
        """
        Get GPU information for display using nvidia-smi.
        Results are cached to avoid repeated subprocess calls.

        Args:
            force_refresh: If True, bypass cache and re-detect GPU info

        Returns:
            Dictionary with GPU information
        """
        # Return cached result if available and not forcing refresh
        if LocalWhisperManager._gpu_info_cache is not None and not force_refresh:
            return LocalWhisperManager._gpu_info_cache

        logger.debug("Detecting GPU information using nvidia-smi")
        gpu_info = {
            "available": False,
            "device_count": 0,
            "device_names": [],
            "cuda_version": None,
            "recommended_compute_type": "int8",
        }

        try:
            import subprocess
            import sys

            # Prepare subprocess arguments to prevent cmd windows on Windows
            subprocess_kwargs = {
                "stderr": subprocess.DEVNULL,
                "universal_newlines": True,
            }
            if sys.platform == "win32":
                subprocess_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

            # Check if nvidia-smi is available and GPUs exist
            subprocess.check_output(
                ["nvidia-smi", "--query-gpu=count", "--format=csv,noheader,nounits"],
                **subprocess_kwargs,
            )
            gpu_info["available"] = True
            gpu_info["recommended_compute_type"] = "float16"

            # Get GPU count
            try:
                count_output = subprocess.check_output(
                    ["nvidia-smi", "-L"],
                    **subprocess_kwargs,
                )
                gpu_info["device_count"] = len(
                    [
                        line
                        for line in count_output.strip().split("\n")
                        if line.startswith("GPU")
                    ]
                )
            except subprocess.CalledProcessError:
                gpu_info["device_count"] = 0

            # Get GPU names
            try:
                names_output = subprocess.check_output(
                    ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader,nounits"],
                    **subprocess_kwargs,
                )
                gpu_info["device_names"] = [
                    name.strip()
                    for name in names_output.strip().split("\n")
                    if name.strip()
                ]
            except subprocess.CalledProcessError:
                gpu_info["device_names"] = []

            # Get driver version (closest to CUDA version info)
            try:
                driver_output = subprocess.check_output(
                    [
                        "nvidia-smi",
                        "--query-gpu=driver_version",
                        "--format=csv,noheader,nounits",
                    ],
                    **subprocess_kwargs,
                )
                # Use first GPU's driver version
                gpu_info["cuda_version"] = driver_output.strip().split("\n")[0].strip()
            except subprocess.CalledProcessError:
                gpu_info["cuda_version"] = None

        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            # nvidia-smi not found, not working, or no GPUs
            logger.debug("NVIDIA GPU not detected or nvidia-smi not available")

        # Cache the result for future calls
        LocalWhisperManager._gpu_info_cache = gpu_info
        return gpu_info

    @staticmethod
    def get_status_summary() -> Dict:
        """
        Get a summary of the local Whisper system status.

        Returns:
            Dictionary with system status
        """
        gpu_info = LocalWhisperManager.get_gpu_info()
        models_info = LocalWhisperManager.get_all_models_info()

        downloaded_models = [
            name for name, info in models_info.items() if info["downloaded"]
        ]

        return {
            "pywhispercpp_available": PYWHISPERCPP_AVAILABLE,
            "gpu_available": gpu_info["available"],
            "gpu_count": gpu_info["device_count"],
            "gpu_names": gpu_info["device_names"],
            "downloaded_models": downloaded_models,
            "total_models": len(models_info),
            "recommended_device": "cuda" if gpu_info["available"] else "cpu",
            "recommended_compute_type": gpu_info["recommended_compute_type"],
        }

    @staticmethod
    def validate_model_name(model_name: str) -> tuple[bool, str]:
        """
        Validate if a model name is supported.

        Args:
            model_name: Name of the model to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not PYWHISPERCPP_AVAILABLE:
            return False, "pywhispercpp is not available"

        if model_name not in LocalWhisperManager.MODEL_INFO:
            available_models = ", ".join(LocalWhisperManager.MODEL_INFO.keys())
            return (
                False,
                f"Unknown model '{model_name}'. Available models: {available_models}",
            )

        return True, ""

    @staticmethod
    def get_recommended_model() -> str:
        """
        Get the recommended model based on system capabilities.

        Returns:
            Name of the recommended model
        """
        gpu_info = LocalWhisperManager.get_gpu_info()

        if gpu_info["available"]:
            # With GPU, we can handle larger models
            return "large-v3"
        else:
            # On CPU, prefer smaller, faster models
            return "base"

    @staticmethod
    def get_cache_directory() -> Path:
        """
        Get the whisper.cpp model cache directory path.

        Returns:
            Path to the cache directory
        """
        import sys

        # pywhispercpp cache directory varies by platform
        if sys.platform == "win32":
            # Windows: %LOCALAPPDATA%\pywhispercpp\pywhispercpp\models
            cache_dir = (
                Path.home()
                / "AppData"
                / "Local"
                / "pywhispercpp"
                / "pywhispercpp"
                / "models"
            )
        else:
            # Unix-like: ~/.cache/whisper or similar
            cache_dir = Path.home() / ".cache" / "whisper"
        return cache_dir

    @staticmethod
    def open_cache_folder() -> bool:
        """
        Open the model cache folder in the system file explorer.

        Returns:
            True if successful, False otherwise
        """
        try:
            cache_dir = LocalWhisperManager.get_cache_directory()

            # Create cache directory if it doesn't exist
            cache_dir.mkdir(parents=True, exist_ok=True)

            # Open folder using platform-specific command
            if sys.platform == "win32":
                os.startfile(str(cache_dir))
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", str(cache_dir)], check=True)
            else:  # Linux and other Unix-like systems
                subprocess.run(["xdg-open", str(cache_dir)], check=True)

            logger.info(f"Opened cache folder: {cache_dir}")
            return True

        except Exception as e:
            logger.error(f"Failed to open cache folder: {e}")
            return False

    @staticmethod
    def get_cache_info() -> Dict:
        """
        Get information about the cache directory.

        Returns:
            Dictionary with cache information
        """
        try:
            cache_dir = LocalWhisperManager.get_cache_directory()

            info = {
                "path": str(cache_dir),
                "exists": cache_dir.exists(),
                "total_size_mb": 0,
                "whisper_models": [],
            }

            if cache_dir.exists():
                # Calculate total size of Whisper models
                model_files = list(cache_dir.glob("*.bin"))

                for model_file in model_files:
                    if model_file.is_file():
                        model_name = model_file.stem.replace("ggml-", "")
                        size_mb = model_file.stat().st_size / (1024 * 1024)

                        info["whisper_models"].append(
                            {"name": model_name, "size_mb": round(size_mb, 1)}
                        )
                        info["total_size_mb"] += size_mb

                info["total_size_mb"] = round(info["total_size_mb"], 1)

            return info

        except Exception as e:
            logger.error(f"Failed to get cache info: {e}")
            return {
                "path": "Unknown",
                "exists": False,
                "total_size_mb": 0,
                "whisper_models": [],
            }
