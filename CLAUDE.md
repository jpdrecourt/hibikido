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
python tests/test_smoke.py

# Or with pytest
pytest tests/test_smoke.py -v

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
- Background thread runs orchestrator updates every 100ms

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
3. Background thread processes queue every 100ms
4. Frequency conflict resolution using logarithmic overlap
5. `/manifest` messages sent when niches are available

### Key OSC Commands

```
/invoke "ethereal forest breathing"  # Search and queue manifestations
/add_recording "forest.wav" "description"  # Simplified: auto-analyzes Bark bands and duration
/add_segment "path" "desc" "start" 0.1 "end" 0.6  # Add timed segment (auto Bark analysis)
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

## Development Guidelines

- Always ask before starting to implement

## Development Tools

- Use python3 for all Python-based development and scripts
```