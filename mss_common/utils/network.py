"""
Copyright (c) 2025 Monster Spawned Studios | https://monsterspawned.studio | All rights reserved.
"""

import socket

import requests
from redbot.core import commands
from redbot.core.bot import Red


class MSSUtilsNetwork(commands.Cog):
    """
    A common network utility library for Monster Spawned Studios cogs.
    """

    def __init__(self, bot: Red):
        self.bot = bot
        self.logger = getattr(self.bot, "log", None)

    async def get_local_ip_address(self) -> str:
        """
        Get the local IP address of the machine.

        Returns:
            str: The local IP address of the machine.
        """
        return socket.gethostbyname(socket.gethostname())

    async def get_ip_address_by_hostname(self, hostname: str = None) -> str:
        """
        Get the IP address of a hostname.

        Args:
            hostname (str, optional): The hostname to get the IP address of. Defaults to None.

        Returns:
            str: The IP address of the hostname.
        """
        return socket.gethostbyname(hostname)

    async def get_hostname_by_ip_address(self, ip_address: str = None) -> str:
        """
        Get the hostname of an IP address.

        Args:
            ip_address (str, optional): The IP address to get the hostname of. Defaults to None.

        Returns:
            str: The hostname of the IP address.
        """
        return socket.gethostbyaddr(ip_address)

    async def get_ip_address_by_hostname(self, hostname: str = None) -> str:
        """
        Get the IP address of a hostname.

        Args:
            hostname (str, optional): The hostname to get the IP address of. Defaults to None.

        Returns:
            str: The IP address of the hostname.
        """
        return socket.gethostbyname(hostname)

    async def get_open_ports(self) -> list:
        """
        Get the open ports of the machine.

        Returns:
            list: A list of open ports.
        """
        return socket.getaddrinfo(socket.gethostname(), 0, socket.AF_UNSPEC, socket.SOCK_STREAM, 0, socket.AI_PASSIVE)

    async def get_open_ports_by_ip_address(self, ip_address: str = None) -> list:
        """
        Get the open ports of an IP address.

        Args:
            ip_address (str, optional): The IP address to get the open ports of. Defaults to None.

        Returns:
            list: A list of open ports.
        """
        return socket.getaddrinfo(ip_address, 0, socket.AF_UNSPEC, socket.SOCK_STREAM, 0, socket.AI_PASSIVE)

    async def get_public_ip_address(self) -> str:
        """
        Get the public IP address of the machine (using the ipify API).

        Returns:
            str: The public IP address of the machine.
        """
        try:
            return requests.get("https://api.ipify.org?format=json").json()["ip"]
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error getting public IP address: {e}")
            return None

    async def get_public_ip_address_by_hostname(self, hostname: str = None) -> str:
        """
        Get the public IP address of a hostname (using the ipify API).

        Args:
            hostname (str, optional): The hostname to get the public IP address of. Defaults to None.

        Returns:
            str: The public IP address of the hostname.
        """
        try:
            return requests.get(f"https://api.ipify.org?format=json&hostname={hostname}").json()["ip"]
        except requests.exceptions.RequestException as e:
            self.logger.error(
                f"Error getting public IP address by hostname: {e}")
            return None

    async def get_system_dns_servers(self) -> list:
        """
        Get the system DNS servers.

        Returns:
            list: A list of system DNS servers.
        """
        try:
            # Get the system DNS servers
            dns_servers = socket.getaddrinfo(socket.gethostname(
            ), 0, socket.AF_UNSPEC, socket.SOCK_STREAM, 0, socket.AI_PASSIVE)
            return [server[4][0] for server in dns_servers]
        except socket.gaierror as e:
            self.logger.error(f"Error getting system DNS servers: {e}")
            return None

    async def get_system_name(self) -> str:
        """
        Get the system name.

        Returns:
            str: The system name.
        """
        return socket.gethostname()

    async def get_system_domain(self) -> str:
        """
        Get the system domain.

        Returns:
            str: The system domain.
        """
        return socket.getfqdn()

    async def get_system_fqdn(self) -> str:
        """
        Get the system FQDN.

        Returns:
            str: The system FQDN.
        """
        return socket.getfqdn()

    async def get_system_netmask(self) -> str:
        """
        Get the system netmask.

        Returns:
            str: The system netmask.
        """
        return socket.getnetbyname(socket.gethostname())
