"""
Combined audio analyzer for Hibikidō - does both Bark and Energy analysis on loaded audio.
"""

import numpy as np
import librosa
from typing import Dict, List, Tuple, Optional
import logging
from .bark_analyzer import BarkAnalyzer

logger = logging.getLogger(__name__)


class AudioAnalyzer:
    """Combined analyzer that performs both Bark band and energy analysis on pre-loaded audio."""
    
    def __init__(self, sample_rate: int = 22050):
        """
        Initialize combined audio analyzer.
        
        Args:
            sample_rate: Target sample rate for analysis
        """
        self.sample_rate = sample_rate
        self.bark_analyzer = BarkAnalyzer(sample_rate)
        
    def analyze_audio_data(self, y: np.ndarray, sr: int, start_time: float = 0.0, 
                          end_time: Optional[float] = None) -> Dict:
        """
        Perform complete audio analysis on loaded audio data.
        
        Args:
            y: Audio signal array
            sr: Sample rate
            start_time: Start time in seconds
            end_time: End time in seconds (None = full audio)
            
        Returns:
            Dictionary with all analysis results:
            {
                'duration': float,
                'bark_bands_raw': List[float],
                'bark_norm': float,
                'onset_count': int,
                'onset_density': float
            }
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
            
            # Perform both analyses on the loaded audio
            bark_bands_raw = self.bark_analyzer._compute_bark_bands(y_segment, sr)
            bark_norm = BarkAnalyzer.vector_norm(bark_bands_raw)
            
            # Onset detection
            onset_frames = librosa.onset.onset_detect(
                y=y_segment,
                sr=sr,
                units='frames',
                hop_length=512,
                backtrack=True
            )
            
            onset_count = len(onset_frames)
            onset_density = onset_count / duration if duration > 0 else 0.0
            
            logger.debug(f"Combined analysis: {duration:.2f}s, Bark norm: {bark_norm:.3f}, "
                        f"{onset_count} onsets ({onset_density:.1f}/sec)")
            
            return {
                'duration': duration,
                'bark_bands_raw': bark_bands_raw,
                'bark_norm': bark_norm,
                'onset_count': onset_count,
                'onset_density': onset_density
            }
            
        except Exception as e:
            logger.error(f"Audio analysis failed: {e}")
            # Return safe defaults
            return {
                'duration': 0.0,
                'bark_bands_raw': [0.0] * 24,
                'bark_norm': 0.0,
                'onset_count': 0,
                'onset_density': 0.0
            }


def analyze_loaded_audio(y: np.ndarray, sr: int, start_time: float = 0.0, 
                        end_time: Optional[float] = None) -> Dict:
    """
    Convenience function to analyze loaded audio data with both Bark and energy features.
    
    Args:
        y: Audio signal array
        sr: Sample rate
        start_time: Start time in seconds
        end_time: End time in seconds (None = full audio)
        
    Returns:
        Dictionary with complete analysis results
    """
    analyzer = AudioAnalyzer(sr)
    return analyzer.analyze_audio_data(y, sr, start_time, end_time)