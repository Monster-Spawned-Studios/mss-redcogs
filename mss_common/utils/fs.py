"""
Copyright (c) 2025 Monster Spawned Studios | https://monsterspawned.studio | All rights reserved.
"""

import os
import shutil

from redbot.core import commands
from redbot.core.bot import Red


class MSSUtilsFS(commands.Cog):
    """
    A common file system utility library for Monster Spawned Studios cogs.
    """

    def __init__(self, bot: Red):
        """
        Initialize the MSSUtilsFS class.
        """
        self.bot = bot
        self.logger = getattr(self.bot, "log", None)

    def get_file_properties(self, file_path: str = None) -> dict:
        """
        Get properties about a file.

        Args:
            file_path (str, optional): The path to the file to get properties from. Defaults to None.

        Returns:
            dict: The properties of the file.
        """
        try:
            return {
                "size": os.path.getsize(file_path),
                "last_modified": os.path.getmtime(file_path),
                "last_accessed": os.path.getatime(file_path),
                "last_changed": os.path.getctime(file_path),
                "is_file": os.path.isfile(file_path),
                "is_dir": os.path.isdir(file_path),
                "is_symlink": os.path.islink(file_path),
                "is_readable": os.access(file_path, os.R_OK),
                "is_writable": os.access(file_path, os.W_OK),
                "is_executable": os.access(file_path, os.X_OK),
                "is_hidden": os.path.basename(file_path).startswith("."),
                "is_system": os.path.basename(file_path).startswith("."),
                "owner": os.stat(file_path).st_uid,
                "group": os.stat(file_path).st_gid,
                "permissions": oct(os.stat(file_path).st_mode)[-3:],
                "extension": os.path.splitext(file_path)[1],
                "name": os.path.basename(file_path),
                "path": file_path,
                "is_empty": os.path.getsize(file_path) == 0,
            }
        except (OSError, FileNotFoundError, PermissionError) as e:
            self.logger.error(f"Error getting file properties: {e}")
            return None

    async def create_directory(self, directory_path: str = None) -> bool:
        """
        Create a directory.

        Args:
            directory_path (str, optional): The path to the directory to create. Defaults to None.

        Returns:
            bool: True if the directory was created, False otherwise.

        Raises:
            FileExistsError: If the directory already exists.
            PermissionError: If the user does not have permission to create the directory.
            OSError: If the directory cannot be created.
        """
        try:
            os.makedirs(directory_path, exist_ok=True)
            return True
        except (OSError, PermissionError, FileExistsError) as e:
            self.logger.error(f"Error creating directory: {e}")
            return False

    async def delete_file(self, file_path: str = None) -> bool:
        """
        Delete a file.

        Args:
            file_path (str, optional): The path to the file to delete. Defaults to None.

        Returns:
            bool: True if the file was deleted, False otherwise.

        Raises:
            FileNotFoundError: If the file does not exist.
            PermissionError: If the user does not have permission to delete the file.
            OSError: If the file cannot be deleted.
            shutil.Error: If the file cannot be deleted.
        """
        try:
            shutil.rmtree(file_path)
            return True
        except (OSError, PermissionError, FileNotFoundError, shutil.Error) as e:
            self.logger.error(f"Error deleting file: {e}")
            return False

    async def delete_directory(self, directory_path: str = None) -> bool:
        """
        Delete a directory.

        Args:
            directory_path (str, optional): The path to the directory to delete. Defaults to None.

        Returns:
            bool: True if the directory was deleted, False otherwise.

        Raises:
            FileNotFoundError: If the directory does not exist.
            PermissionError: If the user does not have permission to delete the directory.
            OSError: If the directory cannot be deleted.
            shutil.Error: If the directory cannot be deleted.
        """
        try:
            shutil.rmtree(directory_path)
            return True
        except (OSError, PermissionError, FileNotFoundError, shutil.Error) as e:
            self.logger.error(f"Error deleting directory: {e}")
            return False

    async def rename_file(self, file_path: str = None, new_name: str = None) -> bool:
        """
        Rename a file.

        Args:
            file_path (str, optional): The path to the file to rename. Defaults to None.
            new_name (str, optional): The new name of the file. Defaults to None.

        Returns:
            bool: True if the file was renamed, False otherwise.

        Raises:
            FileExistsError: If the new file already exists.
            PermissionError: If the user does not have permission to rename the file.
            OSError: If the file does not exist.
            shutil.Error: If the file cannot be renamed.
        """
        try:
            shutil.move(file_path, new_name)
            return True
        except (OSError, PermissionError, FileExistsError, shutil.Error) as e:
            self.logger.error(f"Error renaming file: {e}")
            return False

    async def move_file(self, file_path: str = None, new_path: str = None) -> bool:
        """
        Move a file.

        Args:
            file_path (str, optional): The path to the file to move. Defaults to None.
            new_path (str, optional): The path to the new file. Defaults to None.

        Returns:
            bool: True if the file was moved, False otherwise.

        Raises:
            FileExistsError: If the new file already exists.
            PermissionError: If the user does not have permission to move the file.
            OSError: If the file does not exist.
            shutil.Error: If the file cannot be moved.
        """
        try:
            shutil.move(file_path, new_path)
            return True
        except (OSError, PermissionError, FileExistsError, shutil.Error) as e:
            self.logger.error(f"Error moving file: {e}")
            return False

    async def copy_file(self, file_path: str = None, new_path: str = None) -> bool:
        """
        Copy a file.

        Args:
            file_path (str, optional): The path to the file to copy. Defaults to None.
            new_path (str, optional): The path to the new file. Defaults to None.

        Returns:
            bool: True if the file was copied, False otherwise.

        Raises:
            FileExistsError: If the new file already exists.
            PermissionError: If the user does not have permission to copy the file.
            OSError: If the file does not exist.
            shutil.Error: If the file cannot be copied.
        """
        try:
            shutil.copy(file_path, new_path)
            return True
        except (OSError, PermissionError, FileExistsError, shutil.Error) as e:
            self.logger.error(f"Error copying file: {e}")
            return False

    async def copy_directory(self, directory_path: str = None, new_path: str = None, recursive: bool = True) -> bool:
        """
        Copy a directory.

        Args:
            directory_path (str, optional): The path to the directory to copy. Defaults to None.
            new_path (str, optional): The path to the new directory. Defaults to None.
            recursive (bool, optional): Whether to copy the directory recursively. Defaults to True.

        Returns:
            bool: True if the directory was copied, False otherwise.

        Raises:
            FileExistsError: If the new directory already exists.
            PermissionError: If the user does not have permission to copy the directory.
            OSError: If the directory does not exist.
            shutil.Error: If the directory cannot be copied.
        """
        try:
            shutil.copytree(directory_path, new_path, recursive=recursive)
            return True
        except (OSError, PermissionError, FileExistsError, shutil.Error) as e:
            self.logger.error(f"Error copying directory: {e}")
            return False
