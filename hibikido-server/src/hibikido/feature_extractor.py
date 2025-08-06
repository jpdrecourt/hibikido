"""
Comprehensive audio feature extraction for Hibikidō.
Extracts detailed spectral, temporal, and perceptual features from audio.
"""

import numpy as np
import librosa
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class AudioFeatureExtractor:
    """Extracts comprehensive audio features for semantic analysis and storage."""
    
    def __init__(self, sample_rate: int = 32000):
        """
        Initialize feature extractor.
        
        Args:
            sample_rate: Target sample rate for analysis
        """
        self.sample_rate = sample_rate
        
    def extract_features(self, audio_path: str, start_time: float = 0.0, 
                        end_time: Optional[float] = None) -> Optional[Dict]:
        """
        Extract comprehensive audio features from file.
        
        Args:
            audio_path: Path to audio file
            start_time: Start time in seconds
            end_time: End time in seconds (None = full file)
            
        Returns:
            Dictionary with comprehensive features or None if analysis fails
        """
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Handle time segment
            if end_time is not None:
                start_sample = int(start_time * sr)
                end_sample = int(end_time * sr)
                y = y[start_sample:end_sample]
            
            return self.extract_features_from_audio(y, sr)
            
        except Exception as e:
            logger.error(f"Failed to extract features from {audio_path}: {e}")
            return None
    
    def extract_features_from_audio(self, y: np.ndarray, sr: int) -> Dict:
        """
        Extract comprehensive features from loaded audio data.
        
        Args:
            y: Audio signal array
            sr: Sample rate
            
        Returns:
            Dictionary with all extracted features
        """
        duration = librosa.get_duration(y=y, sr=sr)
        
        # Basic properties
        rms = librosa.feature.rms(y=y)[0]
        rms_mean = float(np.mean(rms))
        rms_std = float(np.std(rms))
        
        # Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
        zero_crossing_rate = librosa.feature.zero_crossing_rate(y)[0]
        
        # MFCCs (first 13 coefficients)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_means = [float(np.mean(mfcc)) for mfcc in mfccs]
        
        # Chroma features
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_mean = [float(np.mean(c)) for c in chroma]
        
        # Tempo and rhythm
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        
        # Onset detection
        onsets = librosa.onset.onset_detect(y=y, sr=sr, units='time')
        onset_rate = len(onsets) / duration if duration > 0 else 0
        
        # Spectral contrast
        contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
        contrast_mean = [float(np.mean(c)) for c in contrast]
        
        # Harmonic-percussive separation
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        harmonic_ratio = float(np.mean(np.abs(y_harmonic)) / (np.mean(np.abs(y)) + 1e-8))
        percussive_ratio = float(np.mean(np.abs(y_percussive)) / (np.mean(np.abs(y)) + 1e-8))
        
        # Spectral flux (temporal spectral change)
        stft = librosa.stft(y)
        spectral_flux = np.sum(np.diff(np.abs(stft), axis=1) ** 2, axis=0)
        spectral_flux_mean = float(np.mean(spectral_flux))
        spectral_flux_std = float(np.std(spectral_flux))
        
        # Envelope analysis (amplitude dynamics)
        envelope = np.abs(librosa.util.pad_center(y, len(y)))
        envelope_smooth = librosa.util.smooth(envelope, length=int(sr * 0.01))  # 10ms smoothing
        
        # Attack time (time to reach 90% of peak from 10%)
        peak_val = np.max(envelope_smooth)
        if peak_val > 0:
            attack_start = np.argmax(envelope_smooth > 0.1 * peak_val)
            attack_end = np.argmax(envelope_smooth > 0.9 * peak_val)
            attack_time = (attack_end - attack_start) / sr if attack_end > attack_start else 0
        else:
            attack_time = 0
        
        # Decay analysis (from peak to sustained level)
        peak_idx = np.argmax(envelope_smooth)
        if peak_idx < len(envelope_smooth) - 1 and peak_val > 0:
            post_peak = envelope_smooth[peak_idx:]
            decay_threshold = 0.5 * peak_val
            decay_point = np.argmax(post_peak < decay_threshold)
            decay_time = decay_point / sr if decay_point > 0 else 0
        else:
            decay_time = 0
        
        # Sustained level (average amplitude in middle 50% of sound)
        mid_start = int(len(envelope_smooth) * 0.25)
        mid_end = int(len(envelope_smooth) * 0.75)
        sustained_level = float(np.mean(envelope_smooth[mid_start:mid_end])) if mid_end > mid_start else 0
        
        # Dynamic range
        dynamic_range = float(np.max(envelope_smooth) - np.min(envelope_smooth))
        
        # Energy density clusters (frequency band analysis)
        magnitude = np.abs(stft)
        freqs = librosa.fft_frequencies(sr=sr)
        
        # Define frequency bands (Hz)
        bands = {
            'sub_bass': (20, 60),
            'bass': (60, 250),
            'low_mid': (250, 500),
            'mid': (500, 2000),
            'high_mid': (2000, 4000),
            'presence': (4000, 8000),
            'brilliance': (8000, 16000),
            'air': (16000, sr//2)
        }
        
        band_energies = {}
        for band_name, (low, high) in bands.items():
            band_mask = (freqs >= low) & (freqs <= high)
            if np.any(band_mask):
                band_energy = np.mean(magnitude[band_mask, :])
                band_energies[f'{band_name}_energy'] = float(band_energy)
            else:
                band_energies[f'{band_name}_energy'] = 0.0
        
        # Find dominant frequency region
        total_energy = sum(band_energies.values())
        if total_energy > 0:
            band_ratios = {k: v/total_energy for k, v in band_energies.items()}
            dominant_band = max(band_ratios.keys(), key=lambda k: band_ratios[k])
        else:
            dominant_band = 'mid_energy'
        
        # Perceptual qualities
        spectral_irregularity = []
        for frame in magnitude.T:
            if len(frame) > 2:
                diffs = np.abs(np.diff(frame))
                irregularity = np.sum(diffs) / (np.sum(frame) + 1e-8)
                spectral_irregularity.append(irregularity)
        
        irregularity_mean = float(np.mean(spectral_irregularity)) if spectral_irregularity else 0.0
        irregularity_std = float(np.std(spectral_irregularity)) if spectral_irregularity else 0.0
        
        # Pitch salience (how "melodic" vs "textural")
        pitch_salience = harmonic_ratio / (harmonic_ratio + percussive_ratio + 1e-8)
        
        # Spectral entropy (chaos vs order)
        spectral_entropy = []
        for frame in magnitude.T:
            if np.sum(frame) > 0:
                prob = frame / np.sum(frame)
                prob = prob[prob > 0]
                entropy = -np.sum(prob * np.log2(prob + 1e-8))
                spectral_entropy.append(entropy)
        
        entropy_mean = float(np.mean(spectral_entropy)) if spectral_entropy else 0.0
        entropy_std = float(np.std(spectral_entropy)) if spectral_entropy else 0.0
        
        # Roughness coefficient (sensory dissonance)
        roughness = irregularity_mean * (1 - pitch_salience)
        
        return {
            'duration': round(duration, 2),
            'sample_rate': int(sr),
            'rms_mean': round(rms_mean, 4),
            'rms_std': round(rms_std, 4),
            'spectral_centroid_mean': round(float(np.mean(spectral_centroids)), 1),
            'spectral_centroid_std': round(float(np.std(spectral_centroids)), 1),
            'spectral_rolloff_mean': round(float(np.mean(spectral_rolloff)), 1),
            'spectral_bandwidth_mean': round(float(np.mean(spectral_bandwidth)), 1),
            'zero_crossing_rate_mean': round(float(np.mean(zero_crossing_rate)), 4),
            'tempo': round(float(tempo), 1),
            'onset_rate': round(onset_rate, 2),
            'harmonic_ratio': round(harmonic_ratio, 3),
            'percussive_ratio': round(percussive_ratio, 3),
            'spectral_flux_mean': round(spectral_flux_mean, 2),
            'spectral_flux_std': round(spectral_flux_std, 2),
            'attack_time': round(attack_time, 3),
            'decay_time': round(decay_time, 3),
            'sustained_level': round(sustained_level, 4),
            'dynamic_range': round(dynamic_range, 4),
            'sub_bass_energy': round(band_energies['sub_bass_energy'], 4),
            'bass_energy': round(band_energies['bass_energy'], 4),
            'low_mid_energy': round(band_energies['low_mid_energy'], 4),
            'mid_energy': round(band_energies['mid_energy'], 4),
            'high_mid_energy': round(band_energies['high_mid_energy'], 4),
            'presence_energy': round(band_energies['presence_energy'], 4),
            'brilliance_energy': round(band_energies['brilliance_energy'], 4),
            'air_energy': round(band_energies['air_energy'], 4),
            'dominant_frequency_band': dominant_band.replace('_energy', ''),
            'spectral_irregularity_mean': round(irregularity_mean, 4),
            'spectral_irregularity_std': round(irregularity_std, 4),
            'pitch_salience': round(pitch_salience, 3),
            'spectral_entropy_mean': round(entropy_mean, 2),
            'spectral_entropy_std': round(entropy_std, 2),
            'roughness_coefficient': round(roughness, 4),
            'mfcc_means': [round(m, 3) for m in mfcc_means],
            'chroma_mean': [round(c, 3) for c in chroma_mean],
            'spectral_contrast_mean': [round(c, 3) for c in contrast_mean]
        }