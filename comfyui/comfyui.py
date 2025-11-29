"""
Copyright (c) 2025 Monster Spawned Studios | https://monsterspawned.studio | All rights reserved.

A cog to generate images using the ComfyUI API with support for
multiple models and NSFW detection. This cog can also install
and manage ComfyUI servers using the ComfyUI CLI tool through
the manager.py script/module.
"""

import asyncio
import io
import json
import random
import uuid

import aiohttp
import discord
from nsfw_image_detector.detector import NSFWDetector
from PIL import Image, ImageDraw, ImageFont
from redbot.core import app_commands, commands
from redbot.core.bot import Red
from redbot.core.data_manager import cog_data_path

from comfyui import __author__, __version__
from comfyui.comfy_manager import ComfyManager
from comfyui.config import ComfyUIConfig
from msscommon.utils.security import decrypt_string, encrypt_string, generate_key


class ComfyUI(commands.Cog):
    """
    A cog to generate images using the ComfyUI API.
    """

    def __init__(self, bot: Red):
        self.bot = bot

        self.bot.log.info(f"ComfyUI cog starting up... (v{__version__})")
        self.bot.log.info(f"Made in the USA by {__author__}")
        configclass = ComfyUIConfig(bot)
        self.config = configclass.config
        self.dev_mode = configclass.dev_mode
        self.nsfw_detector = NSFWDetector()
        self.queue = asyncio.Queue(maxsize=10)
        self.cooldown = 90
        self.cooldown_type = commands.BucketType.user
        self.processor_task = self.bot.loop.create_task(self.queue_processor())

    def cog_unload(self):
        """
        Cleanly cancel the background task when the cog is unloaded.
        """
        self.processor_task.cancel()

    async def queue_processor(self):
        """
        The background task that processes items from the queue one by one.
        """
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                # Wait for an item to be available in the queue.
                ctx, prompt, model = await self.queue.get()
                # Once an item is received, run the actual processing logic.
                await self.do_generation(ctx, prompt, model)
            except Exception as e:
                print(f"Error in queue processor: {e}")
            finally:
                # Mark the task as done.
                self.queue.task_done()

    async def do_generation(self, ctx: commands.Context, prompt: str, model: str):
        """
        The actual processing logic for the queue.
        """
        await ctx.send(f"⚙️ Now generating an image for **{ctx.author.display_name}** with the prompt: `{prompt}`, using the model: `{model}`")

        address = await self.config.address()
        workflow_file = await self.config.workflow_file()
        if not address or not workflow_file:
            await ctx.send(
                "The ComfyUI address and workflow file must be set by the bot owner."
            )
            return

        try:
            def read_json(filename):
                with open(filename, "r", encoding="utf-8") as f:
                    return json.load(f)

            workflow = await self.bot.loop.run_in_executor(None, read_json, workflow_file)
        except (FileNotFoundError, json.JSONDecodeError):
            await ctx.send("The workflow file is not found or is invalid.")
            return

        models = await self.config.models()
        if model.lower() not in models:
            await ctx.send(
                f"Model `{model}` not found. Available models: {', '.join(models.keys())}"
            )
            return

        loras = await self.config.loras()
        lora_weights = await self.config.lora_weights()
        lora_weight_locked = await self.config.lora_weight_locked()
        embeddings = await self.config.embeddings()
        lycoris = await self.config.lycoris()
        lycoris_weights = await self.config.lycoris_weights()
        lycoris_weight_locked = await self.config.lycoris_weight_locked()

        workflow, lora_parts, lycoris_parts, embedding_parts = self._modify_workflow(
            workflow,
            model,
            prompt,
            models,
            loras,
            lora_weights,
            lora_weight_locked,
            embeddings,
            lycoris,
            lycoris_weights,
            lycoris_weight_locked,
        )

        if lora_parts and lora_parts[0].split(":")[1].lower() not in loras:
            await ctx.send("Could not find a LoraLoader node in the workflow.")
        if lycoris_parts and lycoris_parts[0].split(":")[1].lower() not in lycoris:
            await ctx.send("Could not find a LyCORIS model in the available options.")

        # Retrieve and decrypt auth token
        auth_token = None
        encrypted_token = await self.config.user(ctx.author).auth_token()
        key = await self.config.encryption_key()

        if encrypted_token and key:
            auth_token = decrypt_string(encrypted_token, key)

        # Fallback to global token if no user token
        if not auth_token:
            encrypted_global_token = await self.config.global_auth_token()
            if encrypted_global_token and key:
                auth_token = decrypt_string(encrypted_global_token, key)

        client_id = str(uuid.uuid4())
        queued_prompt = await self.queue_prompt(workflow, client_id, auth_token)
        if not queued_prompt:
            await ctx.send("Failed to queue the prompt.")
            return

        prompt_id = queued_prompt["prompt_id"]

        # Websocket connection to get the result
        ws_protocol = "wss" if address.startswith("https://") else "ws"
        ws_address = address.replace("https://", "").replace("http://", "")
        ws_url = f"{ws_protocol}://{ws_address}/ws?clientId={client_id}"
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        try:
            async with aiohttp.ClientSession().ws_connect(ws_url, headers=headers) as ws:
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        message = json.loads(msg.data)
                        if (
                            message["type"] == "executing"
                            and message["data"]["node"] is None
                            and message["data"]["prompt_id"] == prompt_id
                        ):
                            break  # Execution is done
        except (
            aiohttp.ClientError,
            aiohttp.WSServerHandshakeError,
            json.JSONDecodeError,
            KeyError,
        ) as e:
            await ctx.send(f"An error occurred during image generation: {e}")
            return

        history = await self.get_history(prompt_id, auth_token)
        if not history:
            await ctx.send("Could not retrieve generation history.")
            return

        history_entry = history.get(prompt_id)
        if not history_entry or "outputs" not in history_entry:
            await ctx.send("Generation failed or produced no output.")
            return

        for _, node_output in history_entry["outputs"].items():
            if "images" in node_output:
                for image_data in node_output["images"]:
                    image_bytes = await self.get_image(
                        image_data["filename"],
                        image_data["subfolder"],
                        image_data["type"],
                        token=auth_token
                    )
                    if image_bytes:
                        # NSFW Check
                        nsfw_threshold = await self.config.nsfw_threshold()
                        # Run NSFW check in executor
                        is_nsfw = await self.bot.loop.run_in_executor(
                            None,
                            self.nsfw_detector.is_nsfw,
                            io.BytesIO(image_bytes),
                            nsfw_threshold
                        )

                        if is_nsfw:
                            # NSFW Notification
                            notification_users = (
                                await self.config.nsfw_notification_users()
                            )
                            notification_channel_id = (
                                await self.config.nsfw_notification_channel()
                            )

                            if notification_users and notification_channel_id:
                                notification_channel = ctx.guild.get_channel(
                                    notification_channel_id
                                )
                                if notification_channel:
                                    user_mentions = " ".join(
                                        [
                                            f"<@{user_id}>"
                                            for user_id in notification_users
                                        ]
                                    )
                                    embed = discord.Embed(
                                        title="🚨 NSFW Content Detected",
                                        description=f"**User:** {ctx.author.mention} ({ctx.author.name}#{ctx.author.discriminator})\n"
                                        f"**Channel:** {ctx.channel.mention}\n"
                                        f"**Model:** {model}\n"
                                        f"**Prompt:** {prompt}\n"
                                        f"**Threshold:** {nsfw_threshold}",
                                        color=discord.Color.red(),
                                        timestamp=ctx.message.created_at,
                                    )
                                    embed.set_footer(
                                        text=f"User ID: {ctx.author.id}")
                                    await notification_channel.send(
                                        content=user_mentions, embed=embed
                                    )

                            await ctx.send(
                                "The generated image was flagged as NSFW and has been deleted."
                            )
                            return

                        # Watermarking
                        # Run watermarking in executor
                        watermarked_image = await self.bot.loop.run_in_executor(
                            None,
                            self.apply_watermark,
                            image_bytes,
                            ctx.author.display_name
                        )

                        file = discord.File(
                            io.BytesIO(watermarked_image), filename="image.png"
                        )
                        await ctx.send(
                            content=f"Here is your generated image, **{ctx.author.display_name}**!",
                            file=file,
                        )

        await ctx.send(f"✅ Generation finished for **{ctx.author.display_name}**!")

    async def get_image(self, filename, subfolder, folder_type, token=None):
        """
        Gets an image from the ComfyUI server.

        Args:
            filename (str): The filename of the image.
            subfolder (str): The subfolder of the image.
            folder_type (str): The type of folder the image is in.
            token (str): The auth token (decrypted).

        Returns:
            bytes: The image data.
        """
        address = await self.config.address()
        if not address:
            return None

        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        protocol = "https" if address.startswith("https://") else "http"
        clean_address = address.replace("https://", "").replace("http://", "")
        url = f"{protocol}://{clean_address}/view?filename={filename}&subfolder={subfolder}&type={folder_type}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.read()
                return None



    async def queue_prompt(self, prompt, client_id, token=None):
        """
        Queues a prompt to the ComfyUI server.

        Args:
            prompt (str): The prompt to queue.
            client_id (str): The client ID to use for the prompt.
            token (str): The auth token (decrypted).

        Returns:
            dict: The response from the ComfyUI server.
        """
        try:
            address = await self.config.address()
            if not address:
                return None

            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"

            protocol = "https" if address.startswith("https://") else "http"
            clean_address = address.replace("https://", "").replace("http://", "")

            p = {"prompt": prompt, "client_id": client_id}
            data = json.dumps(p).encode("utf-8")
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{protocol}://{clean_address}/prompt", data=data, headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except (aiohttp.ClientError, json.JSONDecodeError) as e:
            print(f"Error queuing prompt: {e}")
            return None

    async def get_history(self, prompt_id, token=None):
        """
        Gets the history of a prompt from the ComfyUI server.

        Args:
            prompt_id (str): The ID of the prompt to get the history of.
            token (str): The auth token (decrypted).

        Returns:
            dict: The history of the prompt.
        """
        address = await self.config.address()
        if not address:
            return None

        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            protocol = "https" if address.startswith("https://") else "http"
            clean_address = address.replace("https://", "").replace("http://", "")

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{protocol}://{clean_address}/history/{prompt_id}", headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except (aiohttp.ClientError, json.JSONDecodeError) as e:
            print(f"Error getting history: {e}")
            return None

    def apply_watermark(self, image_data: bytes, user_name: str) -> bytes:
        """
        Applies a watermark to the image.

        Args:
            image_data (bytes): The image data to apply the watermark to.
            user_name (str): The name of the user who generated the image.

        Returns:
            bytes: The image data with the watermark applied.
        """
        try:
            image = Image.open(io.BytesIO(image_data)).convert("RGBA")
            txt = Image.new("RGBA", image.size, (255, 255, 255, 0))

            try:
                font = ImageFont.truetype("arial.ttf", 40)
            except IOError:
                font = ImageFont.load_default()

            draw = ImageDraw.Draw(txt)
            text = f"Generated by: {user_name}"

            # Get text size using the new method
            left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
            textwidth = right - left
            textheight = bottom - top

            x = image.width - textwidth - 10
            y = image.height - textheight - 10

            draw.text((x, y), text, font=font, fill=(255, 255, 255, 128))

            watermarked = Image.alpha_composite(image, txt)

            img_byte_arr = io.BytesIO()
            watermarked.convert("RGB").save(img_byte_arr, format="PNG")
            return img_byte_arr.getvalue()
        except (OSError, ValueError, IOError) as e:
            print(f"Error applying watermark: {e}")
            return image_data

    def _modify_workflow(
        self,
        workflow,
        model,
        prompt,
        models,
        loras,
        lora_weights,
        lora_weight_locked,
        embeddings,
        lycoris,
        lycoris_weights,
        lycoris_weight_locked,
    ):
        """
        Modifies the workflow with user input for model, prompt, LoRAs, embeddings, and LyCORIS.

        Args:
            workflow (dict): The workflow to modify
            model (str): The model name
            prompt (str): The user prompt
            models (dict): Available models
            loras (dict): Available LoRAs
            lora_weights (dict): Default LoRA weights
            lora_weight_locked (bool): Whether LoRA weights are locked
            embeddings (dict): Available embeddings
            lycoris (dict): Available LyCORIS models
            lycoris_weights (dict): Default LyCORIS weights
            lycoris_weight_locked (bool): Whether LyCORIS weights are locked

        Returns:
            tuple: (modified_workflow, lora_parts, lycoris_parts, embedding_parts)
        """
        # Modify workflow with user input
        checkpoint_loader_node = next(
            (
                node
                for node in workflow.values()
                if node["class_type"] == "CheckpointLoaderSimple"
            ),
            None,
        )
        if checkpoint_loader_node:
            checkpoint_loader_node["inputs"]["ckpt_name"] = models[model.lower()]

        positive_prompt_node = next(
            (
                node
                for node in workflow.values()
                if node["class_type"] == "CLIPTextEncode"
            ),
            None,
        )
        if positive_prompt_node:
            positive_prompt_node["inputs"]["text"] = prompt

        # Handle LoRAs
        lora_parts = [p for p in prompt.split(
        ) if p.lower().startswith("lora:")]
        if lora_parts:
            lora_name_str = lora_parts[0].split(":")[1]

            # Check if weight is locked or user provided custom weight
            if lora_weight_locked or len(lora_parts[0].split(":")) <= 2:
                # Use default weight from config
                lora_strength = lora_weights.get(lora_name_str.lower(), 1.0)
            else:
                # User provided custom weight
                lora_strength = float(lora_parts[0].split(":")[2])

            if lora_name_str.lower() in loras:
                lora_loader_node = next(
                    (
                        node
                        for node in workflow.values()
                        if node["class_type"] == "LoraLoader"
                    ),
                    None,
                )
                if lora_loader_node:
                    lora_loader_node["inputs"]["lora_name"] = loras[
                        lora_name_str.lower()
                    ]
                    lora_loader_node["inputs"]["strength_model"] = lora_strength
                    lora_loader_node["inputs"]["strength_clip"] = lora_strength

        # Handle LyCORIS models
        lycoris_parts = [p for p in prompt.split(
        ) if p.lower().startswith("lycoris:")]
        if lycoris_parts:
            lycoris_name_str = lycoris_parts[0].split(":")[1]

            # Check if weight is locked or user provided custom weight
            if lycoris_weight_locked or len(lycoris_parts[0].split(":")) <= 2:
                # Use default weight from config
                lycoris_strength = lycoris_weights.get(
                    lycoris_name_str.lower(), 1.0)
            else:
                # User provided custom weight
                lycoris_strength = float(lycoris_parts[0].split(":")[2])

            if lycoris_name_str.lower() in lycoris:
                lycoris_loader_node = next(
                    (
                        node
                        for node in workflow.values()
                        if node["class_type"] == "LoraLoader"
                    ),
                    None,
                )
                if lycoris_loader_node:
                    lycoris_loader_node["inputs"]["lora_name"] = lycoris[
                        lycoris_name_str.lower()
                    ]
                    lycoris_loader_node["inputs"]["strength_model"] = lycoris_strength
                    lycoris_loader_node["inputs"]["strength_clip"] = lycoris_strength

        # Handle embeddings (they are typically added to the prompt text)
        embedding_parts = [
            p for p in prompt.split() if p.lower().startswith("embedding:")
        ]
        if embedding_parts:
            embedding_name_str = embedding_parts[0].split(":")[1]
            if embedding_name_str.lower() in embeddings:
                # Embeddings are usually handled by adding trigger words to the prompt
                # This is a simplified implementation - you might need to adjust based on your workflow
                pass

        return workflow, lora_parts, lycoris_parts, embedding_parts

    @commands.hybrid_group(name="comfy")
    @commands.is_owner()
    @app_commands.describe(description="Configuration commands for the ComfyUI cog.")
    async def comfy(self, ctx: commands.Context):
        """
        Configuration commands for the ComfyUI cog.
        """
        # Ensure encryption key exists
        if not await self.config.encryption_key():
            key = generate_key()
            await self.config.encryption_key.set(key)

        if ctx.interaction:
            await ctx.send("Please use the subcommands to configure ComfyUI settings.")

    @comfy.command(name="add-token")
    @app_commands.describe(token="The authentication token for the ComfyUI server")
    async def add_token(self, ctx: commands.Context, token: str):
        """
        Adds an authentication token for the ComfyUI server.
        The token is encrypted before storage.
        """
        # Delete the message to protect the token if possible
        if ctx.guild and ctx.channel.permissions_for(ctx.guild.me).manage_messages:
            try:
                await ctx.message.delete()
            except (discord.Forbidden, discord.NotFound):
                pass

        key = await self.config.encryption_key()
        if not key:
            key = generate_key()
            await self.config.encryption_key.set(key)

        encrypted_token = encrypt_string(token, key)
        if not encrypted_token:
            await ctx.send("Failed to encrypt token. Please check logs.")
            return

        await self.config.user(ctx.author).auth_token.set(encrypted_token)
        await ctx.send(f"Authentication token stored securely for {ctx.author.mention}.", delete_after=10)

    @comfy.command(name="set-global-token")
    @app_commands.describe(token="The global authentication token for the ComfyUI server")
    async def set_global_token(self, ctx: commands.Context, token: str):
        """
        Sets a global authentication token for the ComfyUI server.
        This token will be used if a user does not have their own token set.
        The token is encrypted before storage.
        """
        # Delete the message to protect the token if possible
        if ctx.guild and ctx.channel.permissions_for(ctx.guild.me).manage_messages:
            try:
                await ctx.message.delete()
            except (discord.Forbidden, discord.NotFound):
                pass

        key = await self.config.encryption_key()
        if not key:
            key = generate_key()
            await self.config.encryption_key.set(key)

        encrypted_token = encrypt_string(token, key)
        if not encrypted_token:
            await ctx.send("Failed to encrypt token. Please check logs.")
            return

        await self.config.global_auth_token.set(encrypted_token)
        await ctx.send("Global authentication token stored securely.", delete_after=10)

    @comfy.command(name="set-address")
    @app_commands.describe(
        address="The address of the ComfyUI server (e.g., localhost:8188)"
    )
    async def set_address(self, ctx: commands.Context, address: str):
        """Sets the address of the ComfyUI server."""
        # Store extra launch arguments as a string
        current_args = await self.config.extra_launch_arguments()
        if current_args:
            new_args = current_args + f" --address {address}"
        else:
            new_args = f"--address {address}"
        await self.config.extra_launch_arguments.set(new_args)
        await self.config.address.set(address)
        await ctx.send(f"ComfyUI address set to: `{address}`")

    @comfy.command(name="set-workflow")
    @app_commands.describe(path="The path to the ComfyUI API workflow JSON file")
    async def set_workflow(self, ctx: commands.Context, path: str = None):
        """
        Sets the path to the ComfyUI API workflow JSON file.
        You can also upload a JSON file as an attachment to this command.
        """
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            if not attachment.filename.endswith(".json"):
                await ctx.send("Please upload a valid JSON file.")
                return

            # Create workflows directory if it doesn't exist
            workflow_dir = cog_data_path(self) / "workflows"
            workflow_dir.mkdir(parents=True, exist_ok=True)

            file_path = workflow_dir / attachment.filename

            try:
                await attachment.save(file_path)
                path = str(file_path)
            except Exception as e:
                await ctx.send(f"Failed to save workflow file: {e}")
                return

        if not path:
            await ctx.send("Please provide a file path or upload a JSON file.")
            return

        await self.config.workflow_file.set(path)
        await ctx.send(f"ComfyUI workflow file path set to: `{path}`")

    @comfy.command(name="add-model")
    @app_commands.describe(
        name="The display name for the model", filename="The filename of the model file"
    )
    async def add_model(self, ctx: commands.Context, name: str, filename: str):
        """Adds a model to the list of available models."""
        async with self.config.models() as models:
            models[name.lower()] = filename
        await ctx.send(f"Model `{name}` with filename `{filename}` has been added.")

    @comfy.command(name="add-lora")
    @app_commands.describe(
        name="The display name for the LoRA",
        filename="The filename of the LoRA file",
        default_weight="The default weight/strength for this LoRA (0.0 to 2.0)",
    )
    async def add_lora(
        self,
        ctx: commands.Context,
        name: str,
        filename: str,
        default_weight: float = 1.0,
    ):
        """Adds a LoRA to the list of available LoRAs with a default weight."""
        if not 0.0 <= default_weight <= 2.0:
            await ctx.send("Default weight must be between 0.0 and 2.0.")
            return

        async with self.config.loras() as loras:
            loras[name.lower()] = filename
        async with self.config.lora_weights() as weights:
            weights[name.lower()] = default_weight
        await ctx.send(
            f"LoRA `{name}` with filename `{filename}` and default weight `{default_weight}` has been added."
        )

    @comfy.command(name="toggle-lora-weight-lock")
    @app_commands.describe(
        locked="Whether to lock LoRA weights to admin-set defaults (true/false)"
    )
    async def toggle_lora_weight_lock(self, ctx: commands.Context, locked: bool):
        """Toggles whether LoRA weights are locked to admin-set defaults for security."""
        await self.config.lora_weight_locked.set(locked)
        status = "locked" if locked else "unlocked"
        await ctx.send(f"LoRA weights are now {status} to admin defaults.")

    @comfy.command(name="set-lora-weight")
    @app_commands.describe(
        lora_name="The name of the LoRA to set weight for",
        weight="The weight/strength for this LoRA (0.0 to 2.0)",
    )
    async def set_lora_weight(
        self, ctx: commands.Context, lora_name: str, weight: float
    ):
        """Sets the default weight for a specific LoRA."""
        if not 0.0 <= weight <= 2.0:
            await ctx.send("Weight must be between 0.0 and 2.0.")
            return

        loras = await self.config.loras()
        if lora_name.lower() not in loras:
            await ctx.send(f"LoRA `{lora_name}` not found.")
            return

        async with self.config.lora_weights() as weights:
            weights[lora_name.lower()] = weight
        await ctx.send(f"Default weight for LoRA `{lora_name}` set to `{weight}`.")

    @comfy.command(name="add-embedding")
    @app_commands.describe(
        name="The display name for the embedding",
        filename="The filename of the embedding file",
    )
    async def add_embedding(self, ctx: commands.Context, name: str, filename: str):
        """Adds an embedding to the list of available embeddings."""
        async with self.config.embeddings() as embeddings:
            embeddings[name.lower()] = filename
        await ctx.send(f"Embedding `{name}` with filename `{filename}` has been added.")

    @comfy.command(name="add-lycoris")
    @app_commands.describe(
        name="The display name for the LyCORIS model",
        filename="The filename of the LyCORIS model file",
        default_weight="The default weight/strength for this LyCORIS model (0.0 to 2.0)",
    )
    async def add_lycoris(
        self,
        ctx: commands.Context,
        name: str,
        filename: str,
        default_weight: float = 1.0,
    ):
        """Adds a LyCORIS model to the list of available options."""
        if not 0.0 <= default_weight <= 2.0:
            await ctx.send("Default weight must be between 0.0 and 2.0.")
            return

        async with self.config.lycoris() as lycoris:
            lycoris[name.lower()] = filename
        async with self.config.lycoris_weights() as weights:
            weights[name.lower()] = default_weight
        await ctx.send(
            f"LyCORIS model `{name}` with filename `{filename}` and default weight `{default_weight}` has been added."
        )

    @comfy.command(name="toggle-lycoris-weight-lock")
    @app_commands.describe(
        locked="Whether to lock LyCORIS weights to admin-set defaults (true/false)"
    )
    async def toggle_lycoris_weight_lock(self, ctx: commands.Context, locked: bool):
        """Toggles whether LyCORIS weights are locked to admin-set defaults for security."""
        await self.config.lycoris_weight_locked.set(locked)
        status = "locked" if locked else "unlocked"
        await ctx.send(f"LyCORIS weights are now {status} to admin defaults.")

    @comfy.command(name="set-lycoris-weight")
    @app_commands.describe(
        lycoris_name="The name of the LyCORIS model to set weight for",
        weight="The weight/strength for this LyCORIS model (0.0 to 2.0)",
    )
    async def set_lycoris_weight(
        self, ctx: commands.Context, lycoris_name: str, weight: float
    ):
        """Sets the default weight for a specific LyCORIS model."""
        if not 0.0 <= weight <= 2.0:
            await ctx.send("Weight must be between 0.0 and 2.0.")
            return

        lycoris = await self.config.lycoris()
        if lycoris_name.lower() not in lycoris:
            await ctx.send(f"LyCORIS model `{lycoris_name}` not found.")
            return

        async with self.config.lycoris_weights() as weights:
            weights[lycoris_name.lower()] = weight
        await ctx.send(
            f"Default weight for LyCORIS model `{lycoris_name}` set to `{weight}`."
        )

    @comfy.command(name="set-nsfw-threshold")
    @app_commands.describe(threshold="The NSFW detection threshold (0.0 to 1.0)")
    async def set_nsfw_threshold(self, ctx: commands.Context, threshold: float):
        """Sets the NSFW detection threshold (0.0 to 1.0)."""
        if 0.0 <= threshold <= 1.0:
            await self.config.nsfw_threshold.set(threshold)
            await ctx.send(f"NSFW detection threshold set to `{threshold}`.")
        else:
            await ctx.send("Threshold must be between 0.0 and 1.0.")

    @comfy.command(name="add-nsfw-notification")
    @app_commands.describe(
        user="The user to add to NSFW notification list",
        channel="The channel where NSFW notifications will be sent",
    )
    async def add_nsfw_notification(
        self, ctx: commands.Context, user: discord.Member, channel: discord.TextChannel
    ):
        """Adds a user to the NSFW notification list and sets the notification channel."""
        # Check if user has permission (bot owner or guild owner)
        if not (await ctx.bot.is_owner(ctx.author) or ctx.author == ctx.guild.owner):
            await ctx.send(
                "You must be the bot owner or guild owner to use this command."
            )
            return

        async with self.config.nsfw_notification_users() as users:
            if user.id not in users:
                users.append(user.id)
            else:
                await ctx.send(
                    f"{user.mention} is already in the NSFW notification list."
                )
                return

        await self.config.nsfw_notification_channel.set(channel.id)
        await ctx.send(
            f"Added {user.mention} to NSFW notification list. Notifications will be sent to {channel.mention}."
        )

    @comfy.command(name="remove-nsfw-notification")
    @app_commands.describe(user="The user to remove from NSFW notification list")
    async def remove_nsfw_notification(
        self, ctx: commands.Context, user: discord.Member
    ):
        """Removes a user from the NSFW notification list."""
        # Check if user has permission (bot owner or guild owner)
        if not (await ctx.bot.is_owner(ctx.author) or ctx.author == ctx.guild.owner):
            await ctx.send(
                "You must be the bot owner or guild owner to use this command."
            )
            return

        async with self.config.nsfw_notification_users() as users:
            if user.id in users:
                users.remove(user.id)
                await ctx.send(
                    f"Removed {user.mention} from the NSFW notification list."
                )
            else:
                await ctx.send(f"{user.mention} is not in the NSFW notification list.")

    @comfy.command(name="set-admin-log-channel")
    @app_commands.describe(channel="The channel where user command logs will be sent")
    async def set_admin_log_channel(
        self, ctx: commands.Context, channel: discord.TextChannel
    ):
        """Sets the channel where user command logs will be sent for security monitoring."""
        await self.config.admin_log_channel.set(channel.id)
        await ctx.send(f"Admin log channel set to {channel.mention}.")

    @comfy.command(name="toggle-command-logging")
    @app_commands.describe(
        enabled="Whether to enable or disable command logging (true/false)"
    )
    async def toggle_command_logging(self, ctx: commands.Context, enabled: bool):
        """Toggles whether user commands are logged for security reasons."""
        await self.config.log_user_commands.set(enabled)
        status = "enabled" if enabled else "disabled"
        await ctx.send(f"Command logging has been {status}.")

    @comfy.command(name="list-nsfw-notifications")
    async def list_nsfw_notifications(self, ctx: commands.Context):
        """Lists all users in the NSFW notification list and the notification channel."""
        users = await self.config.nsfw_notification_users()
        channel_id = await self.config.nsfw_notification_channel()

        if not users and not channel_id:
            await ctx.send("No NSFW notifications are configured.")
            return

        embed = discord.Embed(
            title="NSFW Notification Settings", color=discord.Color.blue()
        )

        if channel_id:
            channel = ctx.guild.get_channel(channel_id)
            if channel:
                embed.add_field(
                    name="Notification Channel", value=channel.mention, inline=False
                )
            else:
                embed.add_field(
                    name="Notification Channel", value="Channel not found", inline=False
                )

        if users:
            user_mentions = []
            for user_id in users:
                user = ctx.guild.get_member(user_id)
                if user:
                    user_mentions.append(user.mention)
                else:
                    user_mentions.append(f"<@{user_id}> (User not found)")

            embed.add_field(
                name="Notified Users", value="\n".join(user_mentions), inline=False
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="generate")
        await ctx.send(f"Default weight for LoRA `{lora_name}` set to `{weight}`.")

    @comfy.command(name="add-embedding")
    @app_commands.describe(
        name="The display name for the embedding",
        filename="The filename of the embedding file",
    )
    async def add_embedding(self, ctx: commands.Context, name: str, filename: str):
        """Adds an embedding to the list of available embeddings."""
        async with self.config.embeddings() as embeddings:
            embeddings[name.lower()] = filename
        await ctx.send(f"Embedding `{name}` with filename `{filename}` has been added.")

    @comfy.command(name="add-lycoris")
    @app_commands.describe(
        name="The display name for the LyCORIS model",
        filename="The filename of the LyCORIS model file",
        default_weight="The default weight/strength for this LyCORIS model (0.0 to 2.0)",
    )
    async def add_lycoris(
        self,
        ctx: commands.Context,
        name: str,
        filename: str,
        default_weight: float = 1.0,
    ):
        """Adds a LyCORIS model to the list of available options."""
        if not 0.0 <= default_weight <= 2.0:
            await ctx.send("Default weight must be between 0.0 and 2.0.")
            return

        async with self.config.lycoris() as lycoris:
            lycoris[name.lower()] = filename
        async with self.config.lycoris_weights() as weights:
            weights[name.lower()] = default_weight
        await ctx.send(
            f"LyCORIS model `{name}` with filename `{filename}` and default weight `{default_weight}` has been added."
        )

    @comfy.command(name="toggle-lycoris-weight-lock")
    @app_commands.describe(
        locked="Whether to lock LyCORIS weights to admin-set defaults (true/false)"
    )
    async def toggle_lycoris_weight_lock(self, ctx: commands.Context, locked: bool):
        """Toggles whether LyCORIS weights are locked to admin-set defaults for security."""
        await self.config.lycoris_weight_locked.set(locked)
        status = "locked" if locked else "unlocked"
        await ctx.send(f"LyCORIS weights are now {status} to admin defaults.")

    @comfy.command(name="set-lycoris-weight")
    @app_commands.describe(
        lycoris_name="The name of the LyCORIS model to set weight for",
        weight="The weight/strength for this LyCORIS model (0.0 to 2.0)",
    )
    async def set_lycoris_weight(
        self, ctx: commands.Context, lycoris_name: str, weight: float
    ):
        """Sets the default weight for a specific LyCORIS model."""
        if not 0.0 <= weight <= 2.0:
            await ctx.send("Weight must be between 0.0 and 2.0.")
            return

        lycoris = await self.config.lycoris()
        if lycoris_name.lower() not in lycoris:
            await ctx.send(f"LyCORIS model `{lycoris_name}` not found.")
            return

        async with self.config.lycoris_weights() as weights:
            weights[lycoris_name.lower()] = weight
        await ctx.send(
            f"Default weight for LyCORIS model `{lycoris_name}` set to `{weight}`."
        )

    @comfy.command(name="set-nsfw-threshold")
    @app_commands.describe(threshold="The NSFW detection threshold (0.0 to 1.0)")
    async def set_nsfw_threshold(self, ctx: commands.Context, threshold: float):
        """Sets the NSFW detection threshold (0.0 to 1.0)."""
        if 0.0 <= threshold <= 1.0:
            await self.config.nsfw_threshold.set(threshold)
            await ctx.send(f"NSFW detection threshold set to `{threshold}`.")
        else:
            await ctx.send("Threshold must be between 0.0 and 1.0.")

    @comfy.command(name="add-nsfw-notification")
    @app_commands.describe(
        user="The user to add to NSFW notification list",
        channel="The channel where NSFW notifications will be sent",
    )
    async def add_nsfw_notification(
        self, ctx: commands.Context, user: discord.Member, channel: discord.TextChannel
    ):
        """Adds a user to the NSFW notification list and sets the notification channel."""
        # Check if user has permission (bot owner or guild owner)
        if not (await ctx.bot.is_owner(ctx.author) or ctx.author == ctx.guild.owner):
            await ctx.send(
                "You must be the bot owner or guild owner to use this command."
            )
            return

        async with self.config.nsfw_notification_users() as users:
            if user.id not in users:
                users.append(user.id)
            else:
                await ctx.send(
                    f"{user.mention} is already in the NSFW notification list."
                )
                return

        await self.config.nsfw_notification_channel.set(channel.id)
        await ctx.send(
            f"Added {user.mention} to NSFW notification list. Notifications will be sent to {channel.mention}."
        )

    @comfy.command(name="remove-nsfw-notification")
    @app_commands.describe(user="The user to remove from NSFW notification list")
    async def remove_nsfw_notification(
        self, ctx: commands.Context, user: discord.Member
    ):
        """Removes a user from the NSFW notification list."""
        # Check if user has permission (bot owner or guild owner)
        if not (await ctx.bot.is_owner(ctx.author) or ctx.author == ctx.guild.owner):
            await ctx.send(
                "You must be the bot owner or guild owner to use this command."
            )
            return

        async with self.config.nsfw_notification_users() as users:
            if user.id in users:
                users.remove(user.id)
                await ctx.send(
                    f"Removed {user.mention} from the NSFW notification list."
                )
            else:
                await ctx.send(f"{user.mention} is not in the NSFW notification list.")

    @comfy.command(name="set-admin-log-channel")
    @app_commands.describe(channel="The channel where user command logs will be sent")
    async def set_admin_log_channel(
        self, ctx: commands.Context, channel: discord.TextChannel
    ):
        """Sets the channel where user command logs will be sent for security monitoring."""
        await self.config.admin_log_channel.set(channel.id)
        await ctx.send(f"Admin log channel set to {channel.mention}.")

    @comfy.command(name="toggle-command-logging")
    @app_commands.describe(
        enabled="Whether to enable or disable command logging (true/false)"
    )
    async def toggle_command_logging(self, ctx: commands.Context, enabled: bool):
        """Toggles whether user commands are logged for security reasons."""
        await self.config.log_user_commands.set(enabled)
        status = "enabled" if enabled else "disabled"
        await ctx.send(f"Command logging has been {status}.")

    @comfy.command(name="list-nsfw-notifications")
    async def list_nsfw_notifications(self, ctx: commands.Context):
        """Lists all users in the NSFW notification list and the notification channel."""
        users = await self.config.nsfw_notification_users()
        channel_id = await self.config.nsfw_notification_channel()

        if not users and not channel_id:
            await ctx.send("No NSFW notifications are configured.")
            return

        embed = discord.Embed(
            title="NSFW Notification Settings", color=discord.Color.blue()
        )

        if channel_id:
            channel = ctx.guild.get_channel(channel_id)
            if channel:
                embed.add_field(
                    name="Notification Channel", value=channel.mention, inline=False
                )
            else:
                embed.add_field(
                    name="Notification Channel", value="Channel not found", inline=False
                )

        if users:
            user_mentions = []
            for user_id in users:
                user = ctx.guild.get_member(user_id)
                if user:
                    user_mentions.append(user.mention)
                else:
                    user_mentions.append(f"<@{user_id}> (User not found)")

            embed.add_field(
                name="Notified Users", value="\n".join(user_mentions), inline=False
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="generate")
    @commands.cooldown(1, 60, commands.BucketType.user)
    @app_commands.describe(
        model="The model to use for generation",
        prompt="The prompt describing what to generate",
    )
    async def generate(self, ctx: commands.Context, model: str, *, prompt: str):
        """
        Generates an image with a specified model and prompt.

        Use quotes for multi-word prompts.
        To add a LoRA, include `lora:lora_name:strength` in your prompt.
        Example: `[p]generate sd-xl a beautiful landscape lora:more_details:0.8`
        """
        # Command logging for security
        log_user_commands = await self.config.log_user_commands()
        admin_log_channel_id = await self.config.admin_log_channel()

        if log_user_commands and admin_log_channel_id:
            admin_channel = ctx.guild.get_channel(admin_log_channel_id)
            if admin_channel:
                embed = discord.Embed(
                    title="User Command Log",
                    description=f"**User:** {ctx.author.mention} ({ctx.author.name}#{ctx.author.discriminator})\n"
                    f"**Channel:** {ctx.channel.mention}\n"
                    f"**Model:** {model}\n"
                    f"**Prompt:** {prompt}",
                    color=discord.Color.blue(),
                    timestamp=ctx.message.created_at,
                )
                embed.set_footer(text=f"User ID: {ctx.author.id}")
                await admin_channel.send(embed=embed)

        # Basic validation before queuing
        address = await self.config.address()
        workflow_file = await self.config.workflow_file()
        if not address or not workflow_file:
            await ctx.send(
                "The ComfyUI address and workflow file must be set by the bot owner."
            )
            return

        models = await self.config.models()
        if model.lower() not in models:
            await ctx.send(
                f"Model `{model}` not found. Available models: {', '.join(models.keys())}"
            )
            return

        # Add to queue
        try:
            self.queue.put_nowait((ctx, prompt, model))
            await ctx.send(f"⏳ Added to queue. Position: {self.queue.qsize()}")
        except asyncio.QueueFull:
            await ctx.send("The queue is currently full. Please try again later.")
