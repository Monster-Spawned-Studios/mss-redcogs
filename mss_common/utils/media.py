"""
Copyright (c) 2025 Monster Spawned Studios | https://monsterspawned.studio | All rights reserved.
"""

import os
import subprocess

from redbot.core import commands
from redbot.core.bot import Red
from yt_dlp import YoutubeDL
from yt_dlp.postprocessor import ffmpeg
from yt_dlp.utils import DownloadError


class MSSUtilsMedia(commands.Cog):
    """
    A common media utility library for Monster Spawned Studios cogs.
    """

    def __init__(self, bot: Red):
        """
        Initialize the MSSUtilsMedia class.
        """
        self.bot = bot
        self.logger = getattr(self.bot, "log", None)
        self.embed_subtitles = False
        # Set the default subtitles language to English, and default it to `en` if not provided
        self.subtitles_language = ""
        if self.subtitles_language not in ["en", "en-US", "de", "de-DE", "fr", "fr-FR", "es", "es-ES", "it", "it-IT", "ja", "ja-JP", "ko", "ko-KR", "pt", "pt-PT", "ru", "ru-RU", "zh", "zh-CN", "zh-TW"]:
            self.logger.warning(
                f"Invalid subtitles language provided: {self.subtitles_language}. Defaulting to English.")
            self.subtitles_language = "en"
        # Set the default audio region to United States, and default it to `US` if not provided
        self.audio_region = ""
        if self.audio_region not in ["US", "CA", "GB", "AU", "NZ", "IE", "ZA", "IN", "CN", "JP", "KR", "TW", "HK", "SG", "MY", "PH", "TH", "VN", "ID"]:
            self.logger.warning(
                f"Invalid audio region provided: {self.audio_region}. Defaulting to United States.")
            self.audio_region = "US"
        # Set the default download format to the best available format, and default it to `mp4` if not provided
        self.download_format = "mp4"
        if self.download_format not in ["mp4", "webm", "flac", "m4a", "opus", "aac", "ogg", "wav", "mp3"]:
            self.logger.warning(
                f"Invalid download format provided: {self.download_format}. Defaulting to mp4.")
            self.download_format = "mp4"
        # Set the default download quality to the best available quality, and default it to `best` if not provided
        self.video_download_quality = "best"
        if self.video_download_quality not in ["best", "worst", "144p", "240p", "360p", "480p", "720p", "1080p", "1440p", "2160p", "4320p"]:
            self.logger.warning(
                f"Invalid video download quality provided: {self.video_download_quality}. Defaulting to best.")
            self.video_download_quality = "best"
        # Set the default audio download format to the best available format, and default it to `flac` if not provided
        self.audio_download_format = ""
        if self.audio_download_format not in ["flac", "m4a", "opus", "aac", "ogg", "wav", "mp3"]:
            self.logger.warning(
                f"Invalid audio download format provided: {self.audio_download_format}. Defaulting to flac.")
            self.audio_download_format = "flac"
        # Set the default audio download quality to the best available quality, and default it to `best` if not provided
        self.audio_download_quality = ""
        if self.audio_download_quality not in ["best", "worst", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            self.logger.warning(
                f"Invalid audio download quality provided: {self.audio_download_quality}. Defaulting to best.")
            self.audio_download_quality = "best"
        if self.audio_download_quality == "best":
            self.audio_download_quality = 0
        elif self.audio_download_quality == "worst":
            self.audio_download_quality = 9
        # Set the default download format to the best available format, and default it to `mp4` if not provided
        self.ytdl_opts = {
            "outtmpl": "%(title)s.%(ext)s",
            "noplaylist": True,
            "noprogress": True,
            "nocolor": True,
            "quiet": True,
            "retries": 3,
            "subtitleslangs": [self.subtitles_language],
            "audio_region": self.audio_region,
            "embed_subtitles": self.embed_subtitles,
            "format_sort": ["res", "ext"],
            "format_sort_force": ["res", "ext"],
            "prefer_free_formats": True,
            "allow_unplayable_formats": False,
            "format": self.download_format,
            "quality": self.video_download_quality,
            "audio_format": self.audio_download_format,
            "audio_quality": self.audio_download_quality,
        }
        self.ytdl = YoutubeDL(self.ytdl_opts)

    async def get_youtube_video_info(self, url: str) -> dict:
        """
        Get information about a YouTube video.
        """
        try:
            with self.ytdl as ydl:
                return ydl.extract_info(url, download=False)
        except DownloadError as e:
            self.logger.error(f"Error getting YouTube video info: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting YouTube video info: {e}")
            return None

    async def get_youtube_video_thumbnail_url(self, url: str) -> str:
        """
        Get the thumbnail URL of a YouTube video.
        """
        try:
            with self.ytdl as ydl:
                thumbnail_url = ydl.extract_info(url, download=False)[
                    "thumbnails"][-1]["url"]
                return thumbnail_url
        except DownloadError as e:
            self.logger.error(f"Error getting YouTube video thumbnail: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting YouTube video thumbnail: {e}")
            return None

    async def get_youtube_video_duration(self, url: str) -> float:
        """
        Get the duration of a YouTube video.
        """
        try:
            with self.ytdl as ydl:
                return float(ydl.extract_info(url, download=False)["duration"])
        except DownloadError as e:
            self.logger.error(f"Error getting YouTube video duration: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting YouTube video duration: {e}")
            return None

    async def get_youtube_video_download_url(self, url: str, quality: str = "best", format: str = "mp4") -> str:
        """
        Get the download URL of a YouTube video.
        """
        try:
            with self.ytdl as ydl:
                # Match the format to the quality and format provided
                for video_format in ydl.extract_info(url, download=False)["formats"]:
                    if video_format["quality"] == quality and video_format["ext"] == format:
                        return video_format["url"]
                return None
        except DownloadError as e:
            self.logger.error(f"Error getting YouTube video download URL: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting YouTube video download URL: {e}")
            return None

    async def get_youtube_audio_download_url(self, url: str, quality: str = "best", format: str = "flac") -> str:
        """
        Get the download URL of a YouTube video's audio track, with an optional quality parameter and file format parameter.
        """
        try:
            with self.ytdl as ydl:
                # Match the format to the quality and format provided
                for audio_format in ydl.extract_info(url, download=False)["formats"]:
                    if audio_format["quality"] == quality and audio_format["ext"] == format:
                        return audio_format["url"]
                return None
        except DownloadError as e:
            self.logger.error(f"Error getting YouTube audio download URL: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting YouTube audio download URL: {e}")
            return None

    async def download_audio_from_video(self, video_url: str = None, audio_format: str = "flac", audio_quality: str = "best") -> str:
        """
        Download an audio file from a video using the ffmpeg library.

        Args:
            video_url (str, optional): The URL of the video to download the audio from. Defaults to None.
            audio_format (str, optional): The format of the audio to download. Defaults to "flac".
            audio_quality (str, optional): The quality of the audio to download. Defaults to "best".

        Returns:
            str: The path to the downloaded audio file.
        """
        try:
            # Set the download format and quality
            self.ytdl_opts["audio_format"] = audio_format
            self.ytdl_opts["audio_quality"] = audio_quality
            with self.ytdl as ydl:
                # Download the audio from the video
                ydl.download([video_url])
                # Get the path to the downloaded audio file
                return ydl.prepare_filename(
                    ydl.extract_info(video_url, download=False))
        except DownloadError as e:
            self.logger.error(f"Error converting video to audio: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error converting video to audio: {e}")
            return None

    async def download_video(self, video_url: str = None, video_format: str = "mp4", video_quality: str = "best") -> str:
        """
        Download a video from a URL using the ffmpeg library.
        """
        try:
            # Set the download format and quality
            self.ytdl_opts["format"] = video_format
            self.ytdl_opts["quality"] = video_quality
            with self.ytdl as ydl:
                ydl.download([video_url])
                return ydl.prepare_filename(ydl.extract_info(video_url, download=False))
        except DownloadError as e:
            self.logger.error(f"Error downloading video: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error downloading video: {e}")
            return None

    async def convert_media_file(self, media_file: str = None, media_format: str = "mp4", media_quality: str = "best") -> str:
        """
        Convert a media file to a different format using the ffmpeg library.

        Args:
            media_file (str, optional): The path to the media file to convert. Defaults to None.
            media_format (str, optional): The format to convert the media file to. Defaults to "mp4".
            media_quality (str, optional): The quality of the media file to convert to. Defaults to "best".

        Returns:
            str: The path to the converted media file.
        """
        # Check if the media quality is valid
        if media_quality == "best":
            media_quality = "320k"
        elif media_quality == "worst":
            media_quality = "64k"
        elif media_quality.isdigit():
            media_quality = str(media_quality) + "k"
        else:
            self.logger.warning(
                f"Invalid media quality provided: {media_quality}. Defaulting to best.")
            media_quality = "320k"

        # Check if the media format is valid
        if media_format not in ["mp4", "webm", "mkv", "flac", "m4a", "opus", "aac", "ogg", "wav", "mp3"]:
            self.logger.warning(
                f"Invalid media format provided: {media_format}. Defaulting to mp4.")
            media_format = "mp4"

        # Check if the media file exists
        if media_file == None:
            self.logger.warning(
                "No media file provided. Please provide a media file to convert.")
            return None
        elif not os.path.exists(media_file):
            self.logger.warning(
                f"Media file does not exist: {media_file}. Please provide a valid media file to convert.")
            return None
        elif not os.path.isfile(media_file):
            self.logger.warning(
                f"Media file is not a file: {media_file}. Please provide a valid media file to convert.")
            return None
        elif not os.path.getsize(media_file) > 0:
            self.logger.warning(
                f"Media file is empty: {media_file}. Please provide a valid media file to convert.")
            return None

        # Convert the media file to the new format
        try:
            # Use the ffmpeg library to convert the media file to the new format
            subprocess.run(["ffmpeg", "-i", media_file, "-c:v", "libx264", "-c:a", "aac", "-b:a", media_quality,
                           "-crf", "18", "-preset", "medium", "-movflags", "+faststart", "-f", media_format, media_file])
            return media_file[:-4] + "." + media_format
        except (IOError, subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.error(f"Error converting media file: {e}")
            return None

    async def get_media_file_info(self, media_file: str = None) -> str:
        """
        Get information about a media file.
        """
        try:
            return subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", media_file], capture_output=True, text=True)
        except (IOError, subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.error(f"Error getting media file info: {e}")
            return None
