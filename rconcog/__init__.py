"""
Copyright (c) 2025 Monster Spawned Studios | https://monsterspawned.studio | All rights reserved.

A cog to manage game servers using the RCON protocol and provide utilities for game servers.
"""

import json
from pathlib import Path

from rconcog.rcon_cog import RCON_Cog

__version__ = ""
__author__ = ""

# Get the directory containing this __init__.py file
cog_dir = Path(__file__).parent
info_file = cog_dir / "info.json"

try:
    with open(info_file, "r", encoding="utf-8") as file:
        info_data = json.load(file)
        __version__ = info_data.get("version", "0.0.1")
        __author__ = info_data.get("author", ["Unknown"])[
            0].split("|")[0].strip()
except (FileNotFoundError, json.JSONDecodeError, KeyError, IndexError):
    __version__ = "0.0.1"
    __author__ = "Monster Spawned Studios"


def get_logger(name: str):
    """
    Get a logger for the RCON cog.
    """
    # Use RedBot's built-in logging instead of loguru
    return None  # Will be replaced with bot.log when cog is initialized


async def setup(bot):
    """
    Setup the RCON cog.
    """
    await bot.add_cog(RCON_Cog(bot))
