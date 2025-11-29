"""
Copyright (c) 2025 Monster Spawned Studios | https://monsterspawned.studio | All rights reserved.

A cog to generate images using the ComfyUI API with support for
multiple models and NSFW detection. This cog can also install
and manage ComfyUI servers using the ComfyUI CLI tool through
the manager.py script/module.
"""

from os import getenv

from discord import File, Member
from redbot.core import Config, commands
from redbot.core.bot import Red


class ComfyUIConfig(commands.Cog):
    """
    Config data and functions for the ComfyUI cog.
    """

    def __init__(self, bot: Red):
        self.bot = bot
        try:
            self.COG_ID = int(getenv("COMFY_COG_ID", "0"))
        except (ValueError, TypeError):
            self.COG_ID = 0

        self.dev_mode = self.is_development_mode()
        self.config = Config.get_conf(
            self, identifier=self.COG_ID, force_registration=True
        )

        self.experimental_mode = self.dev_mode or self.config.get_global_setting(
            "enable_experimental_features"
        )

        default_global = {
            "comfy_host": "127.0.0.1",
            "comfy_port": 8188,
            "address": "127.0.0.1:8188",
            "workflow_file": "",
            "models": {},
            "loras": {},
            "lora_weights": {},
            "lora_weight_locked": True,
            "embeddings": {},
            "lycoris": {},
            "lycoris_weights": {},
            "lycoris_weight_locked": True,
            "nsfw_threshold": 0.7,
            "nsfw_lora_name": "NSFWFilter.safetensors",
            "nsfw_notification_channel": 0,
            "nsfw_notification_users": [],
            "log_user_commands": True,
            "admin_log_channel": 0,
            "extra_launch_arguments": "",
            "enable_experimental_features": False,
            "encryption_key": None,
            "global_auth_token": None,
        }
        experimental_global = {
            "enable_instance_management": False,
            "comfyui_instances": {},
            "comfyui_instance_name": "",
            "comfyui_instance_path": "",
            "comfyui_instance_use_existing": False,
            "comfyui_overwrite_instance": False,
        }

        self.config.register_global(**default_global)
        self.config.register_user(auth_token=None)
        if self.experimental_mode:
            # Log that experimental features are enabled
            self.bot.log.warning(
                "Experimental features are enabled! Expect bugs, instability, and potential crashes!"
            )
            self.config.register_global(**experimental_global)

    def is_development_mode(self) -> bool:
        """
        Check if the bot is in development mode.
        """
        return self.bot.get_cog("Dev") is not None

    def is_owner(self, user: Member) -> bool:
        """
        Check if the user is the bot owner.
        """
        return self.bot.is_owner(user)
