"""
Copyright (c) 2025 Monster Spawned Studios | https://monsterspawned.studio | All rights reserved.
"""

import psutil
from redbot.core import commands
from redbot.core.bot import Red


class MSSUtilsProc(commands.Cog):
    """
    A common process utility library for Monster Spawned Studios cogs.
    """

    def __init__(self, bot: Red):
        """
        Initialize the MSSUtilsProc class.
        """
        self.bot = bot
        self.logger = getattr(self.bot, "log", None)

    async def get_process_info(self, process_id: int = None) -> dict:
        """
        Get information about a process.

        Args:
            process_id (int, optional): The ID of the process to get information about. Defaults to None.

        Returns:
            dict: The information about the process.
        """
        if not process_id:
            return {}

        try:
            return psutil.Process(process_id).as_dict(attrs=['pid', 'name', 'status', 'create_time', 'cpu_percent', 'memory_percent'])
        except psutil.NoSuchProcess:
            return {}

    async def get_process_list(self) -> list:
        """
        Get a list of all processes.

        Returns:
            list: A list of all processes.
        """
        try:
            return [psutil.Process(process.pid).as_dict(attrs=['pid', 'name', 'status']) for process in psutil.Process().children()]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return []

    async def get_process_list_by_name(self, process_name: str = None, recursive: bool = True) -> list:
        """
        Get a list of all processes by name.

        Args:
            process_name (str, optional): The name of the process to get. Defaults to None.

        Returns:
            list: A list of all processes by name.
        """
        if not process_name:
            return []

        try:
            return [psutil.Process(process.pid).as_dict(attrs=['pid', 'name', 'status']) for process in psutil.Process().children() if process.name() == process_name]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return []

    async def get_process_list_by_pid(self, process_pid: int = None, recursive: bool = True) -> list:
        """
        Get a list of all processes by PID.

        Args:
            process_pid (int, optional): The PID of the process to get. Defaults to None.
            recursive (bool, optional): Whether to get the process list recursively. Defaults to True.

        Returns:
            list: A list of all processes by PID.
        """
        if not process_pid:
            return []

        try:
            return [psutil.Process(process.pid).as_dict(attrs=['pid', 'name', 'status']) for process in psutil.Process().children() if process.pid == process_pid]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return []

    async def get_process_list_by_name_and_pid(self, process_name: str = None, process_pid: int = None, recursive: bool = True) -> list:
        """
        Get a list of all processes by name and PID.

        Args:
            process_name (str, optional): The name of the process to get. Defaults to None.
            process_pid (int, optional): The PID of the process to get. Defaults to None.
            recursive (bool, optional): Whether to get the process list recursively. Defaults to True.

        Returns:
            list: A list of all processes by name and PID.
        """
        if not process_name or not process_pid:
            return []

        try:
            return [psutil.Process(process.pid).as_dict(attrs=['pid', 'name', 'status']) for process in psutil.Process().children() if process.name() == process_name and process.pid == process_pid]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return []

    async def get_process_owner(self, process_id: int = None) -> str:
        """
        Get the owner of a process.

        Args:
            process_id (int, optional): The ID of the process to get the owner of. Defaults to None.

        Returns:
            str: The owner of the process.
        """
        if not process_id:
            return "Unknown"

        try:
            return psutil.Process(process_id).username()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return "Unknown"

    async def terminate_process(self, process_id: int = None) -> bool:
        """
        Terminate a process.

        Args:
            process_id (int, optional): The ID of the process to terminate. Defaults to None.

        Returns:
            bool: True if the process was terminated, False otherwise.
        """
        try:
            return psutil.Process(process_id).terminate()
        except psutil.NoSuchProcess:
            return False

    async def kill_process(self, process_id: int = None) -> bool:
        """
        Kill a process.

        Args:
            process_id (int, optional): The ID of the process to kill. Defaults to None.

        Returns:
            bool: True if the process was killed, False otherwise.
        """
        try:
            return psutil.Process(process_id).kill()
        except psutil.NoSuchProcess:
            return False

    async def restart_process(self, process_id: int = None) -> bool:
        """
        Restart a process.

        Args:
            process_id (int, optional): The ID of the process to restart. Defaults to None.

        Returns:
            bool: True if the process was restarted, False otherwise.
        """
        try:
            return psutil.Process(process_id).restart()
        except psutil.NoSuchProcess:
            return False

    async def suspend_process(self, process_id: int = None) -> bool:
        """
        Suspend a process.

        Args:
            process_id (int, optional): The ID of the process to suspend. Defaults to None.

        Returns:
            bool: True if the process was suspended, False otherwise.
        """
        try:
            return psutil.Process(process_id).suspend()
        except psutil.NoSuchProcess:
            return False

    async def resume_process(self, process_id: int = None) -> bool:
        """
        Resume a process.

        Args:
            process_id (int, optional): The ID of the process to resume. Defaults to None.

        Returns:
            bool: True if the process was resumed, False otherwise.
        """
        try:
            return psutil.Process(process_id).resume()
        except psutil.NoSuchProcess:
            return False

    async def get_process_memory_info(self, process_id: int = None) -> dict:
        """
        Get the memory information of a process.

        Args:
            process_id (int, optional): The ID of the process to get the memory information of. Defaults to None.

        Returns:
            psutil.Process.memory_info: The memory information of the process.
        """
        try:
            return psutil.Process(process_id).memory_info()
        except psutil.NoSuchProcess:
            return None

    async def get_process_cpu_percent(self, process_id: int = None) -> float:
        """
        Get the CPU usage of a process.

        Args:
            process_id (int, optional): The ID of the process to get the CPU usage of. Defaults to None.

        Returns:
            float: The CPU usage of the process.
        """
        try:
            return psutil.Process(process_id).cpu_percent()
        except psutil.NoSuchProcess:
            return None

    async def get_process_memory_percent(self, process_id: int = None) -> float:
        """
        Get the memory usage of a process.

        Args:
            process_id (int, optional): The ID of the process to get the memory usage of. Defaults to None.

        Returns:
            float: The memory usage of the process.
        """
        try:
            return psutil.Process(process_id).memory_percent()
        except psutil.NoSuchProcess:
            return None

    async def get_process_cpu_count(self, process_id: int = None, logical: bool = True) -> int:
        """
        Get the CPU count of a process.

        Args:
            process_id (int, optional): The ID of the process to get the CPU count of. Defaults to None.
            logical (bool, optional): Whether to get the logical CPU count. Defaults to True.

        Returns:
            int: The CPU count of the process.
        """
        try:
            return psutil.Process(process_id).cpu_count(logical=logical)
        except psutil.NoSuchProcess:
            return None

    async def get_process_memory_info(self, process_id: int = None) -> psutil.Process.memory_info:
        """
        Get the memory information of a process.
        """
        try:
            return psutil.Process(process_id).memory_info()
        except psutil.NoSuchProcess:
            return None
