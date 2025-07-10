"""
Hibikidō Energy Model analyzer - starts with onset detection.

Simple onset counting as foundation for more complex energy analysis.
"""

import numpy as np
import librosa
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class EnergyAnalyzer:
    """Analyzes audio files for energy model features, starting with onset detection."""
    
    def __init__(self, sample_rate: int = 32000):
        """
        Initialize energy analyzer.
        
        Args:
            sample_rate: Target sample rate for analysis
        """
        self.sample_rate = sample_rate
        
    def analyze_energy_data(self, y: np.ndarray, sr: int, start_time: float = 0.0, 
                           end_time: Optional[float] = None) -> Dict[str, float]:
        """
        Analyze onset count and density for loaded audio data.
        
        Args:
            y: Audio signal array
            sr: Sample rate
            start_time: Start time in seconds
            end_time: End time in seconds (None = full audio)
            
        Returns:
            Dictionary with onset_count, onset_density, and duration
        """
        try:
            total_duration = len(y) / sr
            
            # Handle time segment
            if end_time is None:
                end_time = total_duration
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            y_segment = y[start_sample:end_sample]
            duration = len(y_segment) / sr
            
            if len(y_segment) == 0:
                raise ValueError(f"Invalid time segment: {start_time}s to {end_time}s")
            
            # Detect onsets using librosa's robust onset detection
            onset_frames = librosa.onset.onset_detect(
                y=y_segment, 
                sr=sr, 
                units='frames',
                hop_length=512,
                backtrack=True
            )
            
            onset_count = len(onset_frames)
            onset_density = onset_count / duration if duration > 0 else 0.0
            
            logger.debug(f"Energy analysis: {duration:.2f}s, {onset_count} onsets, "
                        f"{onset_density:.1f} onsets/sec")
            
            return {
                'onset_count': onset_count,
                'onset_density': onset_density,
                'duration': duration
            }
            
        except Exception as e:
            logger.error(f"Energy analysis failed: {e}")
            # Return safe defaults on failure
            return {
                'onset_count': 0,
                'onset_density': 0.0,
                'duration': 0.0
            }


def analyze_energy_features(y: np.ndarray, sr: int, start_time: float = 0.0, 
                           end_time: Optional[float] = None) -> Dict[str, float]:
    """
    Convenience function to analyze energy features of loaded audio data.
    
    Args:
        y: Audio signal array
        sr: Sample rate
        start_time: Start time in seconds
        end_time: End time in seconds (None = full audio)
        
    Returns:
        Dictionary with energy analysis results
    """
    analyzer = EnergyAnalyzer(sr)
    return analyzer.analyze_energy_data(y, sr, start_time, end_time)