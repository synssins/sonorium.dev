# Completed - Sonorium Development History

> **Note:** This file is NOT committed to git. It serves as long-term memory for
> completed work, implementation details, and decisions made. Reference this when
> working on similar features or debugging related issues.

---

## 2025-12-18

### Windows App: AirPlay Streaming Implementation (v0.2.30+)
**Files Modified:**
- `app/core/sonorium/streaming.py`

**Problem:**
- AirPlay speakers discovered via mDNS but streaming fails
- pyatv's `stream_url()` only works with Apple TV (video) devices
- Audio-only AirPlay speakers need RAOP push model, not HTTP pull

**Research Findings:**
- pyatv documentation: https://pyatv.dev/development/stream/
- `stream_file()` accepts: file paths, HTTP URLs, asyncio.StreamReader
- MP3 format works for streaming; WAV/OGG require seeking
- ~2 second audio delay is normal RAOP buffering

**Solution Implemented:**
```python
# Use curl to pipe HTTP MP3 stream to pyatv's stream_file()
process = await asp.create_subprocess_exec(
    "curl", "-s", "-N", session.stream_url,
    stdout=asp.PIPE, stderr=asp.PIPE
)
session._airplay_process = process

# Background task for streaming
async def stream_task():
    await atv.stream.stream_file(process.stdout)

session._airplay_task = asyncio.create_task(stream_task())
```

**Key design decisions:**
- Use curl subprocess for HTTP stream piping
- Background asyncio task for non-blocking streaming
- Store process and task handles for cleanup on stop
- Proper cleanup in `_stop_airplay()` - cancel task, kill process, close connection

**Status:** Implemented, awaiting testing with actual AirPlay speakers

---

### Windows App: Local Audio Fix (v0.2.30-alpha)
**Files Modified:**
- `app/core/requirements.txt`

**Problem:** Local audio devices not detected in Windows app.
**Cause:** `sounddevice` library missing from requirements.

**Fix:**
```
# Audio processing
av>=10.0.0
numpy>=1.24.0
sounddevice>=0.4.6  # Added this line
```

---

### Windows App: Embedded Python Module Loading Fix (v0.2.29-alpha)
**Files Modified:**
- `app/windows/src/launcher.py`

**Problem:**
- "ModuleNotFoundError: No module named 'sonorium'"
- Embedded Python (3.11 embeddable) ignores PYTHONPATH environment variable
- The `._pth` file in embedded Python disables site-packages and env vars

**Solution:**
```python
# Use runpy with sys.path injection instead of PYTHONPATH
bootstrap_code = f'''
import sys
sys.path.insert(0, r"{core_dir}")
sys.argv = [r"{main_script}", "--no-tray", "--no-browser", "--port", "{self.port}"]
import runpy
runpy.run_path(r"{main_script}", run_name="__main__")
'''
args = [str(python_exe), '-c', bootstrap_code]
```

**Why this works:**
- Embedded Python's `._pth` file makes it ignore PYTHONPATH
- But it still respects `sys.path` modifications at runtime
- `runpy.run_path()` properly handles `__name__` and `__main__`

---

### Windows App: GitHub Actions Build Workflow (v0.2.27+)
**Files Modified:**
- `.github/workflows/release.yml`

**Problem:** Local PyInstaller builds had PyQt6 errors that crashed at runtime.

**Solution:** Always use GitHub Actions for builds:
1. Push changes to GitHub
2. Create tag: `git tag v0.x.x-alpha && git push --tags`
3. Workflow automatically:
   - Downloads Python 3.11 embeddable
   - Installs pip via get-pip.py
   - Installs all requirements
   - Builds Sonorium.exe and updater.exe via PyInstaller
   - Creates GitHub release with assets

---

## 2025-12-17

### HA Addon: Web UI Fixes (RockettMan feedback)
**Files Modified:**
- `sonorium_addon/sonorium/web/static/js/app.js`

**Issues reported by RockettMan:**

1. **Mobile menu doesn't close after selection**
   - Problem: Sidebar stays open after tapping nav item on mobile
   - Fix: Added `sidebar.classList.remove('open')` in `showView()` when `window.innerWidth <= 768`

2. **Theme list/channel dropdown not updating after import**
   - Problem: Imported themes don't appear until page refresh
   - Fix: Added `renderSessions()` call after `loadThemes()` in import and create functions

3. **"Seamless" label unclear**
   - Problem: Users didn't understand what "Seamless" meant
   - Fix: Renamed to "Gapless" with tooltip "Loop without crossfade (for already-looped audio files)"

4. **Presence timing behavior confusing**
   - Problem: Users expected low presence to mean infrequent playback, but saw back-to-back plays
   - Fix: Added tooltips explaining the timing:
     - Playback mode tooltip: Explains Auto/Continuous/Sparse/Presence modes
     - Presence slider tooltip: "100% = ~3 min gaps, 50% = ~16 min gaps, 10% = ~27 min gaps (±30% random)"

---

### Standalone App: Playback Recovery After Update (v0.1.9-alpha)
**Commit:** `c034ed6`
**Files Modified:**
- `app/windows/src/launcher.py`
- `app/core/sonorium/main.py`

**Problem:** When an update was installed while music was playing, playback stopped and didn't resume after restart.

**Solution:** Implemented recovery state persistence:

1. **Launcher side** (`launcher.py`):
   - `get_recovery_path()` - Returns `config/recovery.json` path
   - `save_recovery_state(state)` - Saves theme/preset/volume to JSON
   - `clear_recovery_state()` - Removes recovery file
   - `get_current_playback_state()` - Queries `/api/status` for current state
   - Modified `install_update()` to save state before launching updater

2. **Core side** (`main.py`):
   - `check_recovery_state(config_dir)` - Validates recovery file
     - Checks `reason == 'update'`
     - Checks timestamp < 5 minutes old
   - `clear_recovery_state(config_dir)` - Removes file after recovery
   - Modified `run_server()` to check and restore playback on startup

**Recovery JSON format:**
```json
{
  "theme": "theme_id",
  "preset": "preset_id",
  "volume": 0.8,
  "timestamp": "2024-12-17T10:30:00",
  "reason": "update"
}
```

---

### Standalone App: Exclusive Track Timing Fix (v0.1.7-alpha)
**Files Modified:**
- `app/core/sonorium/recording.py`

**Problem:** Exclusive+sparse tracks were playing back-to-back instead of having natural intervals.

**Solution:** Implemented `ExclusionGroupCoordinator` and updated sparse playback:

1. **ExclusionGroupCoordinator class** (lines 16-157):
   ```python
   MIN_GAP_AFTER_EXCLUSIVE = 30.0  # seconds after track finishes
   INITIAL_DELAY = 60.0            # seconds before first exclusive plays
   ```
   - Thread-safe with `threading.Lock`
   - Tracks: `_playing_track`, `_play_end_time`, `_last_played_track`, `_cooldown_until`
   - Methods: `register_track()`, `try_start_playing()`, `finish_playing()`, `is_blocked()`, `get_wait_time()`

2. **Sparse playback constants** (lines 184-187):
   ```python
   SPARSE_MIN_INTERVAL = 180.0   # 3 min at 100% presence
   SPARSE_MAX_INTERVAL = 1800.0  # 30 min at ~0% presence
   SPARSE_INTERVAL_VARIANCE = 0.30  # ±30%
   ```

---

### Standalone App: Self-Update System (v0.1.6-alpha)
**Files Created:**
- `app/windows/src/updater.py`
- `app/windows/src/Updater.spec`
- `app/windows/src/version_info.py`

**Files Modified:**
- `app/windows/src/launcher.py`
- `.github/workflows/release.yml`

**Solution:** Separate `updater.exe` that force-closes Sonorium:

1. **updater.py**:
   - Uses `taskkill /F /IM Sonorium.exe` to force-close
   - Creates backup before replacement
   - Restores backup on failure
   - Launches updated app after success

2. **Workflow updates**:
   - Builds both `Sonorium.exe` and `updater.exe`
   - Includes both in release assets

---

## Architecture Notes

### Standalone vs Docker vs HA Addon

| Aspect | Standalone/Docker | HA Addon |
|--------|-------------------|----------|
| Entry point | `main.py` | `entrypoint.py` |
| Config | `config.py` (JSON file) | `settings.py` (env vars) |
| Logging | Standard Python logging | `fmtr.tools` logger |
| Dependencies | Plain pip | `fmtr.tools` setup |
| Speakers | `network_speakers.py` + `streaming.py` | `ha/registry.py` + `ha/media_controller.py` |
| Sessions | Single stream | Multi-session + channels |
| Web UI | `web_api.py` | `api.py` + `web/api_v2.py` |

### Shared Core Concepts
- Theme/preset loading from metadata.json
- Recording playback modes (continuous, sparse, presence, auto)
- Exclusive track coordination
- Audio mixing and streaming

---

## Common Gotchas

1. **Windows line endings** - Always use LF for shell scripts
2. **PyInstaller version resources** - Use hex values, not symbolic constants
3. **Embedded Python PYTHONPATH** - Use runpy + sys.path instead
4. **GitHub Releases API** - Use `/releases` not `/releases/latest` for prereleases
5. **Recovery timing** - 5-minute window prevents stale state
6. **AirPlay streaming** - Use stream_file() push model, not stream_url() pull
7. **Docker vs HA Addon** - Completely separate codebases, don't confuse them
