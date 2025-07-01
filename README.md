# Hibikidō Project

An experimental artistic project implementing semantic audio search with real-time orchestration.

## Project Structure

```
hibikido-project/
├── hibikido-server/          # Python server with OSC communication
├── hibikido-interface/       # Max/MSP client interface  
└── hibikido-data/           # Local data directory (not tracked)
    ├── database/            # TinyDB JSON files
    ├── index/               # FAISS semantic indices
    └── audio/               # Audio files
```

## Quick Start

1. **Setup Data Directory**
   ```bash
   mkdir -p hibikido-data/{database,index,audio}
   ```

2. **Start Server**
   ```bash
   cd hibikido-server
   cp sample_config.json config.json
   python -m hibikido.main_server --config config.json
   ```

3. **Start Max/MSP Client**
   ```bash
   cd hibikido-interface
   # Open hibikido.maxpat in Max/MSP
   ```

## Components

### Server (Python)
- **TinyDB** for portable data storage (no MongoDB required)
- **FAISS** for semantic vector search
- **OSC** communication on ports 9000/9001
- **Real-time orchestration** with frequency conflict resolution

### Interface (Max/MSP)  
- Visual interface for sound invocation
- OSC client connecting to Python server
- Audio playback and processing

### Data
- **Portable structure** - entire project can be moved anywhere
- **Self-contained** - no external database dependencies
- **Gitignored** - user data stays local

## Documentation

### Setup and Deployment
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Complete setup instructions
- **[Monorepo Migration](MONOREPO_MIGRATION.md)** - Migration from older versions
- **[Quick Start](QUICK_START.md)** - Fast setup for new users

### Development
- [Server Documentation](hibikido-server/README.md) - Artistic vision and usage
- [Development Guide](hibikido-server/CLAUDE.md) - Technical development info

## Philosophy

The system implements an "invocation protocol" where sounds manifest when "the cosmos permits" rather than on demand, creating an intentionally non-deterministic but harmonically-aware audio experience.