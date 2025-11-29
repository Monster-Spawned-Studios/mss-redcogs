"""
Copyright (c) 2025 Monster Spawned Studios | https://monsterspawned.studio | All rights reserved.

A common library for Monster Spawned Studios cogs.
"""

import json
from os import getenv
from pathlib import Path

from dotenv import load_dotenv

from msscommon.mss_common import MSSCommon

__version__ = ""
__author__ = ""

OVERRIDE_ENV = True

# Load the environment variables
load_dotenv(override=OVERRIDE_ENV)

# Set the cog ID
COG_ID = getenv("COG_ID")

# Get the directory containing this __init__.py file
cog_dir = Path(__file__).parent
info_file = cog_dir / "info.json"

try:
    with open(info_file, "r", encoding="utf-8") as file:
        info_data = json.load(file)
        __version__ = info_data.get("version", "0.0.1")
        __author__ = info_data.get("author", ["Monster Spawned Studios"])[
            0].split("|")[0].strip()
except (FileNotFoundError, json.JSONDecodeError, KeyError, IndexError):
    __version__ = "0.0.1"
    __author__ = "Monster Spawned Studios"


async def setup(bot):
    """
    Setup the MSSCommon cog.
    """
    await bot.add_cog(MSSCommon(bot))
