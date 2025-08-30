"""
Copyright (c) 2025 Monster Spawned Studios | https://monsterspawned.studio | All rights reserved.

A cog to generate images using the ComfyUI API with support for
multiple models and NSFW detection. This cog can also install
and manage ComfyUI servers using the ComfyUI CLI tool through
the manager.py script/module.
"""

import asyncio
import subprocess
from datetime import datetime
from os import getcwd, pathsep
from os.path import exists
from shutil import make_archive

from redbot.core import commands
from redbot.core.bot import Red

from comfy_cog.comfy_utils import ComfyUtils
from comfy_cog.config import ComfyUIConfig


class ComfyManager(commands.Cog):
    """The Comfy Manager class handles the management of ComfyUI servers
    using the ComfyUI CLI tool. This includes installation, updates,
    and configuration of ComfyUI instances through the `comfy` command
    provided by the `comfy-cli` package.
    """

    def __init__(self, bot: Red):
        self.bot = bot
        self.comfy_utils = ComfyUtils(bot)
        self.configclass = ComfyUIConfig(bot)
        self.dev_mode = self.configclass.dev_mode
        self.config = self.configclass.config

        # Initialize variables as None to avoid errors
        self.comfy_process = None
        self.install_path = None
        self.use_existing_instance = None
        self.instance_path = None
        self.overwrite_instance = None

        # Create task to initialize config values
        self.bot.loop.create_task(self._initialize_comfy_process())

        try:
            # Check if the `comfy-cli` command is available and run it to verify it's working
            subprocess.run(
                ["comfy", "--version"], capture_output=True, text=True, check=False
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            # Log that the `comfy-cli` command failed to run
            self.bot.log.error(
                "The `comfy` command is not installed. Please install the `comfy-cli` package before running any instance management related commands!"
            )
            self.bot.log.error(f"Error: {e}")

        try:
            # Disable analytics from the comfy-cli package
            subprocess.run(
                ["comfy", "tracking", "disable"],
                capture_output=True,
                text=True,
                check=False,
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            # Log that the `comfy-cli` failed to disable analytics
            self.bot.log.error(
                "Something went wrong while disabling analytics from the `comfy-cli` package. Please try again manually by running `comfy tracking disable` in your RedBot virtual environment."
            )
            self.bot.log.error(f"Error: {e}")

        try:
            # Disable the ComfyUI GUI:
            subprocess.run(
                ["comfy", "manager", "disable-gui"],
                capture_output=True,
                text=True,
                check=False,
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            # Log that the `comfy-cli` failed to disable the ComfyUI GUI
            self.bot.log.error(
                "Something went wrong while disabling the ComfyUI GUI. Please try again manually by running `comfy manager disable-gui` in your RedBot virtual environment."
            )
            self.bot.log.error(f"Error: {e}")

    async def _initialize_comfy_process(self):
        """Initialize config values asynchronously."""
        try:
            address = await self.config.address()
            if address and ":" in address:
                host, port = address.split(":", 1)
                self.comfy_process = subprocess.Popen(
                    ["comfy", "launch", "--", "--host", host, "--port", port],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                )
        except Exception:
            pass

    @commands.hybrid_group(name="comfy_manager")
    @commands.is_owner()
    async def comfy_manager(self, ctx: commands.Context):
        """
        Manage ComfyUI instances.
        """
        if ctx.interaction:
            await ctx.send("Please use the subcommands to manage ComfyUI instances.")

    @comfy_manager.command(name="install", aliases=["create", "new"])
    @commands.is_owner()
    async def comfy_manager_install(
        self, ctx: commands.Context, install_path: str = "", version: str = "latest"
    ):
        """Install ComfyUI server. Optionally specify install path."""
        path = (
            install_path.removesuffix(pathsep).removesuffix("ComfyUI")
            + pathsep
            + "ComfyUI"
            or self.install_path
            or getcwd() + pathsep + "ComfyUI"
        )
        await ctx.send(f"Installing ComfyUI at {path}...")
        proc = await self._run_comfy_cmd(
            [f"--workspace='{path}'", "install", "--version", f"'{version}'"]
        )
        await ctx.send(proc)

    @comfy_manager.command(name="update", aliases=["upgrade"])
    @commands.is_owner()
    async def comfy_manager_update(self, ctx: commands.Context):
        """Update ComfyUI server."""
        await ctx.send("Updating ComfyUI...")
        proc = await self._run_comfy_cmd(["update"])
        await ctx.send(proc)

    @comfy_manager.command(name="reinstall", aliases=["reset"])
    @commands.is_owner()
    async def comfy_manager_reinstall(self, ctx: commands.Context):
        """Reinstall/reset ComfyUI server."""
        await ctx.send("Reinstalling/Resetting ComfyUI...")
        proc = await self._run_comfy_cmd(["reinstall"])
        await ctx.send(proc)

    @comfy_manager.command(name="verify", aliases=["check", "status"])
    @commands.is_owner()
    async def comfy_manager_verify(self, ctx: commands.Context):
        """Verify ComfyUI installation."""
        await ctx.send("Verifying ComfyUI installation...")
        proc = await self._run_comfy_cmd(["verify"])
        await ctx.send(proc)

    @comfy_manager.command(name="backup")
    @commands.is_owner()
    async def comfy_manager_backup(self, ctx: commands.Context):
        """Backup ComfyUI instance."""
        await ctx.send("Backing up ComfyUI instance...")
        proc = await self._backup_comfyui_instance(instance_path=self.instance_path)
        await ctx.send(proc)

    @comfy_manager.command(name="start", aliases=["launch", "run"])
    @commands.is_owner()
    async def comfy_manager_start(self, ctx: commands.Context):
        """Start ComfyUI server."""
        await ctx.send("Starting ComfyUI server...")
        proc = await self._run_comfy_cmd(["launch", "--", "--port", "8188"])
        await ctx.send(proc)

    @comfy_manager.command(name="stop", aliases=["shutdown", "kill", "terminate"])
    @commands.is_owner()
    async def comfy_manager_stop(self, ctx: commands.Context):
        """Stop ComfyUI server."""
        await ctx.send("Stopping ComfyUI server...")
        proc = await self._run_comfy_cmd(["stop"])
        # Wait 60 seconds before sending the command to stop the server forcefully:
        await asyncio.sleep(60)
        proc = await self._run_system_cmd([""])
        await ctx.send(proc)

    @comfy_manager.command(name="delete", aliases=["remove", "uninstall"])
    @commands.is_owner()
    async def comfy_manager_delete(self, ctx: commands.Context):
        """Delete a ComfyUI instance. Requires confirmation."""
        confirm = False
        await ctx.send(
            "Are you sure you want to delete the ComfyUI instance? Please reply with 'I confirm' to proceed."
        )

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=45)
            if msg.content.lower() == "i confirm":
                confirm = True
        except TimeoutError:
            await ctx.send("Confirmation timed out. Please try again.")
            return

        if confirm:
            await ctx.send("Deleting ComfyUI instance...")
            proc = await self._run_comfy_cmd([""])
            await ctx.send(proc)

    @comfy_manager.command(name="set_default_instance")
    @commands.is_owner()
    async def comfy_manager_set_default_instance(
        self, ctx: commands.Context, instance_path: str
    ):
        """Set the default ComfyUI instance."""
        await ctx.send(f"Setting default ComfyUI instance path to `{instance_path}`...")
        if not exists(instance_path):
            await ctx.send(
                f"The path `{instance_path}` does not exist. Please enter a valid path and try again."
            )
            return
        proc = await self._run_comfy_cmd(
            [
                "set-default",
                f"'{instance_path}'",
            ]
        )
        await ctx.send(proc)

    async def _run_comfy_cmd(self, args: list[str]):
        """Helper to run comfy command on host."""
        cmd = ["comfy"] + args
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False)
            return (
                f"Output: {result.stdout}\nErrors: {result.stderr}"
                if result.returncode == 0
                else f"Failed: {result.stderr}"
            )
        except subprocess.CalledProcessError as e:
            return f"Subprocess error: {e}"
        except FileNotFoundError as e:
            return f"Command not found: {e}"
        except OSError as e:
            return f"OS error: {e}"
        except ValueError as e:
            return f"Value error: {e}"

    async def _run_system_cmd(self, cmd: str, args: list[str] = []):
        """Helper to run system command."""
        cmd = [cmd] + args
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False)
            return (
                f"Output: {result.stdout}\nErrors: {result.stderr}"
                if result.returncode == 0
                else f"Failed: {result.stderr}"
            )
        except subprocess.CalledProcessError as e:
            return f"Subprocess error: {e}"
        except FileNotFoundError as e:
            return f"Command not found: {e}"
        except OSError as e:
            return f"OS error: {e}"
        except ValueError as e:
            return f"Value error: {e}"

    async def _backup_comfyui_instance(self, instance_path: str, file_name: str = f"comfyui_backup_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.zip") -> bool:
        """Backup the ComfyUI instance."""
        try:
            await self.bot.log.info(f"Backing up ComfyUI instance at '{instance_path}'...")
            make_archive(file_name, "zip", instance_path)
            await self.bot.log.info(f"ComfyUI instance backed up to '{file_name}'.")
        except (FileNotFoundError, OSError, ValueError) as e:
            await self.bot.log.error(f"Error backing up ComfyUI instance: {e}")
            return False

    async def _restore_comfyui_instance(self, instance_path: str, file_name: str = f"comfyui_backup_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.zip") -> bool:
        """Restore the ComfyUI instance."""
        try:
            await self.bot.log.info(f"Restoring ComfyUI instance from '{file_name}'...")
            make_archive(instance_path, "zip", instance_path)
            await self.bot.log.info(f"ComfyUI instance restored from '{file_name}'.")
        except (FileNotFoundError, OSError, ValueError) as e:
            await self.bot.log.error(f"Error restoring ComfyUI instance: {e}")
            return False
