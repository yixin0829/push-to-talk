import numpy as np
import tempfile
import logging
import os
import shutil
from datetime import datetime
from typing import Optional
from pydub import AudioSegment
from pydub.silence import split_on_silence
import soundfile as sf
from psola import vocode

logger = logging.getLogger(__name__)


class AudioProcessor:
    def __init__(
        self,
        silence_threshold: float = -16,
        min_silence_duration: float = 400,
        speed_factor: float = 1.5,
        keep_silence: float = 80,
        debug_mode: bool = False,
    ):
        """
        Initialize the audio processor for silence detection and speed adjustment.

        Args:
            silence_threshold: dBFS threshold below audio level for silence detection (negative value, e.g. -16)
            min_silence_duration: Minimum duration of silence to split on (milliseconds)
            speed_factor: Factor to speed up audio (1.5 = 1.5x faster)
            keep_silence: Amount of silence to keep at the beginning/end of chunks (milliseconds)
            debug_mode: Whether to save debug files to current directory
        """
        self.silence_threshold = silence_threshold
        self.min_silence_duration = min_silence_duration
        self.speed_factor = speed_factor
        self.keep_silence = keep_silence
        self.debug_mode = debug_mode

    def process_audio_file(self, input_path: str) -> Optional[str]:
        """
        Process audio file: detect silence, crop, and speed up using pydub and psola.

        Args:
            input_path: Path to input audio file

        Returns:
            Path to processed WAV file, or None if processing failed
        """
        try:
            # Load audio using pydub
            audio = AudioSegment.from_file(input_path)
            logger.info(f"Original audio length: {len(audio) / 1000:.2f}s")

            # Store original audio for debug
            original_audio = audio

            # Remove silence with pydub
            chunks = split_on_silence(
                audio,
                min_silence_len=int(self.min_silence_duration),
                silence_thresh=audio.dBFS + self.silence_threshold,
                keep_silence=int(self.keep_silence),
            )

            if not chunks:
                logger.warning("No speech detected, returning original audio")
                chunks = [audio]

            # Concatenate chunks
            processed_audio = AudioSegment.empty()
            for chunk in chunks:
                processed_audio += chunk

            logger.info(
                f"Audio after silence cropping: {len(processed_audio) / 1000:.2f}s"
            )

            # Convert to numpy array for psola processing
            samples = np.array(processed_audio.get_array_of_samples(), dtype=np.float32)

            # Handle stereo by converting to mono (take left channel)
            if processed_audio.channels == 2:
                samples = samples[::2]  # Take every other sample (left channel)

            # Normalize to [-1, 1] range
            if processed_audio.sample_width == 2:  # 16-bit
                samples = samples / (2**15)
            elif processed_audio.sample_width == 1:  # 8-bit
                samples = samples / (2**7)
            elif processed_audio.sample_width == 4:  # 32-bit
                samples = samples / (2**31)
            else:
                samples = samples / np.max(np.abs(samples))  # Fallback normalization

            # Speed up with pitch preservation using PSOLA
            sample_rate = processed_audio.frame_rate
            if self.speed_factor != 1.0:
                stretched_samples = vocode(
                    samples, sample_rate=sample_rate, constant_stretch=self.speed_factor
                )
            else:
                stretched_samples = samples

            logger.info(
                f"Audio after speed-up: {len(stretched_samples) / sample_rate:.2f}s"
            )

            # Save result using soundfile
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_filename = temp_file.name
            temp_file.close()

            sf.write(temp_filename, stretched_samples, sample_rate)
            logger.info(f"Processed audio saved to {temp_filename}")

            # Save debug files if debug mode is enabled
            if self.debug_mode:
                self._save_debug_files(
                    input_path,
                    temp_filename,
                    original_audio,
                    processed_audio,
                    stretched_samples,
                    sample_rate,
                )

            return temp_filename

        except Exception as e:
            logger.error(f"Failed to process audio: {e}")
            return None

    def _save_debug_files(
        self,
        original_path: str,
        processed_path: str,
        original_audio: AudioSegment,
        cropped_audio: AudioSegment,
        sped_up_samples: np.ndarray,
        sample_rate: int,
    ):
        """
        Save debug files to the current working directory using pydub-based processing.

        Args:
            original_path: Path to original audio file
            processed_path: Path to processed audio file
            original_audio: Original audio as AudioSegment
            cropped_audio: Audio after silence cropping as AudioSegment
            sped_up_samples: Audio after speed adjustment as numpy array
            sample_rate: Sample rate
        """
        try:
            # Create debug directory with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[
                :-3
            ]  # Remove last 3 digits of microseconds
            debug_dir = f"debug_audio_{timestamp}"
            os.makedirs(debug_dir, exist_ok=True)

            # Copy original file
            original_debug_path = os.path.join(debug_dir, "01_original.wav")
            shutil.copy2(original_path, original_debug_path)
            logger.info(f"Debug: Original audio saved to {original_debug_path}")

            # Save intermediate processing stages
            cropped_debug_path = os.path.join(debug_dir, "02_silence_cropped.wav")
            cropped_audio.export(cropped_debug_path, format="wav")
            logger.info(f"Debug: Silence cropped audio saved to {cropped_debug_path}")

            # Save speed-adjusted audio
            speed_debug_path = os.path.join(debug_dir, "03_speed_adjusted.wav")
            sf.write(speed_debug_path, sped_up_samples, sample_rate)
            logger.info(f"Debug: Speed adjusted audio saved to {speed_debug_path}")

            # Copy final processed file
            final_debug_path = os.path.join(debug_dir, "04_final_processed.wav")
            shutil.copy2(processed_path, final_debug_path)

            # Create processing info file
            info_path = os.path.join(debug_dir, "processing_info.txt")
            with open(info_path, "w") as f:
                f.write("Audio Processing Debug Information (pydub + psola)\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write("Settings:\n")
                f.write(f"  Silence Threshold: {self.silence_threshold} dBFS\n")
                f.write(f"  Min Silence Duration: {self.min_silence_duration}ms\n")
                f.write(f"  Keep Silence: {self.keep_silence}ms\n")
                f.write(f"  Speed Factor: {self.speed_factor}x\n")
                f.write("Results:\n")
                f.write(f"  Original Length: {len(original_audio) / 1000:.3f}s\n")
                f.write(f"  After Cropping: {len(cropped_audio) / 1000:.3f}s\n")
                f.write(
                    f"  After Speed-up: {len(sped_up_samples) / sample_rate:.3f}s\n"
                )
                f.write(
                    f"  Time Saved: {(len(original_audio) / 1000) - (len(sped_up_samples) / sample_rate):.3f}s\n"
                )
                f.write(
                    f"  Compression Ratio: {(len(sped_up_samples) / sample_rate) / (len(original_audio) / 1000):.3f}\n"
                )

            logger.info(f"Debug files saved to directory: {debug_dir}")

        except Exception as e:
            logger.error(f"Failed to save debug files: {e}")
