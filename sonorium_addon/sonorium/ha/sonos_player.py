"""
Direct Sonos Control via SoCo

Uses SoCo library for reliable Sonos streaming playback.
Key advantage: force_radio=True treats streams as radio stations,
which works reliably for continuous audio streams.

Pause/stop/volume still go through HA's media_player service.
"""

from __future__ import annotations

import asyncio
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from sonorium.obs import logger

# SoCo is a blocking library, so we run it in a thread pool
_executor = ThreadPoolExecutor(max_workers=4)


def _is_sonos_entity(entity_id: str) -> bool:
    """Check if an entity is likely a Sonos speaker."""
    # Sonos entities typically have 'sonos' in the name
    return 'sonos' in entity_id.lower()


def _get_sonos_ip_from_attributes(attributes: dict) -> Optional[str]:
    """Extract IP address from HA entity attributes."""
    # HA Sonos integration stores IP in various attributes
    # Try common attribute names
    for attr in ['ip_address', 'soco_ip', 'host', 'address']:
        if attr in attributes:
            return attributes[attr]

    # Some integrations store it nested
    if 'device_info' in attributes:
        device_info = attributes['device_info']
        if isinstance(device_info, dict):
            for attr in ['ip_address', 'host', 'address']:
                if attr in device_info:
                    return device_info[attr]

    return None


def _play_uri_sync(ip: str, uri: str) -> bool:
    """
    Play URI on Sonos speaker (blocking, runs in thread).

    Uses force_radio=True to treat streams as radio stations.
    """
    try:
        import soco
        device = soco.SoCo(ip)

        # force_radio=True is key - makes Sonos treat this as a radio stream
        # rather than a finite file, which works better for continuous streams
        device.play_uri(uri, force_radio=True)

        logger.info(f"  SoCo: Started playback on {ip}")
        return True
    except Exception as e:
        logger.error(f"  SoCo: Failed to play on {ip}: {e}")
        return False


async def play_uri_on_sonos(ip: str, uri: str) -> bool:
    """
    Play URI on Sonos speaker (async wrapper).

    Args:
        ip: Sonos speaker IP address
        uri: Stream URL to play

    Returns:
        True if playback started successfully
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _play_uri_sync, ip, uri)


class SonosPlayer:
    """
    Direct Sonos player using SoCo.

    Uses HA's API to get speaker IPs, then controls Sonos directly.
    """

    def __init__(self, media_controller):
        """
        Initialize with reference to media controller for HA API access.

        Args:
            media_controller: HAMediaController instance for getting entity states
        """
        self.media_controller = media_controller
        # Cache of entity_id -> IP mappings
        self._ip_cache: dict[str, str] = {}

    async def get_sonos_ip(self, entity_id: str) -> Optional[str]:
        """
        Get IP address for a Sonos entity.

        First checks cache, then queries HA for entity attributes.
        """
        # Check cache first
        if entity_id in self._ip_cache:
            return self._ip_cache[entity_id]

        # Query HA for entity state/attributes
        state = await self.media_controller.get_state(entity_id)
        if not state:
            logger.warning(f"  SoCo: Could not get state for {entity_id}")
            return None

        attributes = state.get('attributes', {})
        ip = _get_sonos_ip_from_attributes(attributes)

        if ip:
            self._ip_cache[entity_id] = ip
            logger.info(f"  SoCo: Found IP {ip} for {entity_id}")
        else:
            logger.warning(f"  SoCo: No IP found in attributes for {entity_id}")
            logger.debug(f"  SoCo: Available attributes: {list(attributes.keys())}")

        return ip

    def is_sonos(self, entity_id: str) -> bool:
        """Check if entity is a Sonos speaker."""
        return _is_sonos_entity(entity_id)

    async def play_media(self, entity_id: str, media_url: str) -> bool:
        """
        Play media URL on a Sonos speaker using SoCo.

        Args:
            entity_id: HA entity ID (e.g., media_player.sonos_office)
            media_url: Stream URL to play

        Returns:
            True if playback started successfully
        """
        if not self.is_sonos(entity_id):
            logger.warning(f"  SoCo: {entity_id} is not a Sonos speaker")
            return False

        ip = await self.get_sonos_ip(entity_id)
        if not ip:
            logger.error(f"  SoCo: Cannot play - no IP for {entity_id}")
            return False

        logger.info(f"  SoCo: Playing {media_url} on {entity_id} ({ip})")
        return await play_uri_on_sonos(ip, media_url)

    async def play_media_multi(
        self,
        entity_ids: list[str],
        media_url: str,
    ) -> dict[str, bool]:
        """
        Play media on multiple Sonos speakers.

        Args:
            entity_ids: List of HA entity IDs
            media_url: Stream URL to play

        Returns:
            Dict mapping entity_id to success status
        """
        if not entity_ids:
            return {}

        # Filter to only Sonos speakers
        sonos_ids = [eid for eid in entity_ids if self.is_sonos(eid)]
        non_sonos_ids = [eid for eid in entity_ids if not self.is_sonos(eid)]

        if non_sonos_ids:
            logger.debug(f"  SoCo: Skipping non-Sonos speakers: {non_sonos_ids}")

        if not sonos_ids:
            return {}

        # Play on all Sonos speakers concurrently
        tasks = [self.play_media(eid, media_url) for eid in sonos_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        status = {}
        for entity_id, result in zip(sonos_ids, results):
            if isinstance(result, Exception):
                logger.error(f"  SoCo: Exception for {entity_id}: {result}")
                status[entity_id] = False
            else:
                status[entity_id] = result

        success_count = sum(1 for v in status.values() if v)
        logger.info(f"  SoCo: Started playback on {success_count}/{len(sonos_ids)} Sonos speakers")

        return status

    def clear_ip_cache(self):
        """Clear the IP cache (useful if speaker IPs change)."""
        self._ip_cache.clear()
