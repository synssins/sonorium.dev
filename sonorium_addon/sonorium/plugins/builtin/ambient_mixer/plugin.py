"""
Ambient Mixer Importer Plugin for Sonorium

Imports soundscapes from ambient-mixer.com by:
1. Fetching the page HTML
2. Parsing audio sources and metadata
3. Downloading audio files
4. Creating a theme folder with proper attribution
"""

from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urljoin

from sonorium.plugins.base import BasePlugin
from sonorium.obs import logger


class AmbientMixerPlugin(BasePlugin):
    """
    Import soundscapes from Ambient-Mixer.com.

    This plugin allows users to paste an Ambient-Mixer URL and import
    all audio tracks as a new Sonorium theme with proper attribution.
    """

    id = "ambient_mixer"
    name = "Ambient Mixer Importer"
    version = "1.0.0"
    description = "Import soundscapes from Ambient-Mixer.com"
    author = "Sonorium"

    def get_ui_schema(self) -> dict:
        """Return the UI schema for the import form."""
        return {
            "type": "form",
            "fields": [
                {
                    "name": "url",
                    "type": "url",
                    "label": "Ambient Mixer URL",
                    "placeholder": "https://ambient-mixer.com/m/example",
                    "required": True,
                },
                {
                    "name": "theme_name",
                    "type": "string",
                    "label": "Theme Name (optional)",
                    "placeholder": "Leave empty to use page title",
                    "required": False,
                },
            ],
            "actions": [
                {
                    "id": "import",
                    "label": "Import Soundscape",
                    "primary": True,
                }
            ],
        }

    def get_settings_schema(self) -> dict:
        """Return the settings schema for persistent configuration."""
        return {
            "download_path": {
                "type": "string",
                "default": "/media/sonorium",
                "label": "Download Path",
            },
            "auto_create_metadata": {
                "type": "boolean",
                "default": True,
                "label": "Auto-create metadata.json",
            },
        }

    async def handle_action(self, action: str, data: dict) -> dict:
        """Handle the import action."""
        if action == "import":
            return await self._import_soundscape(data)
        return {"success": False, "message": f"Unknown action: {action}"}

    async def _import_soundscape(self, data: dict) -> dict:
        """
        Import a soundscape from Ambient-Mixer.

        Args:
            data: Form data with 'url' and optional 'theme_name'

        Returns:
            Result dict with success status and message
        """
        url = data.get("url", "").strip()
        custom_name = data.get("theme_name", "").strip()

        if not url:
            return {"success": False, "message": "URL is required"}

        # Validate URL
        parsed = urlparse(url)
        if "ambient-mixer" not in parsed.netloc.lower():
            return {
                "success": False,
                "message": "URL must be from ambient-mixer.com",
            }

        try:
            # Import dependencies
            try:
                import httpx
            except ImportError:
                return {
                    "success": False,
                    "message": "httpx library not available. Please install it.",
                }

            # Fetch the page
            logger.info(f"Fetching Ambient Mixer page: {url}")
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                html = response.text

            # Parse the page
            page_data = self._parse_ambient_mixer_page(html, url)

            if not page_data["tracks"]:
                return {
                    "success": False,
                    "message": "No audio tracks found on the page. The page format may have changed.",
                }

            # Use custom name or page title
            theme_name = custom_name or page_data["title"] or "Imported Soundscape"

            # Create theme folder
            download_path = Path(self.get_setting("download_path", "/media/sonorium"))
            theme_folder = download_path / self._sanitize_folder_name(theme_name)
            theme_folder.mkdir(parents=True, exist_ok=True)

            # Download tracks
            logger.info(f"Downloading {len(page_data['tracks'])} tracks to {theme_folder}")
            downloaded = 0
            track_metadata = {}

            async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
                for track in page_data["tracks"]:
                    track_url = track["url"]
                    track_name = track.get("name", f"track_{downloaded + 1}")

                    # Determine filename
                    filename = self._get_safe_filename(track_name, track_url)
                    filepath = theme_folder / filename

                    try:
                        logger.debug(f"Downloading: {track_url}")
                        resp = await client.get(track_url)
                        resp.raise_for_status()

                        filepath.write_bytes(resp.content)
                        downloaded += 1

                        # Store track metadata for attribution
                        track_metadata[filename] = {
                            "attribution": {
                                "original_name": track.get("name", ""),
                                "source_url": track_url,
                            }
                        }
                    except Exception as e:
                        logger.warning(f"Failed to download {track_url}: {e}")

            if downloaded == 0:
                return {
                    "success": False,
                    "message": "Failed to download any audio files.",
                }

            # Create metadata.json if enabled
            if self.get_setting("auto_create_metadata", True):
                metadata = {
                    "description": page_data.get("description", ""),
                    "icon": "mdi:music",
                    "attribution": {
                        "source": "Ambient-Mixer.com",
                        "source_url": url,
                        "imported_date": datetime.utcnow().isoformat() + "Z",
                        "imported_by": self.id,
                    },
                    "tracks": track_metadata,
                }

                metadata_path = theme_folder / "metadata.json"
                metadata_path.write_text(json.dumps(metadata, indent=2))
                logger.info(f"Created metadata.json for {theme_name}")

            return {
                "success": True,
                "message": f"Successfully imported '{theme_name}' with {downloaded} track(s). Refresh themes to see it.",
                "data": {
                    "theme_name": theme_name,
                    "folder": str(theme_folder),
                    "tracks_downloaded": downloaded,
                },
            }

        except httpx.HTTPError as e:
            logger.error(f"HTTP error importing soundscape: {e}")
            return {
                "success": False,
                "message": f"Failed to fetch page: {e}",
            }
        except Exception as e:
            logger.error(f"Error importing soundscape: {e}")
            return {
                "success": False,
                "message": f"Import failed: {e}",
            }

    def _parse_ambient_mixer_page(self, html: str, base_url: str) -> dict:
        """
        Parse an Ambient-Mixer page to extract audio sources.

        This is a simplified parser that looks for common patterns.
        The actual page structure may vary.

        Args:
            html: Page HTML content
            base_url: Base URL for resolving relative paths

        Returns:
            Dict with title, description, and tracks list
        """
        result = {
            "title": "",
            "description": "",
            "tracks": [],
        }

        # Try to extract title
        title_match = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
        if title_match:
            result["title"] = title_match.group(1).strip()
            # Clean up common suffixes
            result["title"] = re.sub(r'\s*[-|]\s*Ambient.*$', '', result["title"])
            result["title"] = result["title"].strip()

        # Try to find meta description
        desc_match = re.search(
            r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']',
            html,
            re.IGNORECASE,
        )
        if desc_match:
            result["description"] = desc_match.group(1).strip()

        # Look for audio sources - Ambient Mixer typically uses various patterns
        # Pattern 1: Direct audio URLs in data attributes or src
        audio_patterns = [
            # Direct MP3 links
            r'(?:src|href|data-src|data-audio|url)[=:]\s*["\']?(https?://[^"\'>\s]+\.mp3)["\']?',
            # Audio elements
            r'<audio[^>]*src=["\']([^"\']+)["\']',
            r'<source[^>]*src=["\']([^"\']+\.(?:mp3|ogg|wav))["\']',
            # JavaScript audio URLs
            r'["\']?(https?://[^"\'>\s]+/sounds?/[^"\'>\s]+\.mp3)["\']?',
        ]

        found_urls = set()
        for pattern in audio_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                url = match if isinstance(match, str) else match[0]
                if url and url not in found_urls:
                    # Make absolute if relative
                    if not url.startswith('http'):
                        url = urljoin(base_url, url)
                    found_urls.add(url)

        # Convert to track list
        for i, url in enumerate(found_urls, 1):
            # Try to extract a name from the URL
            path = urlparse(url).path
            name = Path(path).stem or f"Track {i}"
            name = name.replace('_', ' ').replace('-', ' ').title()

            result["tracks"].append({
                "url": url,
                "name": name,
            })

        return result

    def _sanitize_folder_name(self, name: str) -> str:
        """Create a safe folder name from a string."""
        # Remove or replace invalid characters
        safe = re.sub(r'[<>:"/\\|?*]', '', name)
        safe = safe.strip('. ')
        # Collapse multiple spaces
        safe = re.sub(r'\s+', ' ', safe)
        return safe or "Imported Theme"

    def _get_safe_filename(self, name: str, url: str) -> str:
        """Generate a safe filename for a track."""
        # Try to use the name
        if name:
            filename = re.sub(r'[<>:"/\\|?*]', '', name)
            filename = filename.strip('. ')[:50]  # Limit length
        else:
            # Fall back to URL filename
            path = urlparse(url).path
            filename = Path(path).stem or "track"

        # Ensure we have an extension
        url_ext = Path(urlparse(url).path).suffix.lower()
        if url_ext in ('.mp3', '.ogg', '.wav', '.flac'):
            ext = url_ext
        else:
            ext = '.mp3'

        return f"{filename}{ext}"
