from redbot.core import Config, commands
from redbot.core.bot import Red

from msscommon.utils import MSSUtils


class ConfigHelper(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.utils = MSSUtils(bot)
        self.logger = self.utils.logger
        self.config = Config.get_conf(
            self, identifier=2444613707, force_registration=True
        )

    def get_config(self) -> Config:
        """
        Get the config for a cog.
        """
        return self.config

    def get_config_value(self, key: str) -> any:
        """
        Get the value of a config key for a cog.
        """
        return self.config.get_global_setting(key)

    def set_config_value(self, key: str, value: any) -> bool:
        """
        Set the value of a config key for a cog.
        """
        try:
            self.config.set_global_setting(key, value)
            return True
        except (AttributeError, KeyError) as e:
            self.logger.error(f"Error setting config value for key {key}: {e}")
            return False
