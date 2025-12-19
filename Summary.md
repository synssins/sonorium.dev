# Sonorium Project Summary

> **Note:** This file is NOT committed to git. It provides a comprehensive overview
> of the project for context between development sessions.

---

## What is Sonorium?

Sonorium is a **multi-zone ambient soundscape mixer** that plays layered audio themes to create immersive ambient environments. Think of it like Tabletop Audio or Ambient Mixer, but self-hosted.

**Core Features:**
- Layer multiple audio tracks (rain, fire, wind, music) into a cohesive soundscape
- Stream to network speakers (DLNA, AirPlay, Chromecast, Sonos)
- Play through local audio devices
- Web-based control interface
- Theme presets with configurable track settings
- Exclusive tracks (only one plays at a time, like dialogue or thunder)
- Sparse playback (occasional sounds with presence-based intervals)

**Origin:** Fork of [Amniotic](https://github.com/fmtr/amniotic) by fmtr

---

## Three Deployment Targets

### 1. Windows Standalone Application
**Path:** `app/windows/` + `app/core/`
**Version:** v0.2.x-alpha (currently v0.2.30-alpha)

A desktop application with:
- PyQt6 GUI launcher with system tray
- Embedded Python 3.11 (no system Python needed)
- Self-update mechanism via GitHub releases
- Local audio output support
- Network speaker discovery and streaming

**Build:** GitHub Actions only (never local PyInstaller)
**Release:** Tag with `v0.x.x-alpha`, workflow creates release

### 2. Docker Container
**Path:** `app/docker/`
**Uses:** Same core as Windows (`app/core/sonorium/`)

A standalone containerized server for:
- NAS deployment (Synology, OMV, etc.)
- Linux servers
- Anywhere Docker runs

**Deploy:** `docker-compose up -d`
**Config:** Environment variables + mounted config volume

### 3. Home Assistant Add-on
**Path:** `sonorium_addon/`
**Version:** v2.x.x (STABLE)

**IMPORTANT: This is a SEPARATE codebase. DO NOT MODIFY.**

Integrated with Home Assistant for:
- Multi-session/multi-zone playback
- Channel-based persistent streaming
- Theme cycling automation
- HA media_player integration
- Floor/area/speaker hierarchy

---

## Folder Structure

```
G:\Projects\SonoriumDev\              # Main development directory
├── app/                              # Standalone applications
│   ├── core/                         # SHARED Python code (Windows + Docker)
│   │   ├── sonorium/                 # Main package
│   │   │   ├── __init__.py
│   │   │   ├── main.py               # FastAPI server entry point
│   │   │   ├── web_api.py            # REST API + embedded Web UI
│   │   │   ├── config.py             # JSON-based configuration
│   │   │   ├── theme.py              # Theme/preset definitions
│   │   │   ├── recording.py          # Audio decoding + playback modes
│   │   │   ├── streaming.py          # Network speaker streaming (DLNA, AirPlay)
│   │   │   ├── network_speakers.py   # Speaker discovery (mDNS, SSDP)
│   │   │   ├── audio_output.py       # Local audio device output
│   │   │   ├── app_device.py         # Device management
│   │   │   ├── local_stream_player.py
│   │   │   ├── update.py             # Version checking
│   │   │   ├── obs.py                # Logging wrapper
│   │   │   └── plugins/              # Plugin system (planned)
│   │   └── requirements.txt          # Python dependencies
│   │
│   ├── docker/                       # Docker deployment
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml
│   │   ├── entrypoint.sh
│   │   ├── requirements.txt          # Docker-specific deps
│   │   └── README.md
│   │
│   ├── windows/                      # Windows desktop app
│   │   └── src/
│   │       ├── launcher.py           # PyQt6 GUI launcher
│   │       ├── updater.py            # Self-update mechanism
│   │       ├── Sonorium.spec         # PyInstaller spec
│   │       ├── Updater.spec
│   │       ├── version.txt           # Windows version info
│   │       └── version_info.py       # Version generator
│   │
│   ├── themes/                       # Bundled themes
│   ├── config/                       # Runtime configuration
│   ├── logs/                         # Log files
│   ├── build/                        # PyInstaller build output
│   └── dist/                         # PyInstaller dist output
│
├── sonorium_addon/                   # HA Add-on (STABLE - DO NOT MODIFY)
│   ├── sonorium/                     # HA addon Python package
│   │   ├── api.py                    # Main FastAPI app
│   │   ├── entrypoint.py             # HA startup
│   │   ├── settings.py               # Environment config
│   │   ├── theme.py                  # Theme handling
│   │   ├── recording.py              # Audio playback
│   │   ├── obs.py                    # fmtr.tools logging
│   │   ├── core/                     # Session/channel management
│   │   │   ├── state.py
│   │   │   ├── session_manager.py
│   │   │   ├── channel.py
│   │   │   ├── group_manager.py
│   │   │   └── cycle_manager.py
│   │   ├── ha/                       # HA-specific modules
│   │   │   ├── registry.py
│   │   │   └── media_controller.py
│   │   └── web/                      # Web interface
│   │       ├── api_v2.py
│   │       └── templates/
│   ├── Dockerfile
│   ├── config.yaml                   # HA addon config
│   ├── run.sh                        # Supervisor startup
│   └── README.md
│
├── .github/
│   └── workflows/
│       └── release.yml               # GitHub Actions build workflow
│
├── CLAUDE.md                         # Claude Code guidance (in git)
├── TODO.md                           # Pending work (NOT in git)
├── Completed.md                      # Work history (NOT in git)
├── Summary.md                        # This file (NOT in git)
├── README.md                         # Public readme
├── ROADMAP.md                        # Feature roadmap
└── .gitignore
```

---

## Current State (December 2024)

### Windows App: v0.2.34-alpha
**Status:** AirPlay implementation in progress

**Working:**
- Theme playback with presets
- Local audio output (after sounddevice fix)
- DLNA speaker discovery and streaming
- AirPlay speaker discovery
- Self-update mechanism
- Web UI

**In Progress:**
- AirPlay streaming to audio speakers

**Current Task (2025-12-18):**
- Local changes discarded, synced to origin/dev (commit `ea3ac74`)
- Created comprehensive AirPlay reference docs in `docs/airplay/`
- Need to implement AirPlay streaming using pyatv
- **Constraint:** Must use pure Python (aiohttp), NO external tools like curl
- **Constraint:** Core code must be fully portable (no OS dependencies)

**Test Devices Available:**
- Office_C97a: 192.168.1.74 (primary, confirmed working)
- Arylic-livingroom: 192.168.1.254
- Marantz SR-5011: 192.168.1.13
- LG Soundbar: IP unknown (discoverable via mDNS)

### Docker Container
**Status:** Deployed for testing

**Location:** NAS at 192.168.1.150
**Port:** 8008

**Needs verification:**
- Network speaker discovery
- DLNA streaming
- Theme loading

### HA Add-on: v2.x.x
**Status:** STABLE - Do not modify

Working features:
- Multi-session playback
- Channel-based streaming
- Theme cycling
- HA integration
- Web UI

---

## Key Technical Details

### Audio Pipeline
```
Theme Folder → Recording (decode audio files)
    ↓
Theme (mix multiple recordings)
    ↓
ThemeStream (generate PCM chunks)
    ↓
MP3 Encoder (via PyAV/FFmpeg)
    ↓
HTTP Stream Endpoint
    ↓
Network Speaker OR Local Output
```

### Speaker Protocols

| Protocol | Library | Model |
|----------|---------|-------|
| DLNA | async-upnp-client | Pull (speaker fetches URL) |
| AirPlay | pyatv | Push (we stream to speaker) |
| Chromecast | pychromecast | Pull |
| Sonos | soco | Pull |
| Local | sounddevice | Direct output |

### Configuration
- **Standalone:** JSON file at `config/config.json`
- **Docker:** Environment variables
- **HA Addon:** HA options via `config.yaml`

### Dependencies

**Core (shared):**
- fastapi, uvicorn (web server)
- av (PyAV for FFmpeg)
- numpy (audio processing)
- aiohttp, httpx (HTTP client)
- async-upnp-client (DLNA)
- zeroconf (mDNS discovery)
- pyatv (AirPlay)
- sounddevice (local audio)

**Windows-specific:**
- PyQt6 (GUI)

**HA Addon-specific:**
- fmtr.tools (setup/logging)

---

## Development Guidelines

### Always:
1. Read TODO.md and Summary.md at session start
2. Use GitHub Actions for Windows builds
3. Keep HA addon stable (don't modify)
4. Test locally before pushing
5. Tag releases with `-alpha` suffix

### Never:
1. Build Windows releases locally
2. Confuse Docker container with HA addon
3. Modify HA addon without explicit request
4. Assume URLs or file paths

### Version Tags:
- Windows/Docker: `v0.x.x-alpha`
- HA Addon: `v2.x.x`

---

## External Resources

- **Repository:** https://github.com/synssins/sonorium
- **pyatv docs:** https://pyatv.dev/
- **async-upnp-client:** https://github.com/StevenLooman/async_upnp_client
- **Original Amniotic:** https://github.com/fmtr/amniotic

---

## Contact & Support

- **Owner:** synssins
- **GitHub Issues:** https://github.com/synssins/sonorium/issues
