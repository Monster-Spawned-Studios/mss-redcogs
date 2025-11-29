"""
Copyright (c) 2025 Monster Spawned Studios | https://monsterspawned.studio | All rights reserved.

A cog to manage game servers using the RCON protocol and provide utilities for game servers.
"""

from enum import Enum

from rcon.battleye import Client as BattleyeClient
from rcon.client import BaseClient
from rcon.source import Client as SourceClient


class ServerType(Enum):
    """
    A enum to represent the type of server.
    """

    default_ports = {
        "source": 27015,
        "battleye": 27016,
        "quake3": 27960,
        "minecraft_bedrock": 19132,
        "minecraft_java": 25565,
        "team_fortress_2": 27015,
        "counter_strike_2": 27015,
        "black_mesa": 27015,
        "garrysmod": 27015,
        "rust": 28015,
        "ark": 7777,
        "ark_survival_evolved": 7777,
        "ark_survival_ascended": 7777,
        "palworld": 8211,
        "valheim": 2456,
        "pavlov": 7777,
        "terraria": 7777,
    }

    def __init__(
        self,
        name: str,
        client: BaseClient,
        rcon_type: str,
        host: str,
        password: str,
        port: int | None = None,
    ):
        """
        Initialize the server type.
        """
        self.name = name
        self.client = client
        self.rcon_type = rcon_type
        self.host = host
        self.password = password
        self.port = port

        if rcon_type.lower().strip() == "source":
            self.client = SourceClient(host=host, port=port, passwd=password)
        elif rcon_type.lower().strip() == "battleye":
            self.client = BattleyeClient(host=host, port=port, passwd=password)
        else:
            raise ValueError(
                f"Invalid RCON type: '{rcon_type}'! Must be 'source' or 'battleye'.")

        try:
            self.port = self.default_ports[name]
        except KeyError:
            self.port = port

    def get_client_name(self) -> str:
        """
        Get the name of the client.
        """
        return self.name

    def get_default_port(self) -> int:
        """
        Get the default port of the server.
        """
        return self.default_port

    def get_client(self) -> BaseClient:
        """
        Get the client of the server.
        """
        return self.client

    def get_rcon_type(self) -> str:
        """
        Get the RCON type of the server.
        """
        return self.rcon_type
