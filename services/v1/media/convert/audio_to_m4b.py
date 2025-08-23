# Copyright (c) 2025
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
"""
Minimal M4B conversion service.

Implements:
- download input via services.file_management.download_file
- basic conversion to M4B (AAC codec) using ffmpeg
- metadata injection where provided (artist/title/album/comment/year/genre/publisher/composer)
- sensible audio defaults: 64k bitrate, 1 channel (mono), 44100 Hz sample rate

Note: Cover art embedding and chapter handling are left for Phase 2 (more complex ffmpeg mapping).
"""

import os
import subprocess
import logging
from services.file_management import download_file
from config import LOCAL_STORAGE_PATH

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _sanitize_metadata_value(val):
    if val is None:
        return None
    # Ensure string and strip problematic newlines
    return str(val).replace("\n", " ").strip()


def process_audio_to_m4b(media_url, job_id, metadata=None, audio_options=None, webhook_url=None):
    """
    Convert an audio file (from URL) to M4B with optional metadata.

    Args:
        media_url (str): URL to source audio file
        job_id (str): unique job id used for temp filenames
        metadata (dict, optional): dict of metadata fields. Supported keys:
            artist_name, album, title, comments, cover_url, publication_year,
            genre, publisher, narrator, isbn
        audio_options (dict, optional): dict of audio options. Supported keys:
            bitrate (e.g., '64k'), channels (1 or 2), sample_rate (e.g., 44100)
        webhook_url (str, optional): webhook for reporting (not used here)

    Returns:
        str: local path to generated .m4b file

    Raises:
        Exception on conversion failure
    """
    metadata = metadata or {}
    audio_options = audio_options or {}

    # Defaults per PRD
    bitrate = audio_options.get("bitrate", "64k")
    channels = int(audio_options.get("channels", 1))
    sample_rate = int(audio_options.get("sample_rate", 44100))

    # Download input file
    input_filename = download_file(media_url, os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_input"))
    output_filename = f"{job_id}.m4b"
    output_path = os.path.join(LOCAL_STORAGE_PATH, output_filename)

    # Build ffmpeg command
    # Minimal robust command with metadata injection and movflags for metadata tags
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_filename,
        "-c:a", "aac",
        "-b:a", bitrate,
        "-ac", str(channels),
        "-ar", str(sample_rate),
    ]

    # Inject metadata flags for recognized fields
    # Map provided metadata keys to ffmpeg metadata keys
    metadata_map = {
        "artist_name": "artist",
        "album": "album",
        "title": "title",
        "comments": "comment",
        "publication_year": "year",
        "genre": "genre",
        "publisher": "publisher",
        "narrator": "composer",  # use composer tag for narrator per PRD suggestions
        "isbn": "isbn"
    }

    for key, tag in metadata_map.items():
        val = _sanitize_metadata_value(metadata.get(key))
        if val:
            cmd.extend(["-metadata", f"{tag}={val}"])

    # Add movflags for metadata tags and use mp4 format (m4b as m4a/mp4 container)
    cmd.extend(["-movflags", "use_metadata_tags", "-f", "mp4", output_path])

    logger.info(f"Job {job_id}: Running ffmpeg command: {' '.join(cmd)}")

    try:
        completed = subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"Job {job_id}: ffmpeg completed successfully: stdout={completed.stdout[:200]} stderr={completed.stderr[:200]}")

        # Remove input file to save space
        try:
            if os.path.exists(input_filename):
                os.remove(input_filename)
                logger.info(f"Job {job_id}: Removed input file {input_filename}")
        except Exception as cleanup_err:
            logger.warning(f"Job {job_id}: Failed to remove input file: {cleanup_err}")

        # Verify output exists
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Output file {output_path} not found after conversion")

        return output_path

    except subprocess.CalledProcessError as cpe:
        stderr = cpe.stderr.decode("utf-8", errors="ignore") if cpe.stderr else str(cpe)
        logger.error(f"Job {job_id}: FFmpeg error: {stderr}")
        # Attempt to clean up
        if os.path.exists(input_filename):
            try:
                os.remove(input_filename)
            except Exception:
                pass
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except Exception:
                pass
        raise Exception(f"FFmpeg conversion failed: {stderr}")

    except Exception as e:
        logger.error(f"Job {job_id}: Conversion failed: {str(e)}")
        # Cleanup
        if os.path.exists(input_filename):
            try:
                os.remove(input_filename)
            except Exception:
                pass
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except Exception:
                pass
        raise