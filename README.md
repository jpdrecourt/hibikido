# Hibikidō (響き道)

> _Still air awaits. Quivering breath. A sound, not yet. We begin..._

**Hibikidō** - The Way of Resonance - is an experimental artistic project that recognizes sounds waiting in latency through natural language. Cast incantations like _"ethereal forest breathing"_ or _"metallic scraping industrial decay"_ and let sonic events manifest when harmony permits.

## What It Does

Instead of browsing folders or remembering filenames, you speak to the system and wait for sound manifestations. The system understands semantic relationships - _"warm analog pulse"_ finds vintage synthesizer patterns, _"ritualistic drone"_ discovers deep sustained tones.

**Technical**: Neural semantic search over hierarchical audio database with real-time frequency conflict resolution.
**Artistic**: An invocation protocol where sounds emerge when "the cosmos permits" rather than on demand.

## Quick Start

### Get Running in 5 Minutes
```bash
# Clone and setup
git clone <repository-url> hibikido-project
cd hibikido-project
mkdir -p hibikido-data/{database,index,audio}

# Install and start server
cd hibikido-server
pip install -e ".[dev]"
cp sample_config.json config.json
python -m hibikido.main_server --config config.json

# Add your first sound (via OSC)
/add_recording "/path/to/audio.wav" "description" "atmospheric drone"

# Search for it
/invoke "atmospheric"
# → /manifest messages when sounds become available
```

See **[Quick Start Guide](docs/QUICK_START.md)** for detailed setup.

## Project Structure

```
hibikido-project/
├── hibikido-server/          # Python OSC server
├── hibikido-interface/       # Max/MSP client interface  
├── hibikido-data/           # Local data (not tracked)
│   ├── database/            # TinyDB JSON files
│   ├── index/               # FAISS semantic indices
│   └── audio/               # Audio files
└── docs/                    # Documentation
    ├── PHILOSOPHY.md        # Artistic vision and practice
    ├── TECHNICAL_GUIDE.md   # Complete technical reference
    └── QUICK_START.md       # Getting started guide
```

## Key Features

- **Semantic Search**: Natural language finds sounds by meaning, not filename
- **Real-time Orchestration**: Frequency conflict resolution prevents harmonic chaos
- **Portable**: Self-contained system with no external database dependencies
- **OSC Protocol**: Works with Max/MSP, Pure Data, SuperCollider, or any OSC client
- **Zero Setup**: TinyDB + FAISS, no MongoDB or complex installation

## Documentation

### For New Users
- **[Quick Start](docs/QUICK_START.md)** - Get running in 5 minutes
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Complete setup instructions

### For Developers  
- **[Technical Guide](docs/TECHNICAL_GUIDE.md)** - Architecture, OSC protocol, configuration
- **[Development Guide](CLAUDE.md)** - Working with Claude Code on this project

### For Artists
- **[Philosophy](docs/PHILOSOPHY.md)** - The Way of Resonance, spiritual practice, terminology
- **[Manual Testing](hibikido-server/tests/manual_testing.md)** - Creative workflow validation

## The Philosophy

Hibikidō implements an "invocation protocol" - sounds manifest when harmony permits rather than on immediate demand. The **Chōwasha** (harmony bringer) manages time-frequency niches, ensuring each sound finds its proper place while respecting the **Kazukorei** (wind spirit) that carries sonic possibilities through digital realms.

This creates an intentionally non-deterministic but harmonically-aware audio experience where manifestation follows natural law rather than user control.

Read more: **[Philosophy of Hibikidō](docs/PHILOSOPHY.md)**

## Technical Overview

- **Server**: Python with TinyDB, FAISS, sentence-transformers, python-osc
- **Interface**: Max/MSP patches with OSC communication
- **Architecture**: Semantic search → orchestrator queue → frequency conflict resolution → manifestation
- **Data**: Portable JSON database with neural embedding indices
- **Protocol**: OSC on ports 9000 (listen) / 9001 (send)

---

_Each manifestation must find its proper moment in the harmonic order._