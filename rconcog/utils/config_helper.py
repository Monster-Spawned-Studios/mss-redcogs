"""
Copyright (c) 2025 Monster Spawned Studios | https://monsterspawned.studio | All rights reserved.

Helper functions for the RCON cog.
"""

import asyncio
from os import getenv

from redbot.core import Config, commands
from redbot.core.bot import Red


class ConfigHelper(commands.Cog):
    """
    Helper functions for the RCON cog.
    """

    def __init__(self, bot: Red):
        self.bot = bot
        self.COG_ID = int(getenv("RCON_COG_ID"))
        self.config: Config = Config.get_conf(
            self, identifier=self.COG_ID, force_registration=True)
        self.config.register_guild(servers={})
        self.bot.loop.create_task(self.update_server_list())

    async def update_server_list(self):
        """Update the server list every 15 minutes."""
        while True:
            await self.config.wait_until_guild_exists(self.config.id)
            servers = {g.id: g for g in self.bot.guilds}
            if not any([servers[server].owner_id == server_info["owner"] for server, server_info in self.config.all().items()]):
                pass
            await asyncio.sleep(900)
