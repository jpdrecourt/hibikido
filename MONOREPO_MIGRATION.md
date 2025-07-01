# Monorepo Migration Guide

This document explains how to migrate from the original hibikido-server repository to the new monorepo structure.

## Why Migrate to Monorepo?

The original structure had components scattered across different locations:
- `hibikido-server/` - Python server code (separate git repo)
- `hibikido-interface/` - Max/MSP client (separate directory)
- MongoDB data - Global system installation
- FAISS index - In interface directory

**Problems:**
- Complex setup requiring MongoDB installation
- Data scattered across system
- Hard to backup/move complete system
- Version coordination between server/client difficult

**Monorepo benefits:**
- Single git repository for everything
- Portable deployment (no external dependencies)
- Easy backup (copy one directory)
- Version coordination between components
- Zero-dependency setup with TinyDB

## Migration Process

### Pre-Migration Checklist

- [ ] Backup current server repository
- [ ] Document any custom configurations
- [ ] Note locations of audio files and data
- [ ] Test current system to ensure it works

### Step 1: Backup Current Work

```bash
# Navigate to current hibikido-server directory
cd /path/to/hibikido-server

# Create backup bundle with complete git history
git bundle create hibikido-server-backup.bundle --all

# Move backup to safe location
mv hibikido-server-backup.bundle ~/backups/
```

### Step 2: Prepare New Structure

```bash
# Navigate to parent directory where you want the monorepo
cd /path/to/projects

# If you want to migrate in-place, rename current structure
mv hibikido-server hibikido-server-old
mkdir hibikido-project
```

### Step 3: Set Up Monorepo

```bash
cd hibikido-project

# Initialize new git repository
git init

# Create directory structure
mkdir -p hibikido-data/{database,index,audio}

# Copy server code (without .git directory)
cp -r /path/to/hibikido-server-old/* hibikido-server/
rm -rf hibikido-server/.git
rm hibikido-server/.gitignore  # We'll use monorepo gitignore

# Copy interface code
cp -r /path/to/hibikido-interface .

# Create gitignore for monorepo
```

Create `.gitignore`:
```gitignore
# Data directory - contains user-specific content
hibikido-data/database/
hibikido-data/index/
hibikido-data/audio/
!hibikido-data/.gitkeep

# User configurations
*/config.json
*/.claude/

# Python
__pycache__/
*.py[cod]
*.egg-info/
build/
dist/

# Audio files
*.wav
*.flac
*.mp3
*.aiff
*.index
*.pkl
*.npy
Sounds.csv

# IDEs
.vscode/
.idea/
*.swp
```

### Step 4: Update Interface Scripts

Update `hibikido-interface/start-hibikido.bat`:
```batch
@echo off
start "Hibikido Server" cmd /k ^
"cd /d %~dp0\..\hibikido-server ^
& python -m hibikido.main_server --config config.json"
```

Update `hibikido-interface/start-hibikido-debug.bat`:
```batch
@echo off
start "Hibikido Server" cmd /k ^
"cd /d %~dp0\..\hibikido-server ^
& python -m hibikido.main_server --config config.json --log-level DEBUG"
```

### Step 5: Verify Configuration

Check `hibikido-server/sample_config.json` uses correct paths:
```json
{
  "database": {
    "data_dir": "../hibikido-data/database"
  },
  "embedding": {
    "index_file": "../hibikido-data/index/hibikido.index"
  }
}
```

### Step 6: Initial Commit

```bash
# Add structure placeholder
echo "# Directory structure placeholder" > hibikido-data/.gitkeep

# Add everything to git
git add .

# Create initial commit
git commit -m "Initial monorepo with portable hibikido system

- Migrated hibikido-server with TinyDB support
- Added hibikido-interface (Max/MSP client)
- Created portable hibikido-data structure
- Updated scripts for monorepo structure
- Zero-dependency deployment ready"
```

### Step 7: Test Migration

```bash
# Test server startup
cd hibikido-server
cp sample_config.json config.json
python -m hibikido.main_server --config config.json

# Should see:
# INFO - TinyDB databases connected in: ../hibikido-data/database
# INFO - All components initialized successfully
```

Test interface:
```bash
cd ../hibikido-interface
# Open hibikido.maxpat in Max/MSP
# Or run start-hibikido.bat
```

## Post-Migration Tasks

### Migrate Existing Data

If you have existing MongoDB data to preserve:

1. **Export from MongoDB:**
   ```bash
   mongoexport --db hibikido --collection recordings --out recordings.json
   mongoexport --db hibikido --collection segments --out segments.json
   # etc.
   ```

2. **Import to TinyDB:**
   - Use the OSC interface to re-add recordings
   - Or write a simple Python script to import JSON data
   - Rebuild FAISS index with `/rebuild_index`

### Update Documentation

- Update any personal notes or documentation
- Update Max/MSP patches if they reference old paths
- Update any custom scripts or workflows

### Cleanup

After verifying everything works:
```bash
# Remove old directories
rm -rf hibikido-server-old
rm -rf old-hibikido-interface

# Remove migration helper files if desired
rm MONOREPO_MIGRATION.md  # (this file)
```

## Rollback Plan

If migration fails, you can restore the original setup:

```bash
# Restore server repository
git clone hibikido-server-backup.bundle hibikido-server-restored

# This gives you back the exact original state
```

## Benefits Achieved

After migration:
- ✅ **Single git repository** for entire project
- ✅ **Portable deployment** - copy folder anywhere
- ✅ **No external dependencies** - TinyDB instead of MongoDB
- ✅ **Consolidated data** - everything in hibikido-data/
- ✅ **Easy backup** - copy one directory
- ✅ **Version coordination** - server/client in sync
- ✅ **Simplified setup** - no database installation

## Troubleshooting Migration

**Import errors after migration:**
- Check Python dependencies: `pip install -e ".[dev]"`
- Verify all files copied correctly

**Interface connection issues:**
- Check batch scripts updated correctly
- Verify config.json paths point to `../hibikido-data/`
- Test server startup manually first

**Missing git history:**
- Git history is preserved in backup bundle
- Use `git clone hibikido-server-backup.bundle` to access
- Consider using `git subtree` or `git submodule` if you need history in monorepo