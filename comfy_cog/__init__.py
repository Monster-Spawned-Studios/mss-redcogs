"""
Copyright (c) 2025 Monster Spawned Studios | https://monsterspawned.studio | All rights reserved.

A cog to generate images using the ComfyUI API with support for
multiple models and NSFW detection. This cog can also install
and manage ComfyUI servers using the ComfyUI CLI tool through
the manager.py script/module.
"""

from json import load as load_json
from os import getcwd, pathsep

from .comfyui import ComfyUI

__version__ = ""
__author__ = ""

with open(getcwd() + pathsep + "info.json", "r", encoding="utf-8") as file:
    __version__ = load_json(file)["version"]
    __author__ = load_json(file)["author"][0].split("|")[0].strip()


async def setup(bot):
    """
    Setup the ComfyUI cog.
    """
    await bot.add_cog(ComfyUI(bot))
