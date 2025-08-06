"""
Combined audio analyzer for Hibikidō - does both Bark and Energy analysis on loaded audio.
This is the primary interface for all audio analysis operations.
"""

import numpy as np
import librosa
from typing import Dict, List, Tuple, Optional
import logging
from .bark_analyzer import BarkAnalyzer
from .energy_analyzer import EnergyAnalyzer
from .feature_extractor import AudioFeatureExtractor

logger = logging.getLogger(__name__)


class AudioAnalyzer:
    """Combined analyzer that performs both Bark band and energy analysis on pre-loaded audio."""
    
    def __init__(self, sample_rate: int = 32000):
        """
        Initialize combined audio analyzer.
        
        Args:
            sample_rate: Target sample rate for analysis
        """
        self.sample_rate = sample_rate
        self.bark_analyzer = BarkAnalyzer(sample_rate)
        self.energy_analyzer = EnergyAnalyzer(sample_rate)
        self.feature_extractor = AudioFeatureExtractor(sample_rate)
        
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
                'onset_times_low_mid': List[float],
                'onset_times_mid': List[float],
                'onset_times_high_mid': List[float],
                'features': Dict  # Comprehensive audio features
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
            
            # Perform Bark analysis using the analyzer
            bark_bands_raw, _ = self.bark_analyzer.analyze_audio_data(y, sr, start_time, end_time)
            bark_norm = BarkAnalyzer.vector_norm(bark_bands_raw)
            
            # Perform energy analysis using the analyzer
            energy_results = self.energy_analyzer.analyze_energy_data(y, sr, start_time, end_time)
            total_onsets = len(energy_results.get('onset_times_low_mid', [])) + len(energy_results.get('onset_times_mid', [])) + len(energy_results.get('onset_times_high_mid', []))
            
            # Extract comprehensive features
            features = self.feature_extractor.extract_features_from_audio(y_segment, sr)
            
            logger.debug(f"Combined analysis: {duration:.2f}s, Bark norm: {bark_norm:.3f}, "
                        f"{total_onsets} total onsets across 3 bands")
            
            return {
                'duration': duration,
                'bark_bands_raw': bark_bands_raw,
                'bark_norm': bark_norm,
                'onset_times_low_mid': energy_results.get('onset_times_low_mid', []),
                'onset_times_mid': energy_results.get('onset_times_mid', []),
                'onset_times_high_mid': energy_results.get('onset_times_high_mid', []),
                'features': features or {}
            }
            
        except Exception as e:
            logger.error(f"Audio analysis failed: {e}")
            # Return safe defaults
            return {
                'duration': 0.0,
                'bark_bands_raw': [0.0] * 24,
                'bark_norm': 0.0,
                'onset_times_low_mid': [],
                'onset_times_mid': [],
                'onset_times_high_mid': [],
                'features': {}
            }


    def analyze_file(self, audio_path: str, start_time: float = 0.0, 
                    end_time: Optional[float] = None) -> Dict:
        """
        Load and analyze an audio file with both Bark and energy analysis.
        
        Args:
            audio_path: Path to audio file
            start_time: Start time in seconds
            end_time: End time in seconds (None = full file)
            
        Returns:
            Dictionary with complete analysis results
        """
        try:
            # Load audio file once
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Perform combined analysis on loaded data
            return self.analyze_audio_data(y, sr, start_time, end_time)
            
        except Exception as e:
            logger.error(f"Failed to load and analyze {audio_path}: {e}")
            # Return safe defaults
            return {
                'duration': 0.0,
                'bark_bands_raw': [0.0] * 24,
                'bark_norm': 0.0,
                'onset_times_low_mid': [],
                'onset_times_mid': [],
                'onset_times_high_mid': [],
                'features': {}
            }


def analyze_audio_file(audio_path: str, start_time: float = 0.0, 
                      end_time: Optional[float] = None) -> Dict:
    """
    Convenience function to load and analyze an audio file with both Bark and energy features.
    
    Args:
        audio_path: Path to audio file
        start_time: Start time in seconds
        end_time: End time in seconds (None = full file)
        
    Returns:
        Dictionary with complete analysis results
    """
    analyzer = AudioAnalyzer()
    return analyzer.analyze_file(audio_path, start_time, end_time)


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