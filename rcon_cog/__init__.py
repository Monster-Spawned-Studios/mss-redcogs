"""
Copyright (c) 2025 Monster Spawned Studios | https://monsterspawned.studio | All rights reserved.

A cog to manage game servers using the RCON protocol and provide utilities for game servers.
"""

from json import load as load_json
from os import getcwd, pathsep

from loguru import logger

from .rcon_cog import RCON_Cog

__version__ = ""
__author__ = ""

with open(getcwd() + pathsep + "info.json", "r", encoding="utf-8") as file:
    __version__ = load_json(file)["version"]
    __author__ = load_json(file)["author"][0].split("|")[0].strip()


def get_logger(name: str) -> logger:
    """
    Get a logger for the RCON cog.
    """
    return logger.bind(name=name)


async def setup(bot):
    """
    Setup the RCON cog.
    """
    await bot.add_cog(RCON_Cog(bot))
