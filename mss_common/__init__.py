"""
Copyright (c) 2025 Monster Spawned Studios | https://monsterspawned.studio | All rights reserved.

A common library for Monster Spawned Studios cogs.
"""

from json import load as load_json
from os import getcwd, pathsep

from mss_common.mss_common import MSSCommon

__version__ = ""
__author__ = ""


def __init__():
    with open(getcwd() + pathsep + "info.json", "r", encoding="utf-8") as file:
        __version__ = load_json(file)["version"]
        __author__ = load_json(file)["author"][0].split("|")[0].strip()

    print(f"Monster Spawned Studios Common v{__version__} by {__author__}")


async def setup(bot):
    """
    Setup the MSSCommon cog.
    """
    await bot.add_cog(MSSCommon(bot))
