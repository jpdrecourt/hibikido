# Hibikidō Deployment Guide

Complete guide for setting up and deploying the portable Hibikidō system.

## System Architecture

Hibikidō uses a fully portable architecture with zero external dependencies:

```
hibikido-project/                    # Monorepo root
├── hibikido-server/                 # Python OSC server
│   ├── src/hibikido/               # Core application code
│   ├── tests/                      # Test suite
│   ├── sample_config.json          # Configuration template
│   └── README.md                   # Server documentation
├── hibikido-interface/             # Max/MSP client
│   ├── hibikido.maxpat            # Main interface patch
│   ├── start-hibikido.bat         # Windows server launcher
│   └── start-hibikido-debug.bat   # Debug mode launcher
├── docs/                           # Documentation
│   ├── PHILOSOPHY.md              # Artistic vision
│   ├── TECHNICAL_GUIDE.md         # Complete technical reference
│   └── QUICK_START.md             # Getting started guide
├── CLAUDE.md                       # Development guide for Claude Code
├── DEPLOYMENT_GUIDE.md            # This file
└── hibikido-data/                  # Local data (not tracked in git)
    ├── database/                   # TinyDB JSON files
    ├── index/                      # FAISS semantic indices
    └── audio/                      # User audio files
```

## Quick Setup

### Prerequisites
- Python 3.8+ with pip
- Max/MSP (for interface)
- No database installation required

### Installation Steps

1. **Clone Repository**
   ```bash
   git clone <repository-url> hibikido-project
   cd hibikido-project
   ```

2. **Create Data Structure**
   ```bash
   mkdir -p hibikido-data/{database,index,audio}
   ```

3. **Install Python Dependencies**
   ```bash
   cd hibikido-server
   pip install -e ".[dev]"
   ```

4. **Configure System**
   ```bash
   cp sample_config.json config.json
   # Edit config.json if needed - all paths are relative to hibikido-data/
   ```

5. **Start Server**
   ```bash
   python -m hibikido.main_server --config config.json
   ```

6. **Start Interface**
   ```bash
   cd ../hibikido-interface
   # Option A: Open hibikido.maxpat in Max/MSP
   # Option B: Double-click start-hibikido.bat (Windows)
   ```

## Deployment Options

### Local Development
- Use the setup above for local testing and development
- Data stays in `hibikido-data/` directory
- Easy to backup: copy entire `hibikido-project/` folder

### Portable Installation
- Copy entire `hibikido-project/` folder to any location
- No additional installation required
- Works across different machines with Python + Max/MSP

### Performance/Installation Setup
- Copy `hibikido-project/` to performance computer
- Pre-populate `hibikido-data/audio/` with sound library
- Use batch scripts for easy startup
- Consider SSD storage for fast audio access

## Configuration Details

### Server Configuration (`config.json`)
```json
{
  "database": {
    "data_dir": "../hibikido-data/database"
  },
  "embedding": {
    "model_name": "all-MiniLM-L6-v2",
    "index_file": "../hibikido-data/index/hibikido.index"
  },
  "osc": {
    "listen_ip": "127.0.0.1",
    "listen_port": 9000,
    "send_ip": "127.0.0.1", 
    "send_port": 9001
  },
  "search": {
    "top_k": 10,
    "min_score": 0.3
  },
  "orchestrator": {
    "bark_similarity_threshold": 0.5
  }
}
```

### Interface Scripts
- `start-hibikido.bat` - Normal startup
- `start-hibikido-debug.bat` - Debug mode with verbose logging
- Both scripts automatically navigate to server directory and use correct config

## Data Management

### Audio Files
- Place audio files in `hibikido-data/audio/` or any accessible path
- Supported formats: WAV, FLAC, MP3, AIFF (anything supported by your audio library)
- Use descriptive filenames for better semantic indexing

### Database
- TinyDB automatically creates JSON files in `hibikido-data/database/`
- No manual database setup required
- Files: `recordings.json`, `segments.json`, `effects.json`, `presets.json`, `performances.json`

### Backup Strategy
- **Code**: Managed by git (server + interface)
- **Data**: Copy `hibikido-data/` directory
- **Complete backup**: Copy entire `hibikido-project/` folder

## Troubleshooting

### Server Issues
**Server won't start:**
- Check Python installation: `python --version`
- Install dependencies: `pip install -e ".[dev]"`
- Verify config.json paths

**No audio responses:**
- Add content first: `/add_recording "/path/to/audio.wav" "description"`
- Check database: `/stats`
- Verify audio file paths are accessible

### Interface Issues
**OSC connection failed:**
- Ensure server is running first
- Check ports 9000/9001 aren't blocked
- Verify IP addresses in config and Max patch

**Batch scripts fail:**
- Check Python is in system PATH
- Verify server directory structure
- Try running server manually first

### Performance Issues
**Slow startup:**
- Large FAISS indices take time to load
- Consider separate indices for different collections
- Use SSD storage for better performance

**Memory usage:**
- Embedding models require RAM
- Large audio libraries increase memory usage
- Monitor with Task Manager/htop

## Advanced Configuration

### Multiple Sound Collections
Create separate configurations for different projects:
```bash
cp sample_config.json forest_sounds_config.json
# Edit paths to point to different hibikido-data directories
python -m hibikido.main_server --config forest_sounds_config.json
```

### Network Setup
For remote OSC clients, edit config.json:
```json
{
  "osc": {
    "listen_ip": "0.0.0.0",    # Listen on all interfaces
    "listen_port": 9000,
    "send_ip": "192.168.1.100", # Client machine IP
    "send_port": 9001
  }
}
```

### Custom Embedding Models
```json
{
  "embedding": {
    "model_name": "sentence-transformers/all-mpnet-base-v2", # Higher quality
    "index_file": "../hibikido-data/index/custom.index"
  }
}
```

## Migration from MongoDB Version

If upgrading from an older MongoDB-based version:

1. **Export MongoDB data** (if needed for preservation)
2. **Follow standard setup** above - TinyDB will create fresh databases
3. **Re-add audio content** using OSC commands
4. **Rebuild semantic index** with `/rebuild_index`

The new system maintains the same OSC interface, so existing Max patches and workflows continue to work unchanged.