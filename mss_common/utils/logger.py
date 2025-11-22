"""
Copyright (c) 2025 Monster Spawned Studios | https://monsterspawned.studio | All rights reserved.

A utility module to handle logging.
"""
from logging import INFO, NOTSET, FileHandler, Formatter, Logger


class MSSUtilsLogger(Logger):
    def __init__(self, name: str, level: int = NOTSET):
        super().__init__(name, level)
        self.addHandler(MSSUtilsFileHandler("mss_utils.log", level))
        self.setLevel(level)
        self.propagate = False
        self.setFormatter(Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    @staticmethod
    def get_logger(name: str = "") -> Logger:
        """
        Get a logger with the given name.
        """
        return MSSUtilsLogger(f"MSSUtilsLogger.{name or 'Unknown'}")

class MSSUtilsFileHandler(FileHandler):
    def __init__(self, filename: str = "mss_utils.log", level: int = INFO):
        super().__init__(filename)
        self.setFormatter(Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.setLevel(level)
        self.propagate = False

