"""
Sonorium Channel System

Channels are persistent audio streams that speakers connect to.
Each channel can play one theme at a time, with smooth crossfading
when switching between themes.

This uses a broadcast model - ONE audio source, multiple listeners.
Like a radio station: all speakers hear the same stream at the same time.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, TYPE_CHECKING, Generator

import numpy as np

from sonorium.obs import logger
from sonorium.recording import SAMPLE_RATE, CROSSFADE_SAMPLES
from fmtr.tools import av

if TYPE_CHECKING:
    from sonorium.theme import ThemeDefinition, ThemeStream


# Crossfade duration for theme transitions (in seconds)
THEME_CROSSFADE_DURATION = 3.0
THEME_CROSSFADE_SAMPLES = int(THEME_CROSSFADE_DURATION * SAMPLE_RATE)

# Chunk size for silence generation
CHUNK_SIZE = 1024

# Default output gain
DEFAULT_OUTPUT_GAIN = 6.0

# Buffer size for broadcast (number of chunks to keep for late-joining clients)
BROADCAST_BUFFER_SIZE = 10


class ChannelState(str, Enum):
    """Current state of a channel."""
    IDLE = "idle"              # No theme assigned, outputting silence
    PLAYING = "playing"        # Playing a theme


@dataclass
class Channel:
    """
    A persistent audio stream channel using broadcast model.

    ONE audio generator runs continuously (when playing).
    ALL connected clients read from the same stream.
    New clients join at current playback position.
    """

    id: int
    name: str = ""

    # Current theme reference
    _current_theme: Optional[ThemeDefinition] = field(default=None, repr=False)

    # Theme version - increments when theme changes
    _theme_version: int = 0

    # State tracking
    state: ChannelState = ChannelState.IDLE

    # Active client count (for resource management)
    _client_count: int = 0

    # Lock for thread-safe operations
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    # Shared audio state
    _theme_stream: Optional[ThemeStream] = field(default=None, repr=False)
    _chunk_generator: Optional[Generator] = field(default=None, repr=False)

    # Broadcast buffer - recent chunks for all clients
    _broadcast_buffer: deque = field(default_factory=lambda: deque(maxlen=BROADCAST_BUFFER_SIZE), repr=False)
    _chunk_sequence: int = 0  # Incrementing ID for each chunk

    # Background generator thread
    _generator_thread: Optional[threading.Thread] = field(default=None, repr=False)
    _generator_running: bool = False

    # Pre-generated crossfade curves
    _fade_out: np.ndarray = field(default=None, repr=False)
    _fade_in: np.ndarray = field(default=None, repr=False)

    # Silence chunk
    _silence: np.ndarray = field(default=None, repr=False)

    def __post_init__(self):
        if not self.name:
            self.name = f"Channel {self.id}"
        # Initialize crossfade curves
        self._fade_out = np.cos(np.linspace(0, np.pi/2, THEME_CROSSFADE_SAMPLES)).astype(np.float32)
        self._fade_in = np.sin(np.linspace(0, np.pi/2, THEME_CROSSFADE_SAMPLES)).astype(np.float32)
        self._silence = np.zeros((1, CHUNK_SIZE), dtype=np.int16)

    @property
    def current_theme(self) -> Optional[ThemeDefinition]:
        """Get the current theme."""
        return self._current_theme

    @property
    def current_theme_id(self) -> Optional[str]:
        """Get the current theme ID."""
        return self._current_theme.id if self._current_theme else None

    @property
    def current_theme_name(self) -> Optional[str]:
        """Get the current theme name."""
        return self._current_theme.name if self._current_theme else None

    @property
    def theme_version(self) -> int:
        """Get current theme version (for change detection)."""
        return self._theme_version

    @property
    def is_active(self) -> bool:
        """Check if channel has connected clients."""
        return self._client_count > 0

    @property
    def stream_path(self) -> str:
        """Get the stream URL path for this channel."""
        return f"/stream/channel{self.id}"

    def set_theme(self, theme: ThemeDefinition) -> None:
        """
        Set or change the theme for this channel.
        Starts/restarts the shared audio generator.
        """
        with self._lock:
            if theme == self._current_theme:
                logger.info(f"Channel {self.id}: Theme '{theme.name}' already active, no change needed")
                return

            old_theme = self._current_theme.name if self._current_theme else "none"
            logger.info(f"Channel {self.id}: Changing theme from '{old_theme}' to '{theme.name}'")

            # Store old generator for crossfade
            old_generator = self._chunk_generator

            self._current_theme = theme
            self._theme_version += 1
            self.state = ChannelState.PLAYING

            # Create new shared stream
            self._theme_stream = theme.get_stream()
            new_generator = self._theme_stream.iter_chunks()

            # If we had an old generator, do crossfade
            if old_generator is not None:
                self._do_crossfade(old_generator, new_generator)

            self._chunk_generator = new_generator

            # Start generator thread if not running
            self._ensure_generator_running()

    def _do_crossfade(self, old_gen, new_gen):
        """Perform crossfade from old to new generator."""
        logger.info(f"Channel {self.id}: Performing crossfade")
        crossfade_position = 0

        while crossfade_position < THEME_CROSSFADE_SAMPLES:
            try:
                old_chunk = next(old_gen)
                new_chunk = next(new_gen)

                # Apply crossfade
                mixed = self._apply_crossfade(old_chunk, new_chunk, crossfade_position)
                crossfade_position += mixed.shape[1]

                # Add to broadcast buffer
                self._add_to_buffer(mixed)

            except StopIteration:
                break

        logger.info(f"Channel {self.id}: Crossfade complete")

    def _apply_crossfade(self, old_chunk: np.ndarray, new_chunk: np.ndarray, position: int) -> np.ndarray:
        """Apply crossfade mixing between two chunks."""
        chunk_size = old_chunk.shape[1]

        fade_start = position
        fade_end = min(fade_start + chunk_size, THEME_CROSSFADE_SAMPLES)
        fade_len = fade_end - fade_start

        if fade_len <= 0 or fade_start >= THEME_CROSSFADE_SAMPLES:
            return new_chunk

        old_f = old_chunk.astype(np.float32).flatten()
        new_f = new_chunk.astype(np.float32).flatten()

        if fade_len < chunk_size:
            fade_out = np.concatenate([
                self._fade_out[fade_start:fade_end],
                np.zeros(chunk_size - fade_len, dtype=np.float32)
            ])
            fade_in = np.concatenate([
                self._fade_in[fade_start:fade_end],
                np.ones(chunk_size - fade_len, dtype=np.float32)
            ])
        else:
            fade_out = self._fade_out[fade_start:fade_end]
            fade_in = self._fade_in[fade_start:fade_end]

        mixed = old_f[:len(fade_out)] * fade_out + new_f[:len(fade_in)] * fade_in
        mixed = np.clip(mixed, -32768, 32767).astype(np.int16)
        return mixed.reshape(1, -1)

    def _add_to_buffer(self, chunk: np.ndarray):
        """Add a chunk to the broadcast buffer."""
        self._chunk_sequence += 1
        self._broadcast_buffer.append((self._chunk_sequence, chunk))

    def _ensure_generator_running(self):
        """Start the generator thread if not running."""
        if self._generator_running:
            return

        self._generator_running = True
        self._generator_thread = threading.Thread(target=self._generator_loop, daemon=True)
        self._generator_thread.start()
        logger.info(f"Channel {self.id}: Started generator thread")

    def _generator_loop(self):
        """Background thread that generates audio chunks."""
        logger.info(f"Channel {self.id}: Generator loop started")

        start_time = time.time()
        audio_time = 0.0

        try:
            while self._generator_running and self.state == ChannelState.PLAYING:
                # Get next chunk from current generator
                if self._chunk_generator is None:
                    chunk = self._silence
                else:
                    try:
                        chunk = next(self._chunk_generator)
                    except StopIteration:
                        chunk = self._silence

                # Add to broadcast buffer
                self._add_to_buffer(chunk)

                # Maintain real-time pacing
                chunk_duration = chunk.shape[1] / SAMPLE_RATE
                audio_time += chunk_duration

                now = time.time()
                ahead = audio_time - (now - start_time)
                if ahead > 0:
                    time.sleep(ahead)

        except Exception as e:
            logger.error(f"Channel {self.id}: Generator error: {e}")
        finally:
            self._generator_running = False
            logger.info(f"Channel {self.id}: Generator loop stopped")

    def stop(self) -> None:
        """Stop the channel and return to idle."""
        with self._lock:
            logger.info(f"Channel {self.id}: Stopping playback")
            self._generator_running = False
            self._current_theme = None
            self._theme_stream = None
            self._chunk_generator = None
            self._theme_version += 1
            self.state = ChannelState.IDLE
            self._broadcast_buffer.clear()

    def client_connected(self) -> None:
        """Track a new client connection."""
        self._client_count += 1
        logger.info(f"Channel {self.id}: Client connected ({self._client_count} total)")

    def client_disconnected(self) -> None:
        """Track a client disconnection."""
        self._client_count = max(0, self._client_count - 1)
        logger.info(f"Channel {self.id}: Client disconnected ({self._client_count} remaining)")

    def get_current_sequence(self) -> int:
        """Get current chunk sequence number."""
        return self._chunk_sequence

    def get_chunks_since(self, since_sequence: int) -> list:
        """Get all chunks since a given sequence number."""
        return [(seq, chunk) for seq, chunk in self._broadcast_buffer if seq > since_sequence]

    def get_stream(self):
        """
        Get an MP3 stream iterator for this channel.

        All clients share the same audio source - they just
        encode from the broadcast buffer independently.
        """
        return ChannelStream(self)

    def to_dict(self) -> dict:
        """Serialize channel state for API."""
        return {
            "id": self.id,
            "name": self.name,
            "state": self.state.value,
            "current_theme": self.current_theme_id,
            "current_theme_name": self.current_theme_name,
            "client_count": self._client_count,
            "stream_path": self.stream_path,
        }


class ChannelStream:
    """
    MP3 streaming client for a Channel.

    Reads from the shared broadcast buffer and encodes to MP3.
    All clients hear the same audio at (approximately) the same time.
    """

    def __init__(self, channel: Channel):
        self.channel = channel
        self.channel.client_connected()

        # Start from current position
        self._last_sequence = channel.get_current_sequence()

        # Silence for gaps
        self._silence = np.zeros((1, CHUNK_SIZE), dtype=np.int16)

    def __iter__(self):
        output = av.open(file='.mp3', mode="w")
        bitrate = 128_000
        out_stream = output.add_stream(codec_name='mp3', rate=SAMPLE_RATE, bit_rate=bitrate)

        try:
            while True:
                # Get new chunks from broadcast buffer
                chunks = self.channel.get_chunks_since(self._last_sequence)

                if chunks:
                    for seq, chunk in chunks:
                        self._last_sequence = seq

                        # Encode to MP3
                        frame = av.AudioFrame.from_ndarray(chunk, format='s16', layout='mono')
                        frame.rate = SAMPLE_RATE

                        for packet in out_stream.encode(frame):
                            yield bytes(packet)
                else:
                    # No new chunks - wait a bit
                    # Output silence to keep stream alive
                    frame = av.AudioFrame.from_ndarray(self._silence, format='s16', layout='mono')
                    frame.rate = SAMPLE_RATE

                    for packet in out_stream.encode(frame):
                        yield bytes(packet)

                    time.sleep(0.01)  # Small sleep to avoid busy-waiting

        finally:
            logger.info(f'Channel {self.channel.id}: Client stream closed')
            self.channel.client_disconnected()
            output.close()


class ChannelManager:
    """
    Manages all channels for the Sonorium system.

    Provides channel creation, lookup, and lifecycle management.
    """

    def __init__(self, max_channels: int = 6):
        self.max_channels = max_channels
        self._channels: dict[int, Channel] = {}
        self._lock = threading.Lock()

        # Pre-create all channels
        for i in range(1, max_channels + 1):
            self._channels[i] = Channel(id=i)

        logger.info(f"ChannelManager initialized with {max_channels} channels")

    def get_channel(self, channel_id: int) -> Optional[Channel]:
        """Get a channel by ID."""
        return self._channels.get(channel_id)

    def get_all_channels(self) -> list[Channel]:
        """Get all channels."""
        return list(self._channels.values())

    def get_active_channels(self) -> list[Channel]:
        """Get channels that are currently playing."""
        return [c for c in self._channels.values() if c.state == ChannelState.PLAYING]

    def list_channels(self) -> list[dict]:
        """Get all channels as serialized dicts for API."""
        return [c.to_dict() for c in self._channels.values()]

    def get_active_count(self) -> int:
        """Get number of currently playing channels."""
        return len(self.get_active_channels())

    def get_available_channel(self) -> Optional[Channel]:
        """Get first available (idle) channel, or None if all busy."""
        for channel in self._channels.values():
            if channel.state == ChannelState.IDLE:
                return channel
        return None
