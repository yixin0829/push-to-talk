import os
import time
import wave
from typing import Optional
from loguru import logger

try:
    from pywhispercpp.model import Model as WhisperModel

    PYWHISPERCPP_AVAILABLE = True
except ImportError:
    logger.warning(
        "pywhispercpp not installed. Local whisper transcription will not be available."
    )
    PYWHISPERCPP_AVAILABLE = False


class LocalWhisperTranscriber:
    """Local Whisper transcriber using whisper.cpp (via pywhispercpp library)."""

    # Class-level cache for GPU information (static during session)
    _gpu_info_cache = None

    def __init__(
        self, model_name: str = "base", device: str = "auto", compute_type: str = "auto"
    ):
        """
        Initialize the local whisper transcriber.

        Args:
            model_name: Name of the Whisper model (base, small, medium, large-v3, etc.)
            device: Device to run on ("auto", "cpu", "cuda")
            compute_type: Compute type ("auto", "float16", "int8", "float32")
        """
        if not PYWHISPERCPP_AVAILABLE:
            raise RuntimeError(
                "pywhispercpp is not installed. Please install it with: pip install pywhispercpp"
            )

        self.model_name = model_name
        self.device = self._determine_device(device)
        self.compute_type = self._determine_compute_type(compute_type)
        self.model = None

        logger.info(
            f"Initializing LocalWhisperTranscriber with model={model_name}, device={self.device}, compute_type={self.compute_type}"
        )

        # Don't initialize the model immediately - use lazy loading
        # The model will be loaded when first needed for transcription

    def _determine_device(self, device: str) -> str:
        """Determine the best device to use."""
        if device == "auto":
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
                count_output = subprocess.check_output(
                    ["nvidia-smi", "-L"],
                    **subprocess_kwargs,
                )
                gpu_count = len(
                    [
                        line
                        for line in count_output.strip().split("\n")
                        if line.startswith("GPU")
                    ]
                )
                if gpu_count > 0:
                    logger.info(f"CUDA available with {gpu_count} GPU(s)")
                    return "cuda"
                else:
                    logger.info("No GPUs detected, using CPU")
                    return "cpu"
            except (subprocess.CalledProcessError, FileNotFoundError, OSError):
                logger.info(
                    "NVIDIA GPU not detected or nvidia-smi not available, using CPU"
                )
                return "cpu"
        return device

    def _determine_compute_type(self, compute_type: str) -> str:
        """Determine the best compute type to use."""
        if compute_type == "auto":
            if self.device == "cuda":
                # Use float16 for GPU for best performance
                return "float16"
            else:
                # Use int8 for CPU for better performance with minimal quality loss
                return "int8"
        return compute_type

    def _initialize_model(self):
        """Initialize the whisper.cpp model via pywhispercpp."""
        try:
            logger.info(
                f"Loading Whisper model '{self.model_name}' on {self.device} with {self.compute_type}"
            )
            # pywhispercpp API: Model(model, n_threads=4, print_realtime=False, print_progress=False)
            # The model will be downloaded automatically if needed
            self.model = WhisperModel(
                model=self.model_name,
                n_threads=4,
                print_realtime=False,
                print_progress=False,
            )
            logger.info("Local Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Whisper model: {e}")
            raise RuntimeError(f"Failed to initialize Whisper model: {e}")

    def transcribe_audio(
        self, audio_file_path: str, language: Optional[str] = None
    ) -> Optional[str]:
        """
        Transcribe audio file to text using local Whisper model.

        Args:
            audio_file_path: Path to the audio file
            language: Language code (optional, auto-detect if None)

        Returns:
            Transcribed text or None if transcription failed
        """
        # Lazy load the model when first needed
        if not self.model:
            logger.info("Loading Whisper model on first use...")
            try:
                self._initialize_model()
            except Exception as e:
                logger.error(f"Failed to load Whisper model on demand: {e}")
                return None

        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found: {audio_file_path}")
            return None

        # Skip very short audio clips (< 0.5s) to avoid unnecessary processing
        try:
            with wave.open(audio_file_path, "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate() or 0
                duration_seconds = frames / float(rate) if rate else 0.0
            if duration_seconds < 0.5:
                logger.info(
                    f"Audio too short ({duration_seconds:.3f}s); skipping transcription"
                )
                return None
        except Exception as e:
            # If duration cannot be determined (e.g., not a valid WAV), handle it gracefully
            logger.debug(
                f"Could not determine audio duration for {audio_file_path}: {e}"
            )

        try:
            start_time = time.time()
            logger.debug(f"Starting local transcription for: {audio_file_path}")

            # Transcribe using pywhispercpp
            segments = self.model.transcribe(audio_file_path, language=language)

            # Collect all segments into a single string
            transcribed_text = ""
            for segment in segments:
                transcribed_text += segment.text

            transcribed_text = transcribed_text.strip()
            transcription_time = time.time() - start_time

            # Log transcription info
            logger.info(
                f"Local transcription successful: {len(transcribed_text)} characters in {transcription_time:.2f}s"
            )

            return transcribed_text if transcribed_text else None

        except Exception as e:
            logger.error(f"Local transcription failed: {e}")
            return None

    def get_model_info(self) -> dict:
        """Get information about the current model."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "compute_type": self.compute_type,
            "is_loaded": self.model is not None,
        }

    @staticmethod
    def is_available() -> bool:
        """Check if pywhispercpp is available."""
        return PYWHISPERCPP_AVAILABLE

    @staticmethod
    def get_gpu_info(force_refresh: bool = False) -> dict:
        """
        Get GPU information for display in GUI using nvidia-smi.
        Results are cached to avoid repeated subprocess calls.

        Args:
            force_refresh: If True, bypass cache and re-detect GPU info

        Returns:
            Dictionary containing GPU availability and details
        """
        # Return cached result if available and not forcing refresh
        if LocalWhisperTranscriber._gpu_info_cache is not None and not force_refresh:
            return LocalWhisperTranscriber._gpu_info_cache

        logger.debug("Detecting GPU information using nvidia-smi")
        gpu_info = {
            "available": False,
            "device_count": 0,
            "device_names": [],
            "cuda_version": None,
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
        LocalWhisperTranscriber._gpu_info_cache = gpu_info
        return gpu_info
