"""
Copyright (c) 2025 Monster Spawned Studios | https://monsterspawned.studio | All rights reserved.

A Seven Days to Die RCON client.
"""


from logging import getLogger

from rcon.source.client import BaseClient, SessionTimeout, WrongPassword
from rcon.source.proto import Packet


class SevenDaysToDieClient(BaseClient):
    """
    A Seven Days to Die RCON client.
    """

    def __init__(self, host: str, port: int, password: str, timeout: float = 10.0, frag_threshold: int = 4096):
        super().__init__(host=host, port=port, passwd=password, timeout=timeout)
        self.password = password
        self.timeout = timeout
        self.host = host
        self.port = port
        self.frag_threshold = frag_threshold
        self.logger = getLogger(__name__)

    def communicate(self, packet: Packet, raise_unexpected_terminator: bool = False) -> Packet:
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
        """Run a command on the Seven Days to Die server."""
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
        """Perform a login to the Seven Days to Die server."""
        try:
            self.send(Packet.make_login(passwd, encoding=encoding))
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
        """Close the Seven Days to Die server connection."""
        try:
            self._socket.close()
            return True
        except Exception as e:
            self.logger.error(
                f"Failed to close Seven Days to Die server connection.\nError: {e}")
            return False
