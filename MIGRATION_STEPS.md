# Monorepo Migration Steps

Follow these steps to complete the monorepo migration:

## Phase 1: Backup and Prepare

```bash
# 1. Navigate to project root
cd /mnt/c/Users/jpdre/Music/Projects/250422-Lisboa-Incomum-Octo/hibikido-project

# 2. Backup server git history
cd hibikido-server
git bundle create ../hibikido-server-backup.bundle --all
cd ..

# 3. Remove old git repos
rm -rf hibikido-server/.git
rm hibikido-server/.gitignore
```

## Phase 2: Initialize Monorepo

```bash
# 4. Initialize new git repository
git init

# 5. Copy monorepo configuration
cp MONOREPO_GITIGNORE .gitignore
rm MONOREPO_GITIGNORE

# 6. Ensure data structure
mkdir -p hibikido-data/{database,index,audio}
echo "# Directory structure placeholder" > hibikido-data/.gitkeep

# 7. First commit
git add .
git commit -m "Initial monorepo with server and interface

- Complete hibikido-server codebase with TinyDB migration
- Max/MSP hibikido-interface client
- Portable hibikido-data structure
- Configured for zero-dependency deployment"
```

## Phase 3: Update Configurations

```bash
# 8. Update server config paths (if needed)
cd hibikido-server
# Verify sample_config.json points to ../hibikido-data/
# Update any hardcoded paths in documentation

# 9. Update interface scripts
cd ../hibikido-interface
# Update .bat files to reference ../hibikido-server/ if needed
```

## Phase 4: Test and Verify

```bash
# 10. Test server startup
cd hibikido-server
cp sample_config.json config.json
python -m hibikido.main_server --config config.json

# 11. Verify data structure
ls -la ../hibikido-data/
# Should show database/, index/, audio/ directories

# 12. Test interface connection
# Open hibikido.maxpat and verify OSC connection
```

## Result

You'll have:
- ✅ Single git repository containing everything
- ✅ Preserved server development history
- ✅ Portable data structure
- ✅ Clean separation of code vs. data
- ✅ Easy deployment and backup

## Rollback (if needed)

If something goes wrong:
```bash
# Restore server repository
git clone hibikido-server-backup.bundle hibikido-server-restored
# This gives you back the original server repo
```