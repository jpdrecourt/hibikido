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
                           end_time: Optional[float] = None) -> Dict[str, any]:
        """
        Analyze onset times for 3 frequency bands and overall metrics.
        
        Args:
            y: Audio signal array
            sr: Sample rate
            start_time: Start time in seconds
            end_time: End time in seconds (None = full audio)
            
        Returns:
            Dictionary with onset times arrays for 3 bands and overall metrics
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
            
            # Define the 3 frequency bands
            bands = {
                'low_mid': {'fmin': 150, 'fmax': 2000},      # Low-mid (150-2000 Hz)
                'mid': {'fmin': 500, 'fmax': 4000},          # Mid (500-4000 Hz) 
                'high_mid': {'fmin': 2000, 'fmax': 8000}     # High-mid (2000-8000 Hz)
            }
            
            onset_times = {}
            total_onsets = 0
            
            # Analyze each frequency band
            for band_name, freq_range in bands.items():
                # Compute onset strength for this frequency band
                band_onset_strength = librosa.onset.onset_strength(
                    y=y_segment,
                    sr=sr,
                    fmin=freq_range['fmin'],
                    fmax=freq_range['fmax']
                )
                
                # Calculate IQR-based adaptive delta for this band
                q75, q25 = np.percentile(band_onset_strength, [75, 25])
                band_delta = float((q75 - q25) * 0.5)
                
                # Detect onsets in this band
                band_onset_frames = librosa.onset.onset_detect(
                    onset_envelope=band_onset_strength,
                    sr=sr,
                    units='frames',
                    delta=band_delta
                )
                
                # Convert frames to times (relative to segment start)
                band_onset_times = librosa.frames_to_time(band_onset_frames, sr=sr)
                onset_times[f'onset_times_{band_name}'] = band_onset_times.tolist()
                total_onsets += len(band_onset_frames)
                
                logger.debug(f"{band_name} band: {len(band_onset_frames)} onsets, delta={band_delta:.3f}")
            
            logger.debug(f"Energy analysis: {duration:.2f}s, {total_onsets} total onsets across 3 bands")
            
            return {
                'onset_times_low_mid': onset_times['onset_times_low_mid'],
                'onset_times_mid': onset_times['onset_times_mid'], 
                'onset_times_high_mid': onset_times['onset_times_high_mid'],
                'duration': duration
            }
            
        except Exception as e:
            logger.error(f"Energy analysis failed: {e}")
            # Return safe defaults on failure
            return {
                'onset_times_low_mid': [],
                'onset_times_mid': [],
                'onset_times_high_mid': [],
                'duration': 0.0
            }


def analyze_energy_features(y: np.ndarray, sr: int, start_time: float = 0.0, 
                           end_time: Optional[float] = None) -> Dict[str, any]:
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