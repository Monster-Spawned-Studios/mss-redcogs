"""
Copyright (c) 2025 Monster Spawned Studios | https://monsterspawned.studio | All rights reserved.

A common library for Monster Spawned Studios cogs.
This class contains utility functions for the Monster Spawned Studios Common library
such as telemetry, logging, and other utility functions.
"""

import string
import sys
from random import choices

from discord import Channel, Guild, Member
from redbot.core import commands
from redbot.core.bot import Red


class MSSUtilsGeneral(commands.Cog):
    """
    A common general utility library for Monster Spawned Studios cogs.
    """

    def __init__(self, bot: Red):
        """
        Initialize the MSSUtilsGeneral class.
        """
        self.bot = bot
        self.logger = getattr(self.bot, "log", None)

    def log(self, level: str = "info", message: str = ""):
        """
        Log a message using the RedBot logging system with different log levels.

        Args:
            level (str): The log level ("info", "warning", "error", "debug", "critical").
            message (str): The message to log.
        """
        # Use Python 3.10+ match-case for switch-like behavior, fallback to if-elif for older versions
        if not self.logger:
            # If the bot does not have a logger, fallback to print
            print(f"[{level.upper()}] {message}")
            return

        if not message:
            # If the message is empty, return
            self.bot.log.warning(
                f"No message provided to log from function: {self.__class__.__name__}.{sys._getframe().f_code.co_name}")
            return

        # Use match-case if available, else fallback to if-elif
        try:
            match level.lower():
                case "info" | "information":
                    self.logger.info(message)
                case "warning" | "warn":
                    self.logger.warning(message)
                case "error" | "err":
                    self.logger.error(message)
                case "debug" | "dbg":
                    self.logger.debug(message)
                case "critical" | "fatal" | "crit":
                    self.logger.critical(message)
                case _:
                    # Default to info if the level is not recognized
                    self.logger.info(message)
        except SyntaxError:
            # For Python <3.10, fallback to if-elif
            lvl = level.lower()
            if lvl == "info":
                self.logger.info(message)
            elif lvl in ("warning", "warn"):
                self.logger.warning(message)
            elif lvl == "error":
                self.logger.error(message)
            elif lvl == "debug":
                self.logger.debug(message)
            elif lvl == "critical":
                self.logger.critical(message)
            else:
                self.logger.info(message)

    def get_random_string(self, length: int = 10, uppercase: bool = True, lowercase: bool = True, digits: bool = True) -> str:
        """
        Get a random string of a given length.
        """
        chars = ""
        if uppercase:
            chars = string.ascii_uppercase
        if lowercase:
            chars += string.ascii_lowercase
        if digits:
            chars += string.digits
        return ''.join(choices(chars, k=length))

    def get_random_number(self, length: int = 10) -> str:
        """
        Get a random number of a given length.
        """
        return ''.join(choices(string.digits, k=length))

    def convert_to_snake_case(self, string: str) -> str:
        """
        Convert a string to snake_case.
        """
        return string.lower().replace(" ", "_").replace("-", "_").replace(".", "_").replace(":", "_").replace(";", "_").replace(",", "_").replace("!", "_").replace("?", "_").replace("'", "_").replace("\"", "_").replace("`", "_").replace("~", "_").replace("|", "_").replace("\\", "_").replace("/", "_").replace("*", "_").replace("&", "_").replace("^", "_").replace("%", "_").replace("$", "_").replace("#", "_").replace("@", "_").replace("!", "_").replace("?", "_").replace("'", "_").replace("\"", "_").replace("`", "_").replace("~", "_").replace("|", "_").replace("\\", "_").replace("/", "_").replace("*", "_").replace("&", "_").replace("^", "_").replace("%", "_").replace("$", "_").replace("#", "_").replace("@", "_").replace("!", "_").replace("?", "_").replace("'", "_").replace("\"", "_").replace("`", "_").replace("~", "_").replace("|", "_").replace("\\", "_").replace("/", "_").replace("*", "_").replace("&", "_").replace("^", "_").replace("%", "_").replace("$", "_").replace("#", "_").replace("@", "_")

    def convert_to_camel_case(self, string: str) -> str:
        """
        Convert a string to camelCase.
        """
        return string.lower().replace(" ", "").replace("-", "").replace(".", "").replace(":", "").replace(";", "").replace(",", "").replace("!", "").replace("?", "").replace("'", "").replace("\"", "").replace("`", "").replace("~", "").replace("|", "").replace("\\", "").replace("/", "").replace("*", "").replace("&", "").replace("^", "").replace("%", "").replace("$", "").replace("#", "").replace("@", "").replace("!", "").replace("?", "").replace("'", "").replace("\"", "").replace("`", "").replace("~", "").replace("|", "").replace("\\", "").replace("/", "").replace("*", "").replace("&", "").replace("^", "").replace("%", "").replace("$", "").replace("#", "").replace("@", "")

    def get_discord_user_id(self, user: Member) -> str:
        """
        Get the Discord user ID from a Discord member object.
        """
        return user.id

    def get_discord_user_name(self, user: Member) -> str:
        """
        Get the Discord user name from a Discord member object.
        """
        return user.name

    def get_discord_user_discriminator(self, user: Member) -> str:
        """
        Get the Discord user discriminator from a Discord member object.
        """
        return user.discriminator

    def get_discord_user_avatar(self, user: Member) -> str:
        """
        Get the Discord user avatar from a Discord member object.
        """
        return user.avatar.url

    def get_discord_user_display_name(self, user: Member) -> str:
        """
        Get the Discord user display name from a Discord member object.
        """
        return user.display_name

    def get_channel_id(self, channel: Channel) -> str:
        """
        Get the Discord channel ID from a Discord channel object.
        """
        return channel.id

    def get_channel_name(self, channel: Channel) -> str:
        """
        Get the Discord channel name from a Discord channel object.
        """
        return channel.name

    def get_channel_type(self, channel: Channel) -> str:
        """
        Get the Discord channel type from a Discord channel object.
        """
        return channel.type

    def get_guild_id(self, guild: Guild) -> str:
        """
        Get the Discord guild ID from a Discord guild object.
        """
        return guild.id

    def get_guild_name(self, guild: Guild) -> str:
        """
        Get the Discord guild name from a Discord guild object.
        """
        return guild.name

    def get_guild_owner_id(self, guild: Guild) -> str:
        """
        Get the Discord guild owner ID from a Discord guild object.
        """
        return guild.owner_id

    def get_guild_owner_name(self, guild: Guild) -> str:
        """
        Get the Discord guild owner name from a Discord guild object.
        """
        return guild.owner.name

    def get_guild_owner_discriminator(self, guild: Guild) -> str:
        """
        Get the Discord guild owner discriminator from a Discord guild object.
        """
        return guild.owner.discriminator
