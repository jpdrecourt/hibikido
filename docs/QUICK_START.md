# Hibikidō Quick Start

Get up and running with semantic audio search in 5 minutes.

## What You Need

- Python 3.8+ with pip
- Max/MSP (for interface)
- Audio files to search through

## Installation

### 1. Get the Code
```bash
git clone <repository-url> hibikido-project
cd hibikido-project
```

### 2. Create Data Directory
```bash
mkdir -p hibikido-data/{database,index,audio}
```

### 3. Install Dependencies
```bash
cd hibikido-server
pip install -e ".[dev]"
```

### 4. Configure
```bash
cp sample_config.json config.json
# Edit config.json if needed - default settings work for most setups
```

## First Run

### Start the Server
```bash
cd hibikido-server
python -m hibikido.main_server --config config.json
```

You should see:
```
HIBIKIDŌ SERVER READY
Database stats: 0 segments, 0 presets, 0 searchable
OSC server listening on 127.0.0.1:9000
```

### Add Your First Sound
From Max/MSP or any OSC client:

```
Send to 127.0.0.1:9000:
/add_recording "/path/to/your/audio.wav" "description" "atmospheric drone"

Expected response:  
/confirm "added recording: your_file.wav with auto-segment"
```

### Test Search
```
Send: /invoke "atmospheric"

Expected responses:
/confirm "invoked: 1 resonances queued"
/manifest 0 "segments" 0.85 "/path/to/your/audio.wav" "atmospheric drone" 0.0 1.0 "[]"
```

## Understanding the Response

The `/manifest` message contains:
- `0` - manifestation index
- `"segments"` - type (segments or presets)  
- `0.85` - similarity score (0.0-1.0)
- `"/path/to/your/audio.wav"` - file path
- `"atmospheric drone"` - description
- `0.0 1.0` - start/end positions (normalized)
- `"[]"` - effect parameters (empty for segments)

## Adding More Content

### Batch Add Audio Files
```bash
# Put audio files in hibikido-data/audio/
# Then add them via OSC:

/add_recording "hibikido-data/audio/forest_ambience.wav" "description" "forest wind through trees"
/add_recording "hibikido-data/audio/metal_scrape.wav" "description" "metallic scraping industrial"
/add_recording "hibikido-data/audio/synth_pad.wav" "description" "warm analog synthesizer pad"
```

### Add Specific Segments
For precise timing:
```
/add_segment "your_file.wav" "description" "wind gusts" "start" 0.1 "end" 0.6 "segmentation_id" "manual" "freq_low" 200 "freq_high" 2000 "duration" 3.5
```

### Check Your Database
```
Send: /stats
Response: /stats_result [recordings] [segments] [effects] [presets] [embeddings] [active_niches] [queued]
```

## Try Different Searches

Once you have several sounds:

```
/invoke "forest"          → nature recordings
/invoke "metallic harsh"  → industrial sounds  
/invoke "warm pad"        → synthesizer textures
/invoke "rhythmic"        → percussive elements
```

## Max/MSP Interface

### Start the Interface
```bash
cd hibikido-interface
# Option A: Open hibikido.maxpat in Max/MSP
# Option B: Double-click start-hibikido.bat (Windows)
```

### Basic Interface Usage
1. **Connect**: Interface should auto-connect to server
2. **Search**: Type descriptions in the search box
3. **Listen**: Manifestations appear as they become available
4. **Play**: Trigger audio playback from manifestations

## Next Steps

### Build Your Sound Library
- Add 20-50 audio files with descriptive names
- Use varied descriptions for better semantic coverage
- Test different search terms to find your sounds

### Explore Advanced Features  
- Read [Technical Guide](TECHNICAL_GUIDE.md) for OSC protocol details
- Read [Philosophy](PHILOSOPHY.md) for the artistic vision
- Check [Deployment Guide](../DEPLOYMENT_GUIDE.md) for production setup

### Customize Configuration
Edit `config.json` to adjust:
- Search sensitivity (`min_score`)
- Number of results (`top_k`)  
- Orchestration timing (`time_precision`)
- Frequency overlap threshold (`overlap_threshold`)

## Troubleshooting

**Server won't start:**
- Check Python version: `python --version`
- Install dependencies: `pip install -e ".[dev]"`

**No search results:**
- Add content first with `/add_recording`
- Check database with `/stats`

**OSC connection issues:**
- Verify server is running first
- Check ports 9000/9001 aren't blocked
- Confirm IP addresses match in config and client

**Slow responses:**
- Large audio libraries take time to process
- Consider using SSD storage
- Monitor memory usage

## Performance Tips

- **Start small**: Begin with 10-20 audio files
- **Descriptive filenames**: Help with semantic indexing
- **Consistent descriptions**: Use similar language patterns
- **Regular rebuilds**: Run `/rebuild_index` after bulk changes

Ready to explore? Try the [manual testing guide](../hibikido-server/tests/manual_testing.md) for creative workflow validation.