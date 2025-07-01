# Hibikidō Server

Python OSC server implementing semantic audio search with real-time orchestration.

This server provides the core functionality for the Hibikidō system. For the complete artistic vision and philosophy, see [Philosophy](../docs/PHILOSOPHY.md). For technical details, see [Technical Guide](../docs/TECHNICAL_GUIDE.md).

## Development Setup

### Quick Start
```bash
cd hibikido-server
pip install -e ".[dev]"
cp sample_config.json config.json
python -m hibikido.main_server --config config.json
```

### Usage Examples

**Add content:**
```
/add_recording "/path/to/audio.wav" "description" "atmospheric drone"
/add_segment "audio.wav" "description" "wind gusts" "start" 0.1 "end" 0.6
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
- **Real-time Orchestration**: Frequency conflict resolution with logarithmic overlap detection  
- **OSC Communication**: Ports 9000 (listen) / 9001 (send)
- **Portable Storage**: TinyDB JSON files, no external database

## Key Components

- `main_server.py` - OSC handler and coordination
- `orchestrator.py` - Frequency niche management and manifestation queue
- `tinydb_manager.py` - Database operations and schema
- `embedding_manager.py` - Neural search and FAISS indexing

For complete technical documentation, see [Technical Guide](../docs/TECHNICAL_GUIDE.md).
For the artistic philosophy and terminology, see [Philosophy](../docs/PHILOSOPHY.md).
