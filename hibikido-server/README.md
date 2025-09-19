# Hibikidō Server

Python OSC server implementing semantic audio search with real-time orchestration.

This server provides the core functionality for the Hibikidō system. For the complete artistic vision and philosophy, see [Philosophy](../docs/PHILOSOPHY.md). For technical details, see [Technical Guide](../docs/TECHNICAL_GUIDE.md).

## Development Setup

### Quick Start
```bash
cd hibikido-server
pip install -e ".[dev,audio]"  # Include audio analysis dependencies
cp sample_config.json config.json
python -m hibikido.main_server --config config.json
```

### Usage Examples

**Add content:**
```
/add_recording "ambient/forest.wav" "ethereal forest breathing"
# Performs comprehensive audio analysis (40+ features), creates full-length segment

/add_segment "audio.wav" "wind gusts" "start" 0.1 "end" 0.6
# Manual segment with full feature extraction and analysis
```

**Search:**
```
/invoke "atmospheric"
→ /manifest messages when sounds become available
```

**Monitor:**
```
/stats
→ Database and orchestrator statistics

/list_segments
→ Show segment IDs and descriptions

/get_segment_field 123 "features.spectral_entropy_mean"
→ Get specific field from segment data
```

See [Technical Guide](../docs/TECHNICAL_GUIDE.md) for complete OSC protocol reference.

## Architecture Overview

This server implements:
- **Semantic Search**: sentence-transformers + FAISS for neural similarity
- **Comprehensive Audio Analysis**: 40+ spectral, temporal, and perceptual features
- **Bark Band Analysis**: Perceptually-accurate 24-band spectral analysis for niche detection
- **Multi-Band Onset Detection**: 3-band onset analysis for percussive transient detection
- **AI-Powered Descriptions**: Claude API integration for semantic audio descriptions
- **Real-time Orchestration**: Cosine similarity conflict resolution using Bark bands
- **OSC Communication**: Ports 9000 (listen) / 9001 (send)
- **Portable Storage**: TinyDB JSON files, no external database

## Key Components

- `main_server.py` - OSC handler and coordination
- `orchestrator.py` - Bark band niche management and manifestation queue
- `audio_analyzer.py` - Combined audio analysis orchestrator
- `feature_extractor.py` - Comprehensive spectral, temporal, and perceptual feature extraction
- `bark_analyzer.py` - Perceptual audio analysis using 24 Bark frequency bands
- `energy_analyzer.py` - Multi-band onset detection across 3 frequency ranges
- `semantic_analyzer.py` - Claude API integration for audio descriptions
- `tinydb_manager.py` - Database operations and schema
- `embedding_manager.py` - Neural search and FAISS indexing
- `tools/batch_processor.py` - Batch processing for audio collections

## Bark Band Niche Analysis

The orchestrator uses perceptually-accurate **Bark band analysis** for intelligent conflict resolution:

- **24 Critical Bands**: Covers 0Hz to ~15.5kHz using the Bark scale
- **Cosine Similarity**: Compares spectral energy distributions between sounds
- **Configurable Threshold**: Default 0.5 similarity triggers conflict detection
- **Pre-computed Analysis**: Zero-latency orchestration for live performance

```json
{
  "orchestrator": {
    "bark_similarity_threshold": 0.5   // 50% similarity = conflict
  },
  "audio": {
    "audio_directory": "../hibikido-data/audio"  // Relative path resolution
  }
}
```

This replaces simple frequency range overlap with human perceptual modeling, allowing harmonically-related sounds to coexist while preventing spectral conflicts.

## Multi-Band Onset Detection

The energy analyzer performs onset detection across 3 frequency bands to capture percussive transients and attacks:

- **Low-mid (150-2000 Hz)**: Low-frequency transients, impacts, rumbles, machinery
- **Mid (500-4000 Hz)**: Primary onset detection, human vocal range, central activity, most natural sounds
- **High-mid (2000-8000 Hz)**: High-frequency transients, clicks, metallic sounds, insects, electronic artifacts

Each segment stores arrays of precise onset timestamps for all 3 bands, enabling detailed rhythmic analysis and visualization.

## Comprehensive Audio Analysis

The system extracts 40+ audio features for enhanced semantic search and AI description generation:

**Spectral Features**: MFCC coefficients, spectral centroid/rolloff/bandwidth, chroma features, spectral contrast
**Temporal Features**: Attack/decay times, sustained levels, dynamic range, onset rate
**Perceptual Features**: Pitch salience, spectral entropy, roughness coefficient, harmonic/percussive ratios
**Frequency Band Analysis**: Energy distribution across 8 perceptual frequency bands (sub-bass to air)

These features enable:
- **Superior Search**: More accurate semantic matching through detailed audio characteristics
- **AI Descriptions**: Claude API can generate poetic descriptions from technical features
- **Advanced Filtering**: Search by texture, mood, spectral character, or temporal dynamics

## Batch Processing

For bulk imports:
```bash
# Process directory with comprehensive analysis
python src/hibikido/tools/batch_processor.py /path/to/audio

# Add Claude descriptions
python src/hibikido/tools/batch_processor.py /path/to/audio --api-key KEY --generate-descriptions

# Outputs OSC commands ready for server import
```

---

For complete technical documentation, see [Technical Guide](../docs/TECHNICAL_GUIDE.md).
For the artistic philosophy and terminology, see [Philosophy](../docs/PHILOSOPHY.md).
