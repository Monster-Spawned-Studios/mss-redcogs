"""
Copyright (c) 2025 Monster Spawned Studios | https://monsterspawned.studio | All rights reserved.

A Minecraft Bedrock RCON client.
"""

from logging import getLogger
from socket import SOCK_STREAM

from rcon.client import BaseClient
from rcon.exceptions import SessionTimeout, WrongPassword
from rcon.source.proto import Packet, Type


class MinecraftBedrockClient(BaseClient, socket_type=SOCK_STREAM):
    """
    A Minecraft Bedrock RCON client.
    """

    def __init__(self, host: str, port: int, password: str, timeout: float = 10.0, frag_threshold: int = 4096):
        """
        Initialize the Minecraft Bedrock client.

        Args:
            host (str): The host of the Minecraft Bedrock server.
            port (int): The port of the Minecraft Bedrock server.
            password (str): The password of the Minecraft Bedrock server.
            timeout (float, optional): The timeout for the Minecraft Bedrock server. Defaults to 10.0.
            frag_threshold (int, optional): The threshold for packet fragmentation. Defaults to 4096.
        """
        super().__init__(host=host, port=port, passwd=password,
                         timeout=timeout)
        self.password = password
        self.timeout = timeout
        self.host = host
        self.port = port
        self.frag_threshold = frag_threshold
        self.logger = getLogger(__name__)

    def communicate(
        self, packet: Packet, raise_unexpected_terminator: bool = False
    ) -> Packet:
        """Send and receive a packet."""
        self.send(packet)
        return self.read(raise_unexpected_terminator)

    def send(self, packet: Packet) -> None:
        """Send a packet to the server."""
        with self._socket.makefile("wb") as file:
            file.write(bytes(packet))

    def read(self, raise_unexpected_terminator: bool = False) -> Packet:
        """Read a packet from the server."""
        with self._socket.makefile("rb") as file:
            response = Packet.read(file, raise_unexpected_terminator)

            if len(response.payload) < self.frag_threshold:
                return response

            self.send(Packet.make_empty_response())

            while (successor := Packet.read(file)).id == response.id:
                response += successor

        return response

    def run(self, command: str, *args: str, encoding: str = "utf-8",
            enforce_id: bool = True, raise_unexpected_terminator: bool = False) -> str:
        """
        Run a command on the Minecraft Bedrock server.

        Args:
            command (str): The command to run.
            *args: Additional arguments for the command.
            encoding (str): Text encoding to use. Defaults to "utf-8".
            enforce_id (bool): Whether to enforce packet ID matching. Defaults to True.
            raise_unexpected_terminator (bool): Whether to raise on unexpected terminator. Defaults to False.

        Returns:
            str: The response from the server.
        """
        try:
            request = Packet.make_command(command, *args, encoding=encoding)
            response = self.communicate(request, raise_unexpected_terminator)

            if enforce_id and response.id != request.id:
                raise SessionTimeout("packet ID mismatch")

            return response.payload.decode(encoding)

        except SessionTimeout:
            self.logger.error(
                f"Session timed out while running command {command} on {self.host}:{self.port}")
            raise SessionTimeout(
                f"Session timed out while running command {command} on {self.host}:{self.port}")
        except WrongPassword:
            self.logger.error(
                f"Wrong password while running command {command} on {self.host}:{self.port}")
            raise WrongPassword(
                f"Wrong password while running command {command} on {self.host}:{self.port}")

    def login(self, passwd: str, *, encoding: str = "utf-8") -> bool:
        """
        Perform a login to the Minecraft Bedrock server.

        Args:
            passwd (str): The password to use for authentication.
            encoding (str): Text encoding to use. Defaults to "utf-8".

        Returns:
            bool: True if login was successful, False otherwise.
        """
        try:
            self.send(Packet.make_login(passwd, encoding=encoding))

            # Wait for SERVERDATA_AUTH_RESPONSE according to Source RCON Protocol
            while (response := self.read()).type != Type.SERVERDATA_AUTH_RESPONSE:
                pass

            if response.id == -1:
                raise WrongPassword(
                    f"Wrong password while logging in to {self.host}:{self.port}")

            return True

        except SessionTimeout:
            self.logger.error(
                f"Session timed out while logging in to {self.host}:{self.port}")
            raise SessionTimeout(
                f"Session timed out while logging in to {self.host}:{self.port}")
        except WrongPassword:
            self.logger.error(
                f"Wrong password while logging in to {self.host}:{self.port}")
            raise WrongPassword(
                f"Wrong password while logging in to {self.host}:{self.port}")

    def close(self) -> bool:
        """Close the Minecraft Bedrock server connection."""
        try:
            self._socket.close()
            return True
        except Exception as e:
            self.logger.error(
                f"Failed to close Minecraft Bedrock server connection.\nError: {e}")
            return False
