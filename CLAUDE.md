# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

This is an experimental artistic project for personal use. Prioritize simple, straightforward solutions over complex architectures. Imperfect but functional code is preferred over over-engineered solutions.

## Development Commands

### Running the Server
```bash
# Basic startup
python -m hibikido.main_server

# With custom config and debug logging
python -m hibikido.main_server --config config.json --log-level DEBUG

# Using the installed script
hibikido-server --config sample_config.json
```

### Testing
```bash
# Run smoke tests (simplified testing approach)
cd hibikido-server
PYTHONPATH=src python3 tests/test_smoke.py

# Or with pytest (if installed)
PYTHONPATH=src pytest tests/test_smoke.py -v

# Manual testing guide
# See tests/manual_testing.md for creative workflow validation
```

### Code Quality
```bash
# JavaScript/Node.js tools (for frontend components)
npm run lint  # ESLint + Prettier

# Python formatting and linting
black src/ tests/  # Code formatting
flake8 src/ tests/  # Linting
```

### Dependencies
```bash
# Install for development
pip install -e ".[dev]"

# Optional GPU support
pip install -e ".[gpu]"

# Optional audio analysis tools
pip install -e ".[audio]"
```

## Architecture Overview

Hibikidō is a semantic audio search system with real-time orchestration using Bark band analysis. The core concept: natural language descriptions invoke audio segments that manifest when perceptual spectral space allows.

### Core Components

**Main Server** (`main_server.py`):
- OSC communication on ports 9000 (listen) and 9001 (send)
- Command routing through `OSCRouter` and `CommandHandlers`
- Event-driven orchestrator processes queue when manifestations are added or niches freed

**Orchestrator** (`orchestrator.py`):
- Manages Bark band "niches" to prevent spectral conflicts
- FIFO queue for all search results - no immediate manifestations
- Cosine similarity conflict detection using 24 Bark frequency bands (default 0.5 threshold)
- Sends `/manifest` OSC messages when sounds can play

**Bark Analyzer** (`bark_analyzer.py`):
- Perceptual audio analysis using 24 critical frequency bands (Bark scale)
- Pre-computed spectral fingerprints for zero-latency orchestration
- Cosine similarity comparison between normalized energy vectors
- Automatic duration calculation from audio files

**TinyDB Manager** (`tinydb_manager.py`):
- JSON file collections: recordings, segments, effects, presets, performances
- Path-based references (segments reference `source_path`, presets reference `effect_path`)
- Hierarchical schema: recordings contain segments, effects contain presets
- Fully portable - no external database required

**Embedding Manager** (`embedding_manager.py`):
- Uses sentence-transformers for semantic search
- FAISS index for vector similarity
- Default model: all-MiniLM-L6-v2

**Energy Analyzer** (`energy_analyzer.py`):
- Multi-band onset detection using spectral novelty across 3 frequency bands:
  - Low-mid (150-2000 Hz): Low-frequency transients, impacts, rumbles
  - Mid (500-4000 Hz): Primary onset detection, human vocal range, central activity
  - High-mid (2000-8000 Hz): High-frequency transients, clicks, metallic sounds
- IQR-based adaptive thresholding for robust onset detection per band
- Handles varying signal dynamics (quiet passages, sirens, etc.)
- Returns onset times arrays for segments

**Feature Extractor** (`feature_extractor.py`):
- Comprehensive spectral, temporal, and perceptual audio analysis
- 40+ features including MFCCs, spectral descriptors, envelope dynamics, frequency band energies
- Perceptual qualities: pitch salience, spectral entropy, roughness coefficient
- Optimized for semantic description generation and advanced search

**Semantic Analyzer** (`semantic_analyzer.py`):
- Claude API integration for poetic audio descriptions
- Converts technical features into evocative natural language
- Configurable via API key in config.json
- On-demand generation to control API costs

**Audio Visualizer** (`visualizer.py`):
- Multi-band onset analysis visualization (Low-mid, Mid, High-mid frequency ranges)
- Spectrograms with detected onsets overlay
- Accessible via `/visualize_segment` OSC command
- Helps debug and understand onset detection behavior

**Audio Analyzer** (`audio_analyzer.py`):
- Unified audio analysis interface combining feature extraction and energy analysis
- Integrates with loaded audio data for comprehensive segment analysis
- Coordinates between feature extraction, onset detection, and Bark band analysis
- Used by command handlers for complete audio processing workflows

**Text Processor** (`text_processor.py`):
- Creates embedding text from structured data for semantic search
- Combines segment, recording, and segmentation metadata into searchable text
- Generates preset embedding text from effect and parameter information
- Ensures consistent text representation across the database

**Component Factory** (`component_factory.py`):
- Centralized factory for creating and initializing all system components
- Manages component dependencies and initialization order
- Provides clean separation between configuration and component creation
- Ensures all components are properly configured and connected

### Portable Data Structure

The system now uses a fully portable structure with no external dependencies:

```
hibikido-project/
├── hibikido-server/          # Server code
├── hibikido-interface/       # Max/MSP client (separate)
└── hibikido-data/           # All data in one place
    ├── database/            # TinyDB JSON files
    │   ├── recordings.json  # Audio file metadata
    │   ├── segments.json    # Timestamped segments  
    │   ├── effects.json     # Effect definitions
    │   ├── presets.json     # Effect presets
    │   ├── performances.json # Session logs
    │   └── segmentations.json # Batch processing
    ├── index/               # FAISS indices
    │   └── hibikido.index   # Main semantic index
    └── audio/               # Audio files (optional)
```

**Key Benefits:**
- No MongoDB installation required (uses TinyDB)
- All data consolidated in one directory
- Easy backup/migration (copy hibikido-data/)
- Self-contained and portable

### Data Flow

1. OSC `/invoke "description"` → semantic search
2. All results queued through orchestrator (no completion signal)
3. Event-driven orchestrator processes queue immediately when manifestations are queued or niches become available
4. Frequency conflict resolution using logarithmic overlap
5. `/manifest` messages sent when niches are available

### OSC Message Formats

**Manifest Message** (sent when sound can play):
```
/manifest [manifestation_id] [collection] [score] [path] [description] [start] [end] [parameters]
```
- `parameters`: JSON string containing metadata (e.g., `{"segment_id": "123"}`)

**Segment Field Response** (response to `/get_segment_field`):
```
/segment_field [segment_id] [field_name] [value]
```

### Key OSC Commands

```
/invoke "ethereal forest breathing"  # Search and queue manifestations
/add_recording "forest.wav" "description"  # Add recording with comprehensive feature analysis
/add_segment "path" "desc" "start" 0.1 "end" 0.6  # Add segment with full analysis
/list_segments  # Show segment IDs and descriptions (first 10)
/get_segment_field 123 "features.spectral_entropy_mean"  # Get specific field from segment
/visualize 123  # Show multi-band onset analysis for segment ID (integer)
/stats  # Database and orchestrator status
/rebuild_index  # Regenerate embeddings
```

### Configuration

Configuration via `config.json` (see `sample_config.json`):
- TinyDB data directory path (relative paths supported)
- FAISS index file location
- OSC ports and embedding model
- Search parameters (top_k, min_score)
- Orchestrator settings (bark_similarity_threshold, time_precision)
- Audio directory for relative path resolution
- Claude API key for semantic description generation (optional)

### Testing Strategy

Simplified testing approach for artistic project:
- **Smoke tests** (`test_smoke.py`): Essential "does it work?" validation
- **Manual testing** (`manual_testing.md`): Creative workflow guide
- **Philosophy**: Focus on "does it inspire creativity?" over exhaustive coverage

Manual testing during creative sessions is prioritized over automated tests.
For personal artistic tools, functional validation matters more than test coverage.

### Development Patterns

**Adding New OSC Commands**: Implement handler in `CommandHandlers` class, register route in `OSCRouter`.

**Debugging Orchestration**: Enable DEBUG logging to see niche conflicts and queue processing.

**Database Schema Changes**: Update `HibikidoDatabase` methods in `tinydb_manager.py`. TinyDB automatically handles schema evolution.

**Launch Workflow**: Max/MSP runs batch scripts from `hibikido-interface/` which cd to `hibikido-server/` and use `config.json` from there.

The system implements an "invocation protocol" - sounds manifest when "the cosmos permits" rather than on demand, creating an intentionally non-deterministic but perceptually-aware audio experience using Bark band analysis for conflict detection.

## Principles

- Do not keep backward compatibility, but tell me when a change is breaking.
- Unless specifically requested, don't keep backwards compatibility

## Development Guidelines

- Always ask before starting to implement

## Development Tools

- Use python3 for all Python-based development and scripts
```