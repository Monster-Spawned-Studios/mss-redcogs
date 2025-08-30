"""
Copyright (c) 2025 Monster Spawned Studios | https://monsterspawned.studio | All rights reserved.
"""

import json
from pathlib import Path

from .amp_cog import AMPCog

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


async def setup(bot):
    """
    Setup the AMP cog.
    """
    await bot.add_cog(AMPCog(bot))
