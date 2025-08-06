"""
Semantic description generation for Hibikidō using Claude API.
Generates poetic descriptions of audio based on comprehensive features.
"""

import json
import logging
import requests
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class SemanticAnalyzer:
    """Generates semantic descriptions of audio using Claude API."""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize semantic analyzer.
        
        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.api_key = api_key
        self.model = model
        
    def generate_description(self, features: Dict) -> Optional[str]:
        """
        Generate semantic description from audio features.
        
        Args:
            features: Dictionary of audio features from FeatureExtractor
            
        Returns:
            Generated description string or None if generation fails
        """
        try:
            # Create analysis summary for prompt
            analysis_text = f"""
Audio file analysis:
- Duration: {features['duration']}s
- Tempo: {features['tempo']} BPM
- Spectral centroid: {features['spectral_centroid_mean']} Hz (brightness)
- RMS energy: {features['rms_mean']} (loudness)
- Harmonic ratio: {features['harmonic_ratio']} (tonal vs noisy)
- Percussive ratio: {features['percussive_ratio']} (rhythmic elements)
- Onset rate: {features['onset_rate']} events/second
- Zero crossing rate: {features['zero_crossing_rate_mean']} (texture indicator)
- Spectral flux: {features['spectral_flux_mean']} ± {features['spectral_flux_std']} (temporal brightness changes)
- Attack time: {features['attack_time']}s (onset sharpness)
- Decay time: {features['decay_time']}s (fade characteristics)
- Sustained level: {features['sustained_level']} (body/resonance)
- Dynamic range: {features['dynamic_range']} (amplitude variation)
- Dominant frequency band: {features['dominant_frequency_band']} (energy concentration)
- Spectral irregularity: {features['spectral_irregularity_mean']} ± {features['spectral_irregularity_std']} (texture roughness)
- Pitch salience: {features['pitch_salience']} (melodic vs textural character)
- Spectral entropy: {features['spectral_entropy_mean']} ± {features['spectral_entropy_std']} (chaos vs order)
- Roughness coefficient: {features['roughness_coefficient']} (sensory dissonance)
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
                    "model": self.model,
                    "max_tokens": 100,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            
            if response.status_code == 200:
                description = response.json()['content'][0]['text'].strip()
                logger.info(f"Generated description: {description}")
                return description
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate description: {e}")
            return None