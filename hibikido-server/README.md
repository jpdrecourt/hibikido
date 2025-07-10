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

**Add content (simplified syntax):**
```
/add_recording "ambient/forest.wav" "ethereal forest breathing"
# Automatically calculates duration, Bark bands, and 3-band onset analysis, creates full-length segment

/add_segment "audio.wav" "wind gusts" "start" 0.1 "end" 0.6
# Manual segment creation with auto Bark band and onset analysis
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
```

See [Technical Guide](../docs/TECHNICAL_GUIDE.md) for complete OSC protocol reference.

## Architecture Overview

This server implements:
- **Semantic Search**: sentence-transformers + FAISS for neural similarity
- **Bark Band Analysis**: Perceptually-accurate 24-band spectral analysis for niche detection
- **Multi-Band Onset Detection**: 3-band onset analysis for percussive transient detection
- **Real-time Orchestration**: Cosine similarity conflict resolution using Bark bands
- **OSC Communication**: Ports 9000 (listen) / 9001 (send)
- **Portable Storage**: TinyDB JSON files, no external database

## Key Components

- `main_server.py` - OSC handler and coordination
- `orchestrator.py` - Bark band niche management and manifestation queue
- `bark_analyzer.py` - Perceptual audio analysis using 24 Bark frequency bands
- `energy_analyzer.py` - Multi-band onset detection across 3 frequency ranges
- `tinydb_manager.py` - Database operations and schema
- `embedding_manager.py` - Neural search and FAISS indexing

## Bark Band Niche Analysis

The orchestrator uses perceptually-accurate **Bark band analysis** for intelligent conflict resolution:

- **24 Critical Bands**: Covers 0Hz to ~15.5kHz using the Bark scale
- **Cosine Similarity**: Compares spectral energy distributions between sounds
- **Configurable Threshold**: Default 0.5 similarity triggers conflict detection
- **Pre-computed Analysis**: Zero-latency orchestration for live performance

```json
{
  "orchestrator": {
    "bark_similarity_threshold": 0.5,  // 50% similarity = conflict
    "time_precision": 0.1              // 100ms update rate
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

---

For complete technical documentation, see [Technical Guide](../docs/TECHNICAL_GUIDE.md).
For the artistic philosophy and terminology, see [Philosophy](../docs/PHILOSOPHY.md).
