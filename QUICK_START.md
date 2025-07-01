# Hibikidō Quick Start Guide

## Prerequisites
- Python 3.8+ with pip
- Max/MSP (for interface)
- No database installation required (uses TinyDB)

## Setup

### 1. Clone and Setup
```bash
git clone <your-repo-url> hibikido-project
cd hibikido-project

# Create data directories
mkdir -p hibikido-data/{database,index,audio}
```

### 2. Install Server Dependencies
```bash
cd hibikido-server
pip install -e ".[dev]"
```

### 3. Configure Server
```bash
# Copy and customize configuration
cp sample_config.json config.json

# Optional: Edit config.json for your needs
# All paths are relative to hibikido-data/
```

### 4. Start Server
```bash
python -m hibikido.main_server --config config.json
```

You should see:
```
INFO - TinyDB databases connected in: ../hibikido-data/database
INFO - All components initialized successfully
INFO - Hibikidō server running on 127.0.0.1:9000
```

### 5. Start Interface
```bash
cd ../hibikido-interface
# Open hibikido.maxpat in Max/MSP
# Or double-click start-hibikido.bat (Windows)
```

## Basic Usage

### Add Audio Content
```bash
# Via OSC (from Max or any OSC client):
/add_recording "/path/to/audio.wav" "description"
/add_segment "/path/to/audio.wav" "segment_desc" "start" 1.0 "end" 3.0
```

### Invoke Sounds
```bash
# Semantic search and manifestation:
/invoke "ethereal forest breathing"
/invoke "metallic percussion"
```

### Check Status
```bash
/stats  # Database and orchestrator status
```

## File Structure
```
hibikido-project/
├── hibikido-server/          # Python OSC server
├── hibikido-interface/       # Max/MSP client  
└── hibikido-data/           # Your local data
    ├── database/            # TinyDB JSON files
    ├── index/               # FAISS indices
    └── audio/               # Your audio files
```

## Troubleshooting

**Server won't start:**
- Check Python dependencies: `pip install -e ".[dev]"`
- Verify config.json paths point to `../hibikido-data/`

**No sound responses:**
- Add audio content first with `/add_recording`
- Check `/stats` for database content
- Verify OSC ports (default 9000/9001) aren't blocked

**Interface connection issues:**
- Ensure server is running first
- Check OSC IP/port settings in Max patch
- Try `/stats` command to test connection