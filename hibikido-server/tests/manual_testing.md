# Manual Testing Guide for Hibikidō

For an artistic project, manual testing during creative sessions is often more valuable than automated tests. This guide provides a structured approach to validating the system works for your creative workflow.

## Basic System Validation

### 1. Server Startup
```bash
cd hibikido-server
python -m hibikido.main_server --config sample_config.json
```

**Expected:**
- No error messages or warnings
- "HIBIKIDŌ SERVER READY" banner appears
- Database stats show clean state: "0 segments, 0 presets, 0 searchable"

### 2. OSC Connection Test
Using Max/MSP or any OSC client:

```
Send: /stats
Expected: Confirmation message with database statistics
```

### 3. Basic Content Workflow

**Add a recording:**
```
Send: /add_recording "/path/to/your/audio.wav" "atmospheric drone"
Expected: "added recording: [path] with auto-segment"
(Includes comprehensive audio analysis: 40+ features + Bark bands + 3-band onset detection)
```

**Verify content:**
```
Send: /stats  
Expected: "1 segments, 0 presets, 1 searchable"
```

**Test semantic search:**
```
Send: /invoke "atmospheric"
Expected: "invoked: 1 resonances queued"
Then: /manifest message with audio file details
```

**Test segment listing and visualization:**
```
Send: /list_segments
Expected: List of segments with IDs and descriptions

Send: /get_segment_field 1 "features.spectral_entropy_mean"
Expected: /segment_field "1" "features.spectral_entropy_mean" "8.58" (specific value will vary)

Send: /visualize 1
Expected: Multi-band onset analysis visualization for segment ID 1

Send: /generate_description "segment" 1
Expected: "generated description for segment 1" (requires Claude API key in config)
```

## Creative Workflow Testing

### Sound Library Integration
1. Add several recordings with varied descriptions
2. Test AI-generated descriptions:
   - Add recordings without descriptions: `/add_recording "path" ""`
   - Generate descriptions: `/generate_description "segment" [ID]`
   - Compare AI vs manual descriptions for search quality
3. Test different semantic queries:
   - Genre terms: "ambient", "industrial", "acoustic"
   - Mood terms: "dark", "ethereal", "energetic"  
   - Technical terms: "drone", "percussive", "harmonic"
   - Feature-based: "bright", "textural", "rhythmic", "sustained"
4. Verify manifestations match expectations

### Orchestration Testing
1. Add recordings with overlapping frequency ranges
2. Send multiple rapid invocations
3. Observe manifestation timing and conflict resolution
4. Verify sounds don't conflict harmonically

### Batch Processing Testing
1. **Test batch processor:**
   ```bash
   python src/hibikido/tools/batch_processor.py /path/to/test/audio
   ```
   Expected: Generates .osc file with import commands

2. **Test bulk import:**
   - Copy audio files to hibikido-data/audio/
   - Send OSC commands from generated file
   - Verify all files imported correctly

3. **Test AI descriptions:**
   ```bash
   python src/hibikido/tools/batch_processor.py /path/to/audio --api-key KEY --generate-descriptions
   ```
   Expected: Generates semantic descriptions for all files

### Performance Testing
1. Load a realistic sound library (50-200 files)
2. Test startup time with large database
3. Test search responsiveness during performance
4. Monitor memory usage during extended sessions
5. Test comprehensive feature extraction performance on various file sizes

## Troubleshooting Checklist

**Server won't start:**
- [ ] Python dependencies installed (`pip install -e ".[dev]"`)
- [ ] Data directory exists (`hibikido-data/`)
- [ ] Config file is valid JSON
- [ ] No port conflicts (9000/9001)

**No search results:**
- [ ] Content added to database (`/stats` shows > 0 segments)
- [ ] FAISS index exists and loaded
- [ ] Embedding model downloaded successfully

**OSC communication issues:**
- [ ] Client sending to correct IP/port (127.0.0.1:9000)
- [ ] Server listening on correct interface
- [ ] Firewall not blocking OSC ports

## Performance Benchmarks

For reference, on a typical development machine:

- **Startup time:** < 10 seconds with 100 audio files
- **Search response:** < 500ms for semantic queries
- **Memory usage:** ~200MB base + ~2MB per 100 audio files
- **Index rebuild:** ~1 minute for 1000 segments

## Creative Session Validation

The ultimate test is using Hibikidō in actual creative work:

1. **Intuitive search:** Can you find sounds by describing what you hear in your mind?
2. **Sonic coherence:** Do manifestations create pleasing sonic relationships?
3. **Creative flow:** Does the system inspire rather than interrupt your creative process?
4. **Reliability:** Does it work consistently during extended creative sessions?

Remember: For an artistic tool, "it inspires creativity" is more important than "it has 100% test coverage."