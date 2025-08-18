"""
Copyright (c) 2025 Monster Spawned Studios | https://monsterspawned.studio | All rights reserved.

A cog to manage game servers using the RCON protocol and provide utilities for game servers.
"""

from __future__ import annotations

from typing import Literal, Optional

from rcon.battleye import Client as BattleyeClient
from rcon.exceptions import EmptyResponse, SessionTimeout, WrongPassword
from rcon.source import Client as SourceClient
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config

from rcon_cog import get_logger
from rcon_cog.utils.config_helper import ConfigHelper


class RCON_Cog(commands.Cog):
    """
    Manage RCON-powered game servers and execute commands via Discord.

    - Admin-only commands
    - Per-guild configuration (each guild has its own server list)
    """

    def __init__(self, bot: Red):
        self.bot = bot
        self.logger = get_logger("RCON Cog")
        # Pick a unique, stable identifier for this cog's Config bucket
        # Do not change once released, or it will orphan existing data
        self.config = ConfigHelper(self.bot)
        # Guild-scoped storage: mapping of server name -> config
        self.config.register_guild(servers={})

    # -------------
    # Helpers
    # -------------
    @staticmethod
    def _build_client(
        host: str,
        port: int,
        password: str,
        rcon_type: Literal["source", "battleye"],
    ) -> SourceClient | BattleyeClient:
        rtype = rcon_type.lower().strip()
        if rtype == "source":
            return SourceClient(host=host, port=port, passwd=password)
        if rtype == "battleye":
            return BattleyeClient(host=host, port=port, passwd=password)
        raise ValueError("Unsupported rcon_type. Use 'source' or 'battleye'.")

    @staticmethod
    def _default_port_for(rcon_type: Literal["source", "battleye"]) -> int:
        return 27015 if rcon_type == "source" else 27016

    # -------------
    # Command group
    # -------------
    @commands.hybrid_group(name="rcon", with_app_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def rcon_group(self, ctx: commands.Context) -> None:
        """
        Manage servers and run RCON commands. Admins only.
        """
        if ctx.interaction:
            await ctx.send("Use a subcommand to manage servers and run RCON commands (such as `rcon addserver`).")

    # Add or update a server configuration
    @rcon_group.command(name="addserver", with_app_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def rcon_addserver(
        self,
        ctx: commands.Context,
        name: str,
        host: str,
        rcon_type: Literal["source", "battleye"],
        password: str,
        port: Optional[int] = None,
    ) -> None:
        """
        Add or update an RCON server config for this guild.

        Required: name, host, rcon_type, password
        Optional: port (defaults by type)
        """
        assert ctx.guild is not None

        rtype = rcon_type.lower().strip()  # normalize for storage
        use_port = port if port is not None else self._default_port_for(
            rcon_type)  # type: ignore[arg-type]

        servers = await self.config.guild(ctx.guild).servers()
        servers[name] = {
            "host": host,
            "port": int(use_port),
            "password": password,
            "rcon_type": rtype,
        }
        await self.config.guild(ctx.guild).servers.set(servers)

        await ctx.send(
            f"Server '{name}' saved for this guild (type: {rtype}, host: {host}, port: {use_port})."
        )

    # Remove a server configuration
    @rcon_group.command(name="delserver", aliases=["rmserver", "removeserver", "delete", "remove"], with_app_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def rcon_delserver(self, ctx: commands.Context, name: str) -> None:
        """Delete a saved server by name for this guild."""
        assert ctx.guild is not None
        servers = await self.config.guild(ctx.guild).servers()
        if name not in servers:
            await ctx.send(f"No server named '{name}' found for this guild.")
            return
        servers.pop(name, None)
        await self.config.guild(ctx.guild).servers.set(servers)
        await ctx.send(f"Server '{name}' removed for this guild.")

    # List saved servers
    @rcon_group.command(name="listservers", aliases=["servers", "list"], with_app_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def rcon_listservers(self, ctx: commands.Context) -> None:
        """List all saved servers for this guild."""
        assert ctx.guild is not None
        servers = await self.config.guild(ctx.guild).servers()
        if not servers:
            await ctx.send("No servers configured for this guild.")
            return
        lines = []
        for name, data in servers.items():
            lines.append(
                f"- {name}: {data['rcon_type']} {data['host']}:{data['port']}")
        await ctx.send("Saved servers:\n" + "\n".join(lines))

    # Execute an RCON command
    @rcon_group.command(name="exec", aliases=["run", "cmd"], with_app_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def rcon_exec(
        self,
        ctx: commands.Context,
        server: str,
        *,
        command: str,
    ) -> None:
        """
        Execute an RCON command on a saved server.

        Example: rcon exec <server_name> status
        """
        assert ctx.guild is not None
        servers = await self.config.guild(ctx.guild).servers()
        if server not in servers:
            await ctx.send(f"No server named '{server}' found for this guild.")
            return

        cfg = servers[server]
        host: str = cfg["host"]
        port: int = int(cfg["port"])  # ensure int
        password: str = cfg["password"]
        rtype: str = cfg["rcon_type"]

        try:
            client = self._build_client(
                host=host, port=port, password=password, rcon_type=rtype)  # type: ignore[arg-type]
        except ValueError as e:
            await ctx.send(f"Configuration error for '{server}': {e}")
            return

        try:
            # Most rcon clients in this lib support context manager + run()
            # If this differs in your environment, adjust here accordingly.
            async def _execute() -> str:
                # The rcon clients are synchronous; run in a thread to avoid blocking
                import asyncio

                def _run_blocking() -> str:
                    with client as c:  # type: ignore[union-attr]
                        return str(c.run(command))  # type: ignore[union-attr]

                return await asyncio.to_thread(_run_blocking)

            response = await _execute()
            if not response:
                await ctx.send("(No response)")
                return
            # Truncate very long responses to keep Discord happy
            if len(response) > 1900:
                response = response[:1900] + "\n… (truncated)"
            message = f"Response:\n```{response}```"
            await ctx.send(message)
        except WrongPassword:
            await ctx.send("Authentication failed: wrong password.")
        except SessionTimeout:
            await ctx.send("Connection timed out. Is the server reachable?")
        except EmptyResponse:
            await ctx.send("The server returned an empty response.")
        except Exception as e:  # pragma: no cover - safety net
            self.logger.log(
                "Unexpected error while executing RCON command", e, level="ERROR")
            await ctx.send(f"Unexpected error: {type(e).__name__}: {e}")
