# Release Workflow

## For Repository Maintainers

### Creating a New Release

1. **Prepare the release**:
   - Ensure all changes are committed and pushed
   - Update version numbers if needed
   - Test the application thoroughly

2. **Build the executable**:
   ```bash
   python build.py
   ```
   - This creates `dist/Traktor-DJ-NowPlaying-Discord-Bot-GUI.exe` (static filename)
   - Version number is automatically included from `version.py`

3. **Test the executable**:
   - Test on a clean Windows system (without Python installed)
   - **Test the setup flow**: Run without `.env` file to verify auto-creation works
   - **Test with template values**: Verify detection of unconfigured template values
   - **Test with real config**: Verify normal operation with proper `.env` file
   - Verify all functionality works

4. **Create GitHub Release**:
   - Go to your GitHub repository
   - Click "Releases" → "Create a new release"
   - Tag version: `v1.0.0` (follow semantic versioning)
   - Release title: `Traktor DJ NowPlaying Discord Bot v1.0.0`
   - Description: Include changelog and setup instructions
   - Upload the `Traktor-DJ-NowPlaying-Discord-Bot-GUI.exe` file
   - Mark as latest release

5. **Update version for next release**:
   - Edit `version.py` to increment version number
   - Update version history in the file

5. **Clean up**:
   - The `dist/` folder is git-ignored, so build files won't be committed
   - PyInstaller spec files are ignored too

## File Management

### What gets committed to Git:
- ✅ Source code (`*.py`)
- ✅ Configuration files (`.env.example`, `requirements.txt`)
- ✅ Documentation (`README.md`)
- ✅ Build scripts (`build.py`, `build.bat`)

### What stays local/ignored:
- ❌ Built executables (`dist/` folder)
- ❌ Build artifacts (`build/` folder, `*.spec` files)
- ❌ Personal environment files (`.env`)
- ❌ PyInstaller cache files

### Distribution:
- **Source code**: Available via Git clone/download
- **Executables**: Available via GitHub Releases only

## Version Management

We follow **Semantic Versioning (SemVer)** with the format `vA.B.C`:

### Version Number Guidelines:
- **A (Major)**: Major feature additions, complete rewrites, breaking changes
  - Example: `v1.0.0` → `v2.0.0` (GUI introduction, architecture changes)
- **B (Minor)**: New features, enhancements, non-breaking additions
  - Example: `v1.0.0` → `v1.1.0` (new commands, feature improvements)
- **C (Patch)**: Bug fixes, minor tweaks, maintenance updates
  - Example: `v1.0.0` → `v1.0.1` (bug fixes, performance improvements)

### Release Process:
- Tag releases in Git: `v1.0.0`, `v1.1.0`, `v1.0.1`, etc.
- Include detailed changelog in release descriptions
- Mark stable releases as "Latest Release"
- Use pre-release tags for testing: `v1.1.0-beta.1`, `v1.1.0-rc.1`

This follows industry-standard **Semantic Versioning** practices, ensuring clear communication about the scope and impact of each release.

## User Instructions

### For users WITH Python:
```bash
git clone <repo-url>
cd Traktor-DJ-NowPlaying-Discord-Bot
pip install -r requirements.txt
python gui.py
```

### For users WITHOUT Python:
1. Go to GitHub Releases
2. Download `Traktor-DJ-NowPlaying-Discord-Bot-GUI.exe` (or latest version)
3. **First Launch**: Run the executable - it will automatically create a `.env` file and show setup instructions
4. **Configure**: Edit the `.env` file with your Discord bot settings and file paths
5. **Second Launch**: Run the executable again to start the bot

### Important Notes for End Users:
- **Automatic Setup**: The first run creates a `.env` template with clear instructions
- **Two-Step Process**: First run creates config file, second run starts the bot
- **No Technical Knowledge Required**: Follow the popup instructions for configuration
- **Portable**: The executable can be run from any location (uses its own directory for files)
- **All data files** (song_requests.json, etc.) are created in the executable's directory
- **Use absolute paths** in your `.env` file for Traktor collection location
