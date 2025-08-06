#!/usr/bin/env python3
"""
Hibikido Batch Processing Tool
Processes directories of audio files and generates OSC commands for bulk import.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from feature_extractor import AudioFeatureExtractor
from semantic_analyzer import SemanticAnalyzer
import librosa

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BatchProcessor:
    """Processes audio files in batches for Hibikido import."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize batch processor.
        
        Args:
            api_key: Optional Anthropic API key for description generation
        """
        self.feature_extractor = AudioFeatureExtractor()
        self.semantic_analyzer = SemanticAnalyzer(api_key) if api_key else None
        self.audio_extensions = {'.wav', '.mp3', '.flac', '.aiff', '.aif', '.m4a', '.ogg', '.opus'}
        self.failed_files = []
        
    def find_audio_files(self, root_dir: Path) -> List[Path]:
        """Recursively find all audio files."""
        audio_files = []
        for file_path in root_dir.rglob('*'):
            if file_path.suffix.lower() in self.audio_extensions:
                audio_files.append(file_path)
        logger.info(f"Found {len(audio_files)} audio files")
        return audio_files
    
    def process_file(self, file_path: Path, root_dir: Path, 
                    generate_descriptions: bool = False) -> Optional[Dict]:
        """Process a single audio file."""
        try:
            logger.info(f"Processing: {file_path.name}")
            
            # Get relative path from root directory
            relative_path = file_path.relative_to(root_dir)
            
            # Extract comprehensive features
            features = self.feature_extractor.extract_features(str(file_path))
            if features is None:
                logger.error(f"Feature extraction failed for {file_path}")
                self.failed_files.append(str(file_path))
                return None
            
            # Generate description if requested and API key available
            description = None
            if generate_descriptions and self.semantic_analyzer:
                description = self.semantic_analyzer.generate_description(features)
                if description is None:
                    logger.warning(f"Description generation failed for {file_path}")
            
            result = {
                'file_path': str(relative_path),
                'description': description or f"Audio file: {file_path.name}",
                'features': features,
                'processed_at': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            self.failed_files.append(str(file_path))
            return None
    
    def process_directory(self, root_dir: Path, output_dir: Path, 
                         generate_descriptions: bool = False):
        """Process all audio files in directory."""
        audio_files = self.find_audio_files(root_dir)
        
        results = []
        osc_commands = []
        
        for i, file_path in enumerate(audio_files, 1):
            logger.info(f"Processing {i}/{len(audio_files)}: {file_path.name}")
            
            result = self.process_file(file_path, root_dir, generate_descriptions)
            if result is None:
                continue
                
            results.append(result)
            
            # Create OSC command for /add_recording
            # Format: /add_recording "relative_path" "description"  
            description = result['description'].replace('"', '\\"')  # Escape quotes
            osc_command = f'/add_recording "{result["file_path"]}" "{description}"'
            osc_commands.append(osc_command)
        
        # Save results
        results_file = output_dir / 'hibikido_batch_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Saved analysis results to {results_file}")
        
        # Save OSC commands
        osc_file = output_dir / 'hibikido_import_commands.osc'
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
        
        return {
            'processed': len(results),
            'failed': len(self.failed_files),
            'results_file': str(results_file),
            'osc_file': str(osc_file)
        }


def main():
    parser = argparse.ArgumentParser(
        description='Batch process audio files for Hibikido import',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process directory without descriptions
  python batch_processor.py /path/to/audio

  # Process with automatic description generation
  python batch_processor.py /path/to/audio --api-key YOUR_CLAUDE_KEY --generate-descriptions

  # Specify output directory
  python batch_processor.py /path/to/audio --output-dir /path/to/output
        """
    )
    
    parser.add_argument('root_dir', help='Root directory containing audio files')
    parser.add_argument('--api-key', help='Anthropic API key for description generation')
    parser.add_argument('--generate-descriptions', action='store_true',
                       help='Generate semantic descriptions (requires --api-key)')
    parser.add_argument('--output-dir', help='Output directory (defaults to root_dir)')
    
    args = parser.parse_args()
    
    root_dir = Path(args.root_dir)
    output_dir = Path(args.output_dir) if args.output_dir else root_dir
    output_dir.mkdir(exist_ok=True)
    
    if not root_dir.exists():
        logger.error(f"Root directory does not exist: {root_dir}")
        return 1
    
    if args.generate_descriptions and not args.api_key:
        logger.error("--generate-descriptions requires --api-key")
        return 1
    
    processor = BatchProcessor(args.api_key)
    
    try:
        stats = processor.process_directory(root_dir, output_dir, args.generate_descriptions)
        
        print("\n" + "="*50)
        print("🎵 BATCH PROCESSING COMPLETE 🎵")
        print("="*50)
        print(f"Processed: {stats['processed']} files")
        print(f"Failed: {stats['failed']} files")
        print(f"Results: {stats['results_file']}")
        print(f"OSC Commands: {stats['osc_file']}")
        
        if stats['failed'] == 0:
            print("\nNext steps:")
            print(f"1. Copy audio files to hibikido-data/audio/")
            print(f"2. Send OSC commands from {stats['osc_file']} to hibikido server")
            print("3. Use /generate_description commands for any files you want Claude descriptions for")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())