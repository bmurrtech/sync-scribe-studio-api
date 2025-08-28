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
Minimal M4A conversion service.

Implements:
- download input via services.file_management.download_file
- basic conversion to M4A (AAC codec) using ffmpeg
- metadata injection where provided (artist/title/album/comment/year/genre/publisher/composer)
- sensible audio defaults: 64k bitrate, 1 channel (mono), 44100 Hz sample rate

Note: Cover art embedding and chapter handling are left for Phase 2 (more complex ffmpeg mapping).
"""

import os
import subprocess
import logging
import threading
import time
from services.file_management import download_file
from config import LOCAL_STORAGE_PATH
from app_utils import log_job_status

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _sanitize_metadata_value(val):
    if val is None:
        return None
    # Ensure string and strip problematic newlines
    return str(val).replace("\n", " ").strip()


def process_audio_to_m4a(media_url, job_id, metadata=None, audio_options=None, webhook_url=None):
    """
    Convert an audio file (from URL) to M4A with optional metadata.

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
        str: local path to generated .m4a file

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
    output_filename = f"{job_id}.m4a"
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

    # Add movflags for metadata tags and use mp4 format (m4a as mp4 container)
    cmd.extend(["-movflags", "use_metadata_tags", "-f", "mp4", output_path])

    logger.info(f"Job {job_id}: Running ffmpeg command: {' '.join(cmd)}")

    try:
        # Allow configurable timeout via environment variable or default (900s)
        import os as _os
        timeout_seconds = int(_os.environ.get('AUDIO_CONVERT_TIMEOUT_SEC', '900'))
 
        # Run ffmpeg with progress output to stdout so we can parse progress updates
        progress_cmd = list(cmd) + ["-progress", "pipe:1", "-nostats"]
        logger.info(f"Job {job_id}: Running ffmpeg with progress: {' '.join(progress_cmd)}")
 
        process = subprocess.Popen(
            progress_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
 
        # Thread to parse progress lines from ffmpeg stdout and log job status
        def _parse_progress_lines(stdout_stream):
            buffer = {}
            for raw_line in stdout_stream:
                line = raw_line.strip()
                if line == "":
                    # End of a progress block; process collected keys
                    if buffer:
                        # Build a minimal progress payload
                        try:
                            out_time_ms = int(buffer.get("out_time_ms", "0"))
                            progress_seconds = out_time_ms / 1000000.0
                        except Exception:
                            progress_seconds = None
                        progress_payload = {
                            "progress": buffer.get("progress"),
                            "out_time_ms": buffer.get("out_time_ms"),
                            "time_seconds": progress_seconds,
                            "speed": buffer.get("speed")
                        }
                        # Log job status (non-blocking, write to job status file)
                        try:
                            log_job_status(job_id, {
                                "job_status": "processing",
                                "job_id": job_id,
                                "progress": progress_payload,
                                "response": None
                            })
                        except Exception as e:
                            logger.warning(f"Job {job_id}: Failed to log progress: {e}")
                        buffer = {}
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    buffer[k.strip()] = v.strip()
 
        progress_thread = threading.Thread(target=_parse_progress_lines, args=(process.stdout,))
        progress_thread.daemon = True
        progress_thread.start()
 
        # Monitor process with timeout
        start_time = time.time()
        while True:
            ret = process.poll()
            if ret is not None:
                break
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                logger.error(f"Job {job_id}: FFmpeg exceeded timeout ({timeout_seconds}s), terminating")
                process.terminate()
                try:
                    process.wait(5)
                except Exception:
                    process.kill()
                raise Exception(f"FFmpeg conversion timed out after {timeout_seconds} seconds")
            time.sleep(1)
 
        # Capture remaining output
        try:
            stdout, stderr = process.communicate(timeout=5)
        except Exception:
            stdout, stderr = "", ""
 
        if process.returncode != 0:
            stderr_text = stderr or ""
            raise subprocess.CalledProcessError(process.returncode, progress_cmd, output=stdout, stderr=stderr_text)
 
        logger.info(f"Job {job_id}: ffmpeg completed successfully (returncode 0).")
 
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
        # Defensive handling: mocks may produce CalledProcessError with None fields
        stderr = None
        try:
            if getattr(cpe, "stderr", None):
                stderr = cpe.stderr.decode("utf-8", errors="ignore") if isinstance(cpe.stderr, (bytes, bytearray)) else str(cpe.stderr)
        except Exception:
            stderr = None

        if not stderr:
            rc = getattr(cpe, "returncode", None)
            stderr = f"FFmpeg returned code {rc}"

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