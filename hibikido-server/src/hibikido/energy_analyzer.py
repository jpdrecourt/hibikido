"""
Hibikidō Energy Model analyzer - starts with onset detection.

Simple onset counting as foundation for more complex energy analysis.
"""

import numpy as np
import librosa
from typing import Dict, Optional
import logging
import matplotlib.pyplot as plt

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
            
            # Compute onset strength using spectral novelty
            onset_strength = librosa.onset.onset_strength(
                y=y_segment, 
                sr=sr
            )
            
            # Multi-band onset detection using IQR
            bands = {
                'Low-mid (150-2000 Hz)': {'fmin': 150, 'fmax': 2000},
                'Mid (500-4000 Hz)': {'fmin': 500, 'fmax': 4000},
                'High-mid (2000-8000 Hz)': {'fmin': 2000, 'fmax': 8000}
            }
            
            onset_results = {}
            for band_name, freq_range in bands.items():
                # Compute onset strength for this frequency band
                band_onset_strength = librosa.onset.onset_strength(
                    y=y_segment,
                    sr=sr,
                    fmin=freq_range['fmin'],
                    fmax=freq_range['fmax']
                )
                
                # Calculate IQR-based delta for this band
                q75, q25 = np.percentile(band_onset_strength, [75, 25])
                band_delta = float((q75 - q25) * 0.5)
                
                # Detect onsets in this band
                band_onset_frames = librosa.onset.onset_detect(
                    onset_envelope=band_onset_strength,
                    sr=sr,
                    units='frames',
                    delta=band_delta
                )
                
                # Convert frames to times
                band_onset_times = librosa.frames_to_time(band_onset_frames, sr=sr)
                
                onset_results[band_name] = {
                    'frames': band_onset_frames,
                    'times': band_onset_times,
                    'strength': band_onset_strength,
                    'delta': band_delta,
                    'count': len(band_onset_frames)
                }
                
                logger.debug(f"{band_name}: {len(band_onset_frames)} onsets, delta={band_delta:.3f}")
            
            # Use the mid-band results as the main output for compatibility
            adaptive_delta = onset_results['Mid (500-4000 Hz)']['delta']
            onset_frames = onset_results['Mid (500-4000 Hz)']['frames']
            
            # TEMPORARY DEBUG VISUALIZATION - Multi-band comparison
            try:
                fig, axes = plt.subplots(nrows=4, sharex=True, figsize=(14, 12))
                
                # Spectrogram on top
                D = np.abs(librosa.stft(y_segment))
                librosa.display.specshow(librosa.amplitude_to_db(D, ref=np.max),
                                         x_axis='time', y_axis='log', ax=axes[0], sr=sr)
                axes[0].set(title='Power spectrogram')
                axes[0].label_outer()
                
                # Plot each frequency band
                colors = ['red', 'blue', 'green']
                for i, (band_name, result) in enumerate(onset_results.items()):
                    ax = axes[i + 1]
                    times_band = librosa.times_like(result['strength'], sr=sr)
                    
                    ax.plot(times_band, result['strength'], 'gray', alpha=0.7, label='Onset strength')
                    ax.vlines(result['times'], 0, result['strength'].max(), 
                             color=colors[i], alpha=0.8, linestyle='--', 
                             label=f"Onsets ({result['count']})")
                    ax.set_title(f"{band_name}: δ={result['delta']:.3f}, {result['count']} onsets")
                    ax.legend()
                    ax.label_outer()
                
                plt.tight_layout()
                plt.show()
                
                # Log onset times for each band
                logger.info("Multi-band onset detection results:")
                for band_name, result in onset_results.items():
                    times_str = ', '.join([f"{t:.2f}s" for t in result['times']])
                    logger.info(f"  {band_name}: {result['count']} onsets at [{times_str}]")
                    
            except Exception as viz_error:
                logger.warning(f"Visualization failed: {viz_error}")
            
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