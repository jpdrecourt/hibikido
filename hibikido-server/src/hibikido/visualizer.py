#!/usr/bin/env python3
"""
Hibikidō Server - Audio Visualization
=====================================

Visualization tools for audio analysis results.
"""

import numpy as np
import librosa
import matplotlib.pyplot as plt
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class AudioVisualizer:
    """Handles visualization of audio analysis results."""
    
    def __init__(self, sample_rate: int = 44100):  # Common default, but dynamically set
        """
        Initialize audio visualizer.
        
        Args:
            sample_rate: Target sample rate for analysis
        """
        self.sample_rate = sample_rate
        
    def visualize_segment_multiband(self, audio_path: str, start_time: float = 0.0, 
                                   end_time: Optional[float] = None) -> None:
        """
        Visualize multi-band onset detection for an audio segment.
        
        Args:
            audio_path: Path to audio file
            start_time: Start time in seconds
            end_time: End time in seconds (None = full file)
        """
        try:
            # Load audio file
            y, sr = librosa.load(audio_path, sr=None)  # Preserve original sample rate
            
            # Handle time segment
            total_duration = len(y) / sr
            if end_time is None:
                end_time = total_duration
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            y_segment = y[start_sample:end_sample]
            duration = len(y_segment) / sr
            
            if len(y_segment) == 0:
                logger.error(f"Invalid time segment: {start_time}s to {end_time}s")
                return
                
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
                
                logger.info(f"{band_name}: {len(band_onset_frames)} onsets, delta={band_delta:.3f}")
            
            # Create visualization
            fig, axes = plt.subplots(nrows=4, sharex=True, figsize=(14, 12))
            
            # Spectrogram on top
            D = np.abs(librosa.stft(y_segment))
            librosa.display.specshow(librosa.amplitude_to_db(D, ref=np.max),
                                     x_axis='time', y_axis='log', ax=axes[0], sr=sr)
            axes[0].set(title=f'Power spectrogram - {audio_path} ({start_time:.1f}s - {end_time:.1f}s)')
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
                
        except Exception as e:
            logger.error(f"Visualization failed for {audio_path}: {e}")
            
    def visualize_segment_from_db(self, db_manager, segment_id: str) -> None:
        """
        Visualize a segment from the database.
        
        Args:
            db_manager: Database manager instance
            segment_id: ID of the segment to visualize
        """
        try:
            # Get segment from database (assuming there's a method for this)
            # For now, we'll need to add this method to the db_manager
            segments = db_manager.get_all_segments()
            segment = None
            
            for s in segments:
                if s.get('id') == segment_id:
                    segment = s
                    break
                    
            if not segment:
                logger.error(f"Segment {segment_id} not found in database")
                return
                
            audio_path = segment.get('source_path')
            start_time = segment.get('start_time', 0.0)
            end_time = segment.get('end_time')
            
            if not audio_path:
                logger.error(f"No source_path found for segment {segment_id}")
                return
                
            logger.info(f"Visualizing segment {segment_id}: {segment.get('description', 'No description')}")
            self.visualize_segment_multiband(audio_path, start_time, end_time)
            
        except Exception as e:
            logger.error(f"Failed to visualize segment {segment_id}: {e}")


def visualize_audio_segment(audio_path: str, start_time: float = 0.0, 
                           end_time: Optional[float] = None) -> None:
    """
    Convenience function to visualize an audio segment.
    
    Args:
        audio_path: Path to audio file
        start_time: Start time in seconds
        end_time: End time in seconds (None = full file)
    """
    visualizer = AudioVisualizer()
    visualizer.visualize_segment_multiband(audio_path, start_time, end_time)