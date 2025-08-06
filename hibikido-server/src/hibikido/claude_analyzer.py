#!/usr/bin/env python3
"""
Hibikido Audio Analysis & Labeling Tool
Analyzes audio files and generates semantic descriptions via Claude API
"""

import os
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import librosa
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.audio_extensions = {'.wav', '.mp3', '.flac', '.aiff', '.aif', '.m4a', '.ogg', '.opus'}
        self.failed_files = []
        
    def find_audio_files(self, root_dir: Path) -> List[Path]:
        """Recursively find all audio files"""
        audio_files = []
        for file_path in root_dir.rglob('*'):
            if file_path.suffix.lower() in self.audio_extensions:
                audio_files.append(file_path)
        logger.info(f"Found {len(audio_files)} audio files")
        return audio_files
    
    def analyze_audio(self, file_path: Path) -> Optional[Dict]:
        """Extract comprehensive audio features"""
        try:
            # Load audio
            y, sr = librosa.load(str(file_path), sr=None)
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
            # Extract envelope using Hilbert transform for more accurate dynamics
            envelope = np.abs(librosa.util.pad_center(y, len(y)))
            # Smooth envelope for better attack/decay detection
            envelope_smooth = librosa.util.smooth(envelope, length=int(sr * 0.01))  # 10ms smoothing
            
            # Attack time (time to reach 90% of peak from 10%)
            peak_val = np.max(envelope_smooth)
            attack_start = np.argmax(envelope_smooth > 0.1 * peak_val)
            attack_end = np.argmax(envelope_smooth > 0.9 * peak_val)
            attack_time = (attack_end - attack_start) / sr if attack_end > attack_start else 0
            
            # Decay analysis (from peak to sustained level)
            peak_idx = np.argmax(envelope_smooth)
            if peak_idx < len(envelope_smooth) - 1:
                post_peak = envelope_smooth[peak_idx:]
                # Find where amplitude drops to 50% of peak
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
            # Divide spectrum into perceptually relevant bands
            stft = librosa.stft(y)
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
                # Find frequency bins in this band
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
            # Spectral irregularity (roughness measure)
            spectral_irregularity = []
            for frame in magnitude.T:
                if len(frame) > 2:
                    # Calculate differences between adjacent frequency bins
                    diffs = np.abs(np.diff(frame))
                    irregularity = np.sum(diffs) / (np.sum(frame) + 1e-8)
                    spectral_irregularity.append(irregularity)
            
            irregularity_mean = float(np.mean(spectral_irregularity)) if spectral_irregularity else 0.0
            irregularity_std = float(np.std(spectral_irregularity)) if spectral_irregularity else 0.0
            
            # Pitch salience (how "melodic" vs "textural")
            # Use harmonic-percussive separation ratio as a proxy
            pitch_salience = harmonic_ratio / (harmonic_ratio + percussive_ratio + 1e-8)
            
            # Spectral entropy (chaos vs order)
            spectral_entropy = []
            for frame in magnitude.T:
                if np.sum(frame) > 0:
                    # Normalize to probability distribution
                    prob = frame / np.sum(frame)
                    # Remove zeros to avoid log(0)
                    prob = prob[prob > 0]
                    entropy = -np.sum(prob * np.log2(prob + 1e-8))
                    spectral_entropy.append(entropy)
            
            entropy_mean = float(np.mean(spectral_entropy)) if spectral_entropy else 0.0
            entropy_std = float(np.std(spectral_entropy)) if spectral_entropy else 0.0
            
            # Roughness coefficient (sensory dissonance)
            # Based on spectral irregularity and inharmonicity
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
            
        except Exception as e:
            logger.error(f"Failed to analyze {file_path}: {e}")
            self.failed_files.append(str(file_path))
            return None
    
    def generate_description(self, file_path: Path, analysis: Dict) -> Optional[str]:
        """Generate semantic description via Claude API"""
        try:
            # Create analysis summary for prompt
            analysis_text = f"""
Audio file analysis:
- Duration: {analysis['duration']}s
- Tempo: {analysis['tempo']} BPM
- Spectral centroid: {analysis['spectral_centroid_mean']} Hz (brightness)
- RMS energy: {analysis['rms_mean']} (loudness)
- Harmonic ratio: {analysis['harmonic_ratio']} (tonal vs noisy)
- Percussive ratio: {analysis['percussive_ratio']} (rhythmic elements)
- Onset rate: {analysis['onset_rate']} events/second
- Zero crossing rate: {analysis['zero_crossing_rate_mean']} (texture indicator)
- Spectral flux: {analysis['spectral_flux_mean']} ± {analysis['spectral_flux_std']} (temporal brightness changes)
- Attack time: {analysis['attack_time']}s (onset sharpness)
- Decay time: {analysis['decay_time']}s (fade characteristics)
- Sustained level: {analysis['sustained_level']} (body/resonance)
- Dynamic range: {analysis['dynamic_range']} (amplitude variation)
- Dominant frequency band: {analysis['dominant_frequency_band']} (energy concentration)
- Spectral irregularity: {analysis['spectral_irregularity_mean']} ± {analysis['spectral_irregularity_std']} (texture roughness)
- Pitch salience: {analysis['pitch_salience']} (melodic vs textural character)
- Spectral entropy: {analysis['spectral_entropy_mean']} ± {analysis['spectral_entropy_std']} (chaos vs order)
- Roughness coefficient: {analysis['roughness_coefficient']} (sensory dissonance)
"""
            
            prompt = f"""You are describing a sound file to a deaf person using exactly 15-20 words. Create an evocative, poetic description that captures the essence and character of the sound based on this technical analysis:

{analysis_text}

Focus on texture, mood, movement, and sonic character. Use vivid, sensory language that would help someone imagine the sound. Examples of good descriptions:
- "ethereal forest breathing with crystalline droplets dancing through misty morning silence"
- "metallic scraping industrial decay echoing through abandoned cathedral spaces"
- "warm analog pulse rhythmically throbbing beneath layers of cosmic drift"

Respond with only the 15-20 word description, nothing else."""

            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self.api_key
                },
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 100,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            
            if response.status_code == 200:
                description = response.json()['content'][0]['text'].strip()
                logger.info(f"Generated description for {file_path.name}: {description}")
                return description
            else:
                logger.error(f"API error for {file_path}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate description for {file_path}: {e}")
            return None
    
    def process_directory(self, root_dir: Path, output_dir: Path):
        """Process all audio files in directory"""
        audio_files = self.find_audio_files(root_dir)
        
        results = []
        osc_commands = []
        
        for i, file_path in enumerate(audio_files, 1):
            logger.info(f"Processing {i}/{len(audio_files)}: {file_path.name}")
            
            # Get relative path from root directory
            relative_path = file_path.relative_to(root_dir)
            
            # Analyze audio
            analysis = self.analyze_audio(file_path)
            if analysis is None:
                continue
                
            # Generate description
            description = self.generate_description(file_path, analysis)
            if description is None:
                continue
            
            # Store result
            result = {
                'file_path': str(relative_path),
                'description': description,
                'analysis': analysis,
                'processed_at': datetime.now().isoformat()
            }
            results.append(result)
            
            # Create OSC command with embedded analysis data
            analysis_json = json.dumps(analysis, separators=(',', ':'))
            osc_command = f'/add_recording "{relative_path}" "{description}" {analysis_json}'
            osc_commands.append(osc_command)
        
        # Save results
        results_file = output_dir / 'hibikido_analysis_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Saved analysis results to {results_file}")
        
        # Save OSC commands
        osc_file = output_dir / 'hibikido_batch_import.osc'
        with open(osc_file, 'w') as f:
            f.write('\n'.join(osc_commands))
        logger.info(f"Saved OSC commands to {osc_file}")
        
        # Save failed files log
        if self.failed_files:
            failed_file = output_dir / 'hibikido_failed_files.log'
            with open(failed_file, 'w') as f:
                f.write('\n'.join(self.failed_files))
            logger.info(f"Logged {len(self.failed_files)} failed files to {failed_file}")
        
        logger.info(f"Processing complete: {len(results)} files processed, {len(self.failed_files)} failed")

def main():
    parser = argparse.ArgumentParser(description='Analyze audio files and generate descriptions for Hibikido')
    parser.add_argument('root_dir', help='Root directory containing audio files')
    parser.add_argument('--api-key', required=True, help='Anthropic API key')
    parser.add_argument('--output-dir', help='Output directory (defaults to root_dir)')
    
    args = parser.parse_args()
    
    root_dir = Path(args.root_dir)
    output_dir = Path(args.output_dir) if args.output_dir else root_dir
    output_dir.mkdir(exist_ok=True)
    
    if not root_dir.exists():
        logger.error(f"Root directory does not exist: {root_dir}")
        return
    
    analyzer = AudioAnalyzer(args.api_key)
    analyzer.process_directory(root_dir, output_dir)

if __name__ == '__main__':
    main()