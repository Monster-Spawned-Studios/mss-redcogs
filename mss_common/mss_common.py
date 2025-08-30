"""
Copyright (c) 2025 Monster Spawned Studios | https://monsterspawned.studio | All rights reserved.

A common library for Monster Spawned Studios cogs.
"""

from __init__ import __author__, __version__
from redbot.core import commands
from redbot.core.bot import Red


class MSSCommon(commands.Cog):
    """
    A common library for Monster Spawned Studios cogs.
    """

    def __init__(self, bot: Red, max_queue_size: int = 10, cooldown: int = 10, cooldown_type: commands.BucketType = commands.BucketType.user):
        self.bot = bot

    def get_version(self) -> str:
        """
        Get the version of the cog.
        """
        return __version__

    def get_author(self) -> str:
        """
        Get the author of the cog.
        """
        return __author__
