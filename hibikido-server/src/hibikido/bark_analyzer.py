"""
Bark band audio analysis for semantic audio niche detection.

Uses the Bark scale (24 critical bands) to analyze frequency content
and compute normalized energy vectors for cosine similarity comparison.
"""

import numpy as np
import librosa
import soundfile as sf
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class BarkAnalyzer:
    """Analyzes audio files to extract Bark band energy vectors."""
    
    # Bark scale critical band frequencies (Hz)
    # 24 bands covering 0 Hz to ~15.5 kHz
    BARK_FREQUENCIES = [
        0, 100, 200, 300, 400, 510, 630, 770, 920, 1080,
        1270, 1480, 1720, 2000, 2320, 2700, 3150, 3700,
        4400, 5300, 6400, 7700, 9500, 12000, 15500
    ]
    
    def __init__(self, sample_rate: int = 32000):
        """
        Initialize Bark analyzer.
        
        Args:
            sample_rate: Target sample rate for audio analysis
        """
        self.sample_rate = sample_rate
        self.n_bark_bands = len(self.BARK_FREQUENCIES) - 1  # 24 bands
        
    def analyze_file(self, audio_path: str, start_time: float = 0.0, 
                    end_time: Optional[float] = None) -> Tuple[List[float], float]:
        """
        Analyze audio file and extract Bark band energy vector.
        
        Args:
            audio_path: Path to audio file
            start_time: Start time in seconds (default: 0.0)
            end_time: End time in seconds (default: None = full file)
            
        Returns:
            Tuple of (bark_vector, duration) where:
            - bark_vector: List of 24 raw Bark band energies
            - duration: Duration of analyzed segment in seconds
            
        Raises:
            FileNotFoundError: If audio file doesn't exist
            ValueError: If audio analysis fails
        """
        try:
            # Load audio file
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Calculate total duration
            total_duration = len(y) / sr
            
            # Handle time segment extraction
            if end_time is None:
                end_time = total_duration
            
            # Convert time to sample indices
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            
            # Extract segment
            y_segment = y[start_sample:end_sample]
            segment_duration = len(y_segment) / sr
            
            if len(y_segment) == 0:
                raise ValueError(f"Invalid time segment: {start_time}s to {end_time}s")
            
            # Compute Bark band energies
            bark_vector = self._compute_bark_bands(y_segment, sr)
            
            logger.debug(f"Analyzed {audio_path}: {segment_duration:.2f}s, "
                        f"Bark vector sum: {sum(bark_vector):.3f}")
            
            return bark_vector, segment_duration
            
        except Exception as e:
            logger.error(f"Failed to analyze {audio_path}: {e}")
            raise ValueError(f"Audio analysis failed: {e}")
    
    def _compute_bark_bands(self, y: np.ndarray, sr: int) -> List[float]:
        """
        Compute raw Bark band energy vector.
        
        Args:
            y: Audio signal
            sr: Sample rate
            
        Returns:
            List of 24 raw Bark band energies (not normalized)
        """
        # Compute power spectral density using STFT
        stft = librosa.stft(y, hop_length=512, n_fft=2048)
        magnitude = np.abs(stft)
        power = magnitude ** 2
        
        # Average power across time frames
        avg_power = np.mean(power, axis=1)
        
        # Convert frequency bins to Hz
        freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
        
        # Compute energy in each Bark band
        bark_energies = []
        
        for i in range(self.n_bark_bands):
            freq_low = self.BARK_FREQUENCIES[i]
            freq_high = self.BARK_FREQUENCIES[i + 1]
            
            # Find frequency bin indices for this Bark band
            bin_low = np.searchsorted(freqs, freq_low)
            bin_high = np.searchsorted(freqs, freq_high)
            
            # Sum energy in this band
            if bin_high > bin_low:
                band_energy = np.sum(avg_power[bin_low:bin_high])
            else:
                band_energy = 0.0
                
            bark_energies.append(band_energy)
        
        # Convert to numpy array and ensure all values are finite
        bark_energies = np.array(bark_energies)
        bark_vector = [float(x) if np.isfinite(x) else 0.0 for x in bark_energies]
        
        return bark_vector
    
    @staticmethod
    def normalize_vector(vector: List[float]) -> List[float]:
        """
        Normalize vector to unit length (L2 norm).
        
        Args:
            vector: Input vector
            
        Returns:
            Normalized vector (unit length)
        """
        v = np.array(vector)
        norm = np.linalg.norm(v)
        if norm == 0:
            return [0.0] * len(vector)
        return (v / norm).tolist()
    
    @staticmethod
    def vector_norm(vector: List[float]) -> float:
        """
        Calculate L2 norm of vector.
        
        Args:
            vector: Input vector
            
        Returns:
            L2 norm value
        """
        return float(np.linalg.norm(np.array(vector)))
    
    @staticmethod
    def cosine_similarity(vector1: List[float], vector2: List[float]) -> float:
        """
        Compute cosine similarity between two Bark vectors.
        
        Args:
            vector1: First Bark band vector
            vector2: Second Bark band vector
            
        Returns:
            Cosine similarity (-1.0 to 1.0, where 1.0 = identical)
        """
        if len(vector1) != len(vector2):
            raise ValueError("Vectors must have same length")
        
        # Convert to numpy arrays
        v1 = np.array(vector1)
        v2 = np.array(vector2)
        
        # Compute dot product
        dot_product = np.dot(v1, v2)
        
        # Compute magnitudes
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        # Handle zero vectors
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Compute cosine similarity
        similarity = dot_product / (norm1 * norm2)
        
        # Ensure result is in valid range
        return float(np.clip(similarity, -1.0, 1.0))


def analyze_audio_file(audio_path: str, start_time: float = 0.0, 
                      end_time: Optional[float] = None) -> Tuple[List[float], float]:
    """
    Convenience function to analyze an audio file.
    
    Args:
        audio_path: Path to audio file
        start_time: Start time in seconds
        end_time: End time in seconds (None = full file)
        
    Returns:
        Tuple of (bark_vector, duration)
    """
    analyzer = BarkAnalyzer(sample_rate=32000)
    return analyzer.analyze_file(audio_path, start_time, end_time)