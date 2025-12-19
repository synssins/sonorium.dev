# CLAUDE.md
This file provides guidance to Claude Code when working with code in this repository.

---

## GIT WORKFLOW - ABSOLUTELY CRITICAL

### Remote Configuration
- `origin` → Local Gitea (http://192.168.1.222:3000/Synthesis/sonorium) - SAFE SANDBOX
- `github` → Production GitHub (https://github.com/synssins/sonorium) - NEVER PUSH HERE

### Rules
1. **ONLY push to `origin`** (local Gitea)
2. **NEVER push to `github` remote** - this is production and requires manual review
3. **NEVER force push** to any remote
4. **Always create feature branches** - never commit directly to main
5. Branch naming: `feature/<description>` or `fix/<description>`

### Before Any Push
1. Run tests if available
2. Commit with descriptive messages
3. Push to origin only: `git push origin <branch>`

### Reference Files (G:\projects\sonoriumdev)
These files contain project context and should be read at session start:
- Summary.md - Project overview and current state
- TODO.md - Pending work items
- Completed.md - Implementation history
- ROADMAP.md - Feature roadmap
- docs/airplay/*.md - AirPlay protocol documentation

**These files are for reference only - they should NEVER be committed to GitHub.**
SEPARATOR
## STARTUP: Read These Files First
When a new session starts or user says Read claude.md, read these files in order:
1. CLAUDE.md - This file
2. Summary.md - Project overview and current work state
3. TODO.md - Pending work
4. Completed.md - Implementation history
SEPARATOR
## CRITICAL RULES
SEPARATOR
### 1. Platform Agnostic Core Code
All code in app/core/ MUST work on ALL platforms: Windows, Linux, Docker, macOS.
NO platform-specific dependencies in core code. Platform code goes in launchers only.
### 2. Fully Portable
All app versions must be 100% portable. Bundle all dependencies. Never rely on system software.
### 3. Keep Summary.md Updated
Update Summary.md after EACH significant step so we can resume exactly where we left off.
Document current work. Do not remove Current Task section until complete.
### 4. No Claude Attribution
NEVER include Claude attribution in commits. No AI attribution of any kind.
### 5. Pure Python for Portability
Use aiohttp for HTTP requests, NOT curl subprocess. All deps must be pip-installable.
### 6. Branching Rules
NEVER commit to origin main without explicit user permission.
All development work goes to origin dev.
### 7. HA Addon is STABLE
DO NOT modify sonorium_addon/ unless explicitly requested. It has a separate codebase.
SEPARATOR
## Project Overview
Sonorium is a multi-zone ambient soundscape mixer with three deployment targets:
1. Windows Standalone App - PyQt6 GUI with embedded Python
2. Docker Container - Standalone server for NAS/Linux
3. Home Assistant Add-on - HA-integrated version (STABLE)
Repository: github.com/synssins/sonorium | Owner: synssins
SEPARATOR
## Key Files
API endpoints: app/core/sonorium/web_api.py
Speaker discovery: app/core/sonorium/network_speakers.py
Speaker streaming: app/core/sonorium/streaming.py
Audio playback: app/core/sonorium/recording.py
Windows launcher: app/windows/src/launcher.py
SEPARATOR
## Speaker Protocol Support
DLNA: Working (SSDP discovery, HTTP pull)
AirPlay: In progress (mDNS discovery, RAOP push via pyatv)
Chromecast: Planned
Sonos: Planned
Local audio: Working (sounddevice)
SEPARATOR
## Common Gotchas
1. Windows line endings - Scripts must use LF not CRLF
2. Embedded Python - Use runpy + sys.path instead of PYTHONPATH
3. Docker vs HA Addon - Completely separate codebases
4. AirPlay streaming - Use stream_file() push model not stream_url()
5. GitHub releases - Always use tags, never local builds
6. Pure Python for AirPlay - Use aiohttp NOT curl subprocess
