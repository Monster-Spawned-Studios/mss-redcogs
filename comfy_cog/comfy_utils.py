"""
Copyright (c) 2025 Monster Spawned Studios | https://monsterspawned.studio | All rights reserved.

Utility functions for the ComfyUI cog.
"""

import os
import platform
import subprocess
from os import pathsep

import psutil
import torch
from redbot.core import commands
from redbot.core.bot import Red


class ComfyUtils(commands.Cog):
    """
    Utility functions for the ComfyUI cog.
    """

    def __init__(self, bot: Red):
        self.bot = bot
        self.gpu_type = self.get_gpu_type()

    def get_gpu_type(self) -> str:
        """
        Get the type of GPU in the system.

        Returns:
            str: The type of GPU in the system.
        """
        try:
            # Check for NVIDIA GPUs:
            if torch.cuda.is_available():
                return "cuda"
            # Check for ROCm-capable AMD GPUs:
            elif self.is_rocm_available():
                return "rocm"
            # Check for Apple Silicon:
            elif torch.backends.mps.is_available():
                return "apple_silicon"
            # Check for CPU:
            elif torch.get_default_device().type == "cpu":
                return "cpu"
            # Check for other AMD GPUs (non-ROCm):
            elif self.has_amd_gpu():
                return "amd_other"
            else:
                return "unknown"
        except (ImportError, RuntimeError):
            return "unknown"

    def is_rocm_available(self) -> bool:
        """
        Check if ROCm is available and working.

        Returns:
            bool: True if ROCm is available, False otherwise
        """
        try:
            # Check if PyTorch was compiled with ROCm support
            if hasattr(torch, "hip") and torch.hip.is_available():
                return True

            # Alternative check using device count
            if hasattr(torch, "hip") and torch.hip.device_count() > 0:
                return True

            return False
        except (AttributeError, RuntimeError):
            return False

    def has_amd_gpu(self) -> bool:
        """
        Check if the system has an AMD GPU (regardless of ROCm support).

        Returns:
            bool: True if AMD GPU is detected, False otherwise
        """
        try:
            if platform.system() == "Windows":
                return self._check_amd_gpu_windows()
            elif platform.system() == "Linux":
                return self._check_amd_gpu_linux()
            else:
                return False
        except (OSError, ValueError, KeyError):
            return False

    def _check_amd_gpu_windows(self) -> bool:
        """Check for AMD GPU on Windows using PowerShell."""
        try:
            # Use PowerShell to query GPU information
            cmd = [
                "powershell",
                "-Command",
                "Get-WmiObject -Class Win32_VideoController | Where-Object {$_.Name -like '*AMD*' -or $_.Name -like '*Radeon*'} | Select-Object Name",
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10, check=False
            )
            return "AMD" in result.stdout or "Radeon" in result.stdout
        except (
            subprocess.TimeoutExpired,
            subprocess.SubprocessError,
            FileNotFoundError,
        ):
            return False

    def _check_amd_gpu_linux(self) -> bool:
        """Check for AMD GPU on Linux using lspci."""
        try:
            # Use lspci to find AMD GPUs
            cmd = ["lspci", "-v"]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10, check=False
            )

            # Look for AMD/ATI graphics controllers
            output = result.stdout.lower()
            return "amd" in output or "ati" in output or "radeon" in output
        except (
            subprocess.TimeoutExpired,
            subprocess.SubprocessError,
            FileNotFoundError,
        ):
            return False

    def get_rocm_gpu_info(self) -> dict:
        """
        Get detailed information about ROCm GPU if available.

        Returns:
            dict: Dictionary containing GPU information or empty dict if not available
        """
        if not self.is_rocm_available():
            return {}

        try:
            info = {}
            if hasattr(torch, "hip"):
                info["device_count"] = torch.hip.device_count()
                if torch.hip.device_count() > 0:
                    info["current_device"] = torch.hip.current_device()
                    info["device_name"] = torch.hip.get_device_name(0)
                    info["device_properties"] = torch.hip.get_device_properties(0)
            return info
        except (AttributeError, RuntimeError):
            return {}

    def get_gpu_vram(self) -> int:
        """Get the amount of VRAM in the system."""
        try:
            if self.gpu_type == "cuda":
                return torch.cuda.get_device_properties(0).total_memory
            elif self.gpu_type == "rocm":
                return torch.hip.get_device_properties(0).total_memory
            else:
                return 0
        except (AttributeError, RuntimeError):
            return 0

    def get_gpu_name(self) -> str:
        """Get the name of the GPU in the system."""
        try:
            if self.gpu_type == "cuda":
                return torch.cuda.get_device_name(0)
            elif self.gpu_type == "rocm":
                return torch.hip.get_device_name(0)
            else:
                return "Unknown"
        except (AttributeError, RuntimeError):
            return "Unknown"

    def get_gpu_count(self) -> int:
        """Get the number of GPUs in the system."""
        try:
            if self.gpu_type == "cuda":
                return torch.cuda.device_count()
            elif self.gpu_type == "rocm":
                return torch.hip.device_count()
            else:
                return 0
        except (AttributeError, RuntimeError):
            return 0

    def is_rocm_capable(self) -> bool:
        """
        Check if the system has a ROCm-capable AMD GPU.
        This includes both hardware and software requirements.

        Returns:
            bool: True if ROCm-capable, False otherwise
        """
        # First check if ROCm is available (software)
        if not self.is_rocm_available():
            return False

        # Check if we have AMD GPU hardware
        if not self.has_amd_gpu():
            return False

        # Additional checks for ROCm compatibility
        try:
            if platform.system() == "Linux":
                # Check for ROCm installation
                rocm_paths = ["/opt/rocm", "/usr/local/rocm", "/opt/rocm-*"]

                for path in rocm_paths:
                    if os.path.exists(path):
                        return True

                # Check for ROCm environment variables
                if any(env_var in os.environ for env_var in ["ROCM_PATH", "HIP_PATH"]):
                    return True

            return True  # If we have ROCm available and AMD GPU, assume capable
        except (OSError, ValueError, KeyError):
            return False

    def get_cpu_count(self) -> int:
        """
        Get the number of CPUs in the system.

        Returns:
            int: The number of CPUs in the system.
        """
        return os.cpu_count()

    def get_cpu_name(self) -> str:
        """
        Get the name of the CPU in the system.

        Returns:
            str: The name of the CPU in the system.
        """
        return platform.processor()

    def get_cpu_capability(self) -> str:
        """
        Get the CPU capability of the system.

        Returns:
            str: The CPU capability of the system.
        """
        return torch.backends.cpu.get_cpu_capability()

    def get_os_name(self) -> str:
        """
        Get the name of the OS in the system.

        Returns:
            str: The name of the OS in the system.
        """
        if "windows" in platform.system().lower():
            return "windows"
        elif "linux" in platform.system().lower():
            return "linux"
        elif "macos" in platform.system().lower():
            return "macos"
        else:
            return "unknown"

    def get_os_version(self) -> str:
        """
        Get the version of the OS in the system.

        Returns:
            str: The version of the OS in the system.
        """
        return platform.version()

    def get_os_release(self) -> str:
        """
        Get the release of the OS in the system.

        Returns:
            str: The release of the OS in the system.
        """
        return platform.release()

    def get_os_architecture(self) -> str:
        """
        Get the architecture of the OS in the system.

        Returns:
            str: The architecture of the OS in the system.
        """
        return platform.machine()

    def is_64bit(self) -> bool:
        """
        Check if the system is 64-bit.

        Returns:
            bool: True if the system is 64-bit, False otherwise
        """
        return platform.machine().lower().contains("64")

    def is_arm(self) -> bool:
        """
        Check if the system is ARM.

        Returns:
            bool: True if the system is ARM, False otherwise
        """
        return platform.machine().lower().contains("arm")

    def get_running_python_version(self) -> str:
        """
        Get the version of the Python interpreter in the system.

        Returns:
            str: The version of the Python interpreter in the system.
        """
        return platform.python_version()

    def get_python_implementation(self) -> str:
        """
        Get the implementation of the Python interpreter in the system.

        Returns:
            str: The implementation of the Python interpreter in the system.
        """
        return platform.python_implementation()

    def get_comfyui_version(self) -> str:
        """
        Get the version of ComfyUI in the system.

        Returns:
            str: The version of ComfyUI in the system, obtained by reading the `comfyui_version.py` file at the root of the ComfyUI installation.
        """
        try:
            comfyui_version_file = os.path.join(
                str(
                    self.bot.get_cog("ComfyUI").config.comfyui_instance_path
                ).removesuffix(pathsep),
                pathsep,
                "comfyui_version.py",
            )
            with open(comfyui_version_file, "r", encoding="utf-8") as file:
                return file.read().strip()
        except (FileNotFoundError, OSError):
            return "Unknown"

    def get_comfyui_path(self) -> str:
        """
        Get the path of ComfyUI in the system.

        Returns:
            str: The path of ComfyUI in the system.
        """
        return self.bot.get_cog("ComfyUI").config.comfyui_instance_path

    def terminate_comfyui_server(self, timeout: int = 15) -> bool:
        """
        Terminate the ComfyUI server.

        Returns:
            bool: True if the ComfyUI server was terminated successfully, False otherwise
        """
        try:
            comfyui_server_process = psutil.Process(
                self.bot.get_cog("ComfyUI").config.comfyui_instance_path
                + pathsep
                + "server.py"
            )
            comfyui_server_process.terminate()
            comfyui_server_process.wait(timeout=timeout)
            self.bot.log.info("ComfyUI server terminated successfully.")
            return True
        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
            psutil.TimeoutExpired,
        ) as e:
            self.bot.log.error(f"Failed to terminate ComfyUI server.\nError: {e}")
            return False
