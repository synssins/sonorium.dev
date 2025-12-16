# Sonorium Provider for Music Assistant

Stream ambient soundscapes from your Sonorium installation directly in Music Assistant.

## Features

- Browse themes by category or favorites
- Search themes by name, description, or category
- Play ambient soundscapes to any Music Assistant player
- Favorite themes sync with Sonorium

## Installation

### Option 1: Custom Provider (Local Testing)

1. Copy the `sonorium` folder to your Music Assistant custom providers directory:
   ```
   /config/custom_components/music_assistant/providers/sonorium/
   ```

   Or if using Docker:
   ```
   /data/providers/sonorium/
   ```

2. Restart Music Assistant

3. Go to **Settings** → **Providers** → **Add Provider**

4. Select "Sonorium" and configure the URL to your Sonorium installation

### Option 2: Submit to Music Assistant (Future)

Once tested, this provider can be submitted as a PR to the [music-assistant/server](https://github.com/music-assistant/server) repository.

## Configuration

| Setting | Description | Default |
|---------|-------------|---------|
| `url` | Base URL of your Sonorium installation | `http://homeassistant.local:8008` |

**Important:** Use an IP address instead of `homeassistant.local` if your players can't resolve mDNS hostnames.

## Usage

After adding the provider:

1. **Browse** - Navigate Sonorium themes by:
   - ⭐ Favorites - Your starred themes
   - 📁 Categories - Themes organized by category
   - 🎵 All Themes - Complete theme list

2. **Search** - Find themes by name, description, or category

3. **Play** - Select any theme to stream to your connected players

4. **Favorite** - Add themes to your library (syncs with Sonorium)

## Requirements

- Sonorium v1.2.0 or later
- Music Assistant 2.0 or later
- Network connectivity between Music Assistant and Sonorium

## How It Works

Sonorium themes appear as "radio stations" in Music Assistant. When you play a theme:

1. Music Assistant requests stream details from this provider
2. The provider returns Sonorium's HTTP stream URL
3. Music Assistant sends the stream to your selected player
4. Sonorium handles the ambient audio mixing

The actual audio processing happens in Sonorium—Music Assistant just routes the stream to players.

## Troubleshooting

### Provider not connecting
- Verify the Sonorium URL is correct and accessible
- Check that Sonorium is running
- Try using an IP address instead of hostname

### No audio playing
- Ensure the stream URL uses an IP address your players can reach
- Check Sonorium logs for streaming errors
- Verify the player supports HTTP audio streams

### Themes not showing
- Click refresh in Music Assistant
- Check Sonorium has themes loaded
- Verify API access: `curl http://YOUR_SONORIUM_URL/api/themes`
