"""
Copyright (c) 2025 Monster Spawned Studios | https://monsterspawned.studio | All rights reserved.
"""

import asyncio
from asyncio import QueueEmpty
from typing import Any, Callable

from redbot.core import commands
from redbot.core.bot import Red

from .utils.general import MSSUtilsGeneral


class MSSUtils(commands.Cog):
    """
    A common utility library for Monster Spawned Studios cogs.
    """

    def __init__(self, bot: Red):
        self.bot = bot
        self.logger = getattr(self.bot, "log", None)
        self.queues = {}

    async def add_to_queue(self, function: Callable, max_queue_size: int = 100, queue_cooldown: int = 15, queue_timeout: int = 10, queue_name: str = None) -> bool:
        """
        Add a function to a queue.

        Args:
            function (Callable): The function to add to the queue.
            max_queue_size (int, optional): The maximum size of the queue. Defaults to 100.
            queue_cooldown (int, optional): The cooldown between function calls. Defaults to 15.
            queue_timeout (int, optional): The timeout for the queue. Defaults to 10.
            queue_name (str, optional): The name of the queue. Defaults to None.
        """
        try:
            if queue_name not in self.queues:
                self.queues[queue_name] = asyncio.Queue(maxsize=max_queue_size)

            queue = self.queues[queue_name]

            queue.maxsize = max_queue_size

            while queue.full():
                await asyncio.sleep(queue_timeout)

            await queue.put(function)

            await asyncio.sleep(queue_cooldown)

            return True
        except asyncio.QueueFull:
            self.logger.error(
                f"Queue is full, function {function} not added to queue {queue_name}.")
            return False
        except Exception as e:
            self.logger.error(
                f"Error adding function to queue {queue_name}: {e}")
            return False

    async def get_from_queue(self, queue_name: str = None) -> Any | None:
        """
        Get a function result from a queue.
        """
        try:
            return await self.queues[queue_name].get()
        except asyncio.QueueEmpty:
            self.logger.error(
                f"Queue is empty, no function result found in queue {queue_name}.")
            return None
        except Exception as e:
            self.logger.error(
                f"Error getting function result from queue {queue_name}: {e}")
            return None
