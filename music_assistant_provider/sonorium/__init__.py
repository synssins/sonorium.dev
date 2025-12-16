"""Sonorium Music Provider for Music Assistant.

Streams ambient soundscapes from a Sonorium installation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from music_assistant_models.config_entries import ConfigEntry
from music_assistant_models.enums import (
    ConfigEntryType,
    ContentType,
    ImageType,
    MediaType,
    ProviderFeature,
    StreamType,
)
from music_assistant_models.errors import MediaNotFoundError
from music_assistant_models.media_items import (
    AudioFormat,
    BrowseFolder,
    MediaItemImage,
    MediaItemType,
    ProviderMapping,
    Radio,
    SearchResults,
    UniqueList,
)
from music_assistant_models.streamdetails import StreamDetails

from music_assistant.models.music_provider import MusicProvider

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Sequence

    from music_assistant_models.config_entries import ProviderConfig
    from music_assistant_models.provider import ProviderManifest

    from music_assistant import MusicAssistant
    from music_assistant.models import ProviderInstanceType


# Constants for browse paths
BROWSE_FAVORITES = "favorites"
BROWSE_CATEGORIES = "categories"
BROWSE_ALL = "all"


async def setup(
    mass: MusicAssistant,
    manifest: ProviderManifest,
    config: ProviderConfig,
) -> ProviderInstanceType:
    """Initialize provider(instance) with given configuration."""
    return SonoriumProvider(mass, manifest, config)


async def get_config_entries(
    mass: MusicAssistant,
    instance_id: str | None = None,
    action: str | None = None,
    values: dict[str, ConfigEntry] | None = None,
) -> tuple[ConfigEntry, ...]:
    """Return Config entries to setup this provider."""
    return (
        ConfigEntry(
            key="url",
            type=ConfigEntryType.STRING,
            label="Sonorium URL",
            default_value="http://homeassistant.local:8008",
            description="Base URL of your Sonorium installation (e.g., http://192.168.1.100:8008)",
            required=True,
        ),
    )


class SonoriumProvider(MusicProvider):
    """Music Provider for Sonorium ambient soundscapes."""

    _themes: list[dict] | None = None

    @property
    def supported_features(self) -> set[ProviderFeature]:
        """Return supported features."""
        return {
            ProviderFeature.BROWSE,
            ProviderFeature.SEARCH,
            ProviderFeature.LIBRARY_RADIOS,
            ProviderFeature.LIBRARY_RADIOS_EDIT,
        }

    @property
    def is_streaming_provider(self) -> bool:
        """Return True if this is a streaming provider."""
        return True

    @property
    def base_url(self) -> str:
        """Return the configured Sonorium base URL."""
        url = self.config.get_value("url")
        return url.rstrip("/") if url else "http://homeassistant.local:8008"

    async def handle_async_init(self) -> None:
        """Handle async initialization."""
        # Test connection to Sonorium
        await self._get_themes(force_refresh=True)

    async def _get_themes(self, force_refresh: bool = False) -> list[dict]:
        """Fetch themes from Sonorium API."""
        if self._themes is not None and not force_refresh:
            return self._themes

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.base_url}/api/themes")
            response.raise_for_status()
            self._themes = response.json()

        return self._themes

    def _parse_radio(self, theme: dict) -> Radio:
        """Parse a Sonorium theme into a Radio object."""
        theme_id = theme.get("id", "")
        name = theme.get("name", "Unknown Theme")
        description = theme.get("description", "")
        icon = theme.get("icon", "")
        categories = theme.get("categories", [])
        is_favorite = theme.get("is_favorite", False)
        track_count = theme.get("total_tracks", 0)

        # Build metadata string
        metadata_parts = []
        if track_count:
            metadata_parts.append(f"{track_count} tracks")
        if categories:
            metadata_parts.append(", ".join(categories))
        metadata = " • ".join(metadata_parts) if metadata_parts else None

        radio = Radio(
            item_id=theme_id,
            provider=self.domain,
            name=f"{icon} {name}".strip() if icon else name,
            provider_mappings={
                ProviderMapping(
                    item_id=theme_id,
                    provider_domain=self.domain,
                    provider_instance=self.instance_id,
                )
            },
        )

        # Add description as metadata
        if description:
            radio.metadata.description = description

        # Mark as favorite if applicable
        radio.favorite = is_favorite

        return radio

    async def get_library_radios(self) -> AsyncGenerator[Radio, None]:
        """Get favorite/library radio stations."""
        themes = await self._get_themes()
        for theme in themes:
            if theme.get("is_favorite", False):
                yield self._parse_radio(theme)

    async def library_add(self, item: MediaItemType) -> bool:
        """Add item to library (favorite in Sonorium)."""
        if item.media_type != MediaType.RADIO:
            return False

        theme_id = item.item_id
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{self.base_url}/api/themes/{theme_id}/favorite")
            if response.status_code == 200:
                # Refresh theme cache
                await self._get_themes(force_refresh=True)
                return True
        return False

    async def library_remove(self, item: MediaItemType) -> bool:
        """Remove item from library (unfavorite in Sonorium)."""
        # Sonorium's favorite endpoint toggles, so same as add
        return await self.library_add(item)

    async def get_radio(self, prov_radio_id: str) -> Radio:
        """Get radio station details."""
        themes = await self._get_themes()
        for theme in themes:
            if theme.get("id") == prov_radio_id:
                return self._parse_radio(theme)
        raise MediaNotFoundError(f"Theme {prov_radio_id} not found")

    async def get_stream_details(
        self,
        item_id: str,
        media_type: MediaType = MediaType.RADIO,
    ) -> StreamDetails:
        """Get stream details for a theme."""
        # Verify the theme exists
        themes = await self._get_themes()
        theme = None
        for t in themes:
            if t.get("id") == item_id:
                theme = t
                break

        if not theme:
            raise MediaNotFoundError(f"Theme {item_id} not found")

        # Return stream details pointing to Sonorium's stream endpoint
        stream_url = f"{self.base_url}/stream/{item_id}"

        return StreamDetails(
            provider=self.domain,
            item_id=item_id,
            audio_format=AudioFormat(
                content_type=ContentType.MP3,
            ),
            media_type=MediaType.RADIO,
            stream_type=StreamType.HTTP,
            path=stream_url,
            can_seek=False,
        )

    async def search(
        self,
        search_query: str,
        media_types: list[MediaType],
        limit: int = 20,
    ) -> SearchResults:
        """Search for themes."""
        result = SearchResults()

        if MediaType.RADIO not in media_types:
            return result

        search_lower = search_query.lower()
        themes = await self._get_themes()

        for theme in themes:
            name = theme.get("name", "").lower()
            description = theme.get("description", "").lower()
            categories = [c.lower() for c in theme.get("categories", [])]

            # Match against name, description, or categories
            if (
                search_lower in name
                or search_lower in description
                or any(search_lower in cat for cat in categories)
            ):
                result.radio.append(self._parse_radio(theme))
                if len(result.radio) >= limit:
                    break

        return result

    async def browse(self, path: str) -> Sequence[MediaItemType | BrowseFolder]:
        """Browse Sonorium themes."""
        themes = await self._get_themes()

        # Root level - show browse options
        if not path or path == "":
            return [
                BrowseFolder(
                    item_id=BROWSE_FAVORITES,
                    provider=self.domain,
                    path=BROWSE_FAVORITES,
                    name="⭐ Favorites",
                    provider_mappings={
                        ProviderMapping(
                            item_id=BROWSE_FAVORITES,
                            provider_domain=self.domain,
                            provider_instance=self.instance_id,
                        )
                    },
                ),
                BrowseFolder(
                    item_id=BROWSE_CATEGORIES,
                    provider=self.domain,
                    path=BROWSE_CATEGORIES,
                    name="📁 Categories",
                    provider_mappings={
                        ProviderMapping(
                            item_id=BROWSE_CATEGORIES,
                            provider_domain=self.domain,
                            provider_instance=self.instance_id,
                        )
                    },
                ),
                BrowseFolder(
                    item_id=BROWSE_ALL,
                    provider=self.domain,
                    path=BROWSE_ALL,
                    name="🎵 All Themes",
                    provider_mappings={
                        ProviderMapping(
                            item_id=BROWSE_ALL,
                            provider_domain=self.domain,
                            provider_instance=self.instance_id,
                        )
                    },
                ),
            ]

        # Favorites
        if path == BROWSE_FAVORITES:
            return [
                self._parse_radio(theme)
                for theme in themes
                if theme.get("is_favorite", False)
            ]

        # All themes
        if path == BROWSE_ALL:
            return [self._parse_radio(theme) for theme in themes]

        # Categories listing
        if path == BROWSE_CATEGORIES:
            # Collect all unique categories
            categories: set[str] = set()
            for theme in themes:
                for cat in theme.get("categories", []):
                    categories.add(cat)

            return [
                BrowseFolder(
                    item_id=f"category_{cat}",
                    provider=self.domain,
                    path=f"{BROWSE_CATEGORIES}/{cat}",
                    name=cat,
                    provider_mappings={
                        ProviderMapping(
                            item_id=f"category_{cat}",
                            provider_domain=self.domain,
                            provider_instance=self.instance_id,
                        )
                    },
                )
                for cat in sorted(categories)
            ]

        # Specific category
        if path.startswith(f"{BROWSE_CATEGORIES}/"):
            category = path.split("/", 1)[1]
            return [
                self._parse_radio(theme)
                for theme in themes
                if category in theme.get("categories", [])
            ]

        return []
