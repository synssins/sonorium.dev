import asyncio
import socket

from pydantic import Field, model_validator

from sonorium.client import ClientSonorium
from sonorium.device import Sonorium
from sonorium.paths import paths
from fmtr import tools
from fmtr.tools import sets, ha


def get_local_ip() -> str:
    """
    Get the local network IP address of this machine.

    This is the IP address that network speakers will use to connect
    to the Sonorium stream endpoint.
    """
    try:
        # Create a UDP socket and connect to an external address
        # This doesn't actually send data, but determines which interface would be used
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        # Connect to Google's DNS - doesn't actually send anything
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


class Settings(sets.Base):
    paths = paths

    ha_core_api: str = Field(default=ha.constants.URL_CORE_ADDON)
    ha_supervisor_api: str = Field(default=ha.constants.URL_SUPERVISOR_ADDON)

    token: str = Field(alias=ha.constants.SUPERVISOR_TOKEN_KEY)


    stream_url: str = "auto"

    # Default streaming port (matches config.yaml ports mapping)
    stream_port: int = 8008

    @model_validator(mode='after')
    def resolve_stream_url(self):
        """
        Auto-detect stream URL using the local IP address.

        Network speakers (Sonos, etc.) can't resolve hostnames like
        'homeassistant.local', so we need to use the actual IP address.

        Handles:
        - "auto" or empty: Auto-detect IP and build URL
        - "homeassistant.local" in URL: Replace with detected IP
        - Any other URL: Use as-is (allows manual override)
        """
        local_ip = get_local_ip()

        # Handle "auto" or empty - build URL from detected IP
        if not self.stream_url or self.stream_url.lower() == "auto":
            if local_ip:
                self.stream_url = f"http://{local_ip}:{self.stream_port}"
            else:
                # Fallback if IP detection fails
                self.stream_url = f"http://127.0.0.1:{self.stream_port}"
        # Handle homeassistant.local - replace with detected IP
        elif 'homeassistant.local' in self.stream_url:
            if local_ip:
                self.stream_url = self.stream_url.replace('homeassistant.local', local_ip)

        return self

    name: str = Sonorium.__name__
    mqtt: tools.mqtt.Client.Args | None = None

    path_audio: str = str(paths.audio)

    def run(self):
        super().run()
        asyncio.run(self.run_async())

    async def run_async(self):
        from fmtr.tools import debug
        debug.trace()
        from fmtr import tools
        from sonorium.obs import logger
        from sonorium.paths import paths
        from sonorium.version import __version__

        logger.info(f'Launching {paths.name_ns} {__version__=} {tools.get_version()=} from entrypoint.')
        logger.debug(f'{paths.settings.exists()=} {str(paths.settings)=}')
        logger.info(f'Stream URL: {self.stream_url}')

        logger.info(f'Launching...')

        client_ha = ha.core.Client(api_url=self.ha_core_api, token=self.token)
        device = Sonorium(name=self.name, client_ha=client_ha, path_audio_str=self.path_audio, sw_version=__version__, manufacturer=paths.org_singleton, model=Sonorium.__name__)

        if self.mqtt:
            client = ClientSonorium.from_args(self.mqtt, device=device)
        else:
            client = ClientSonorium.from_supervisor(device=device)

        await client.start()


ha.apply_addon_env()
settings = Settings()
settings
