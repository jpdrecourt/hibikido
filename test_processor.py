#!/usr/bin/env python3
"""Test the improved text processor with example descriptions."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hibikido-server', 'src'))

from hibikido.text_processor import TextProcessor

def test_processor():
    processor = TextProcessor()
    
    test_cases = [
        "Rising wail spirals outward like an alarmed cry, insistent and mournful, swelling in waves through open, echoing air.",
        "Hollow metallic breath sweeps upward, gliding in tremulous waves, like wind whistling through curved steel in a vast chamber.",
        "Hissing brakes, soft rumble, sudden squeals and low hums, a vehicle breathing as it lurches, pauses, and exhales metallically.",
        "Deep, deliberate beeps cut through air like sonar calls, echoing across water, alert and resonant with mechanical urgency.",
    ]
    
    print("Testing improved text processor:")
    print("=" * 60)
    
    for i, description in enumerate(test_cases, 1):
        print(f"\n{i}. Original:")
        print(f"   {description}")
        
        # Test segment creation
        segment = {"description": description}
        embedding_text = processor.create_segment_embedding_text(segment)
        
        print(f"   New embedding text:")
        print(f"   {embedding_text}")
        print(f"   Words: {len(embedding_text.split())}")

if __name__ == "__main__":
    test_processor()