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
from flask import Blueprint, current_app
from app_utils import validate_payload, queue_task_wrapper
import logging
from services.v1.media.convert.audio_to_m4b import process_audio_to_m4b
from services.authentication import authenticate
from services.cloud_storage import upload_file
import os

v1_audio_to_m4b_bp = Blueprint('v1_audio_to_m4b', __name__)
logger = logging.getLogger(__name__)


@v1_audio_to_m4b_bp.route('/v1/media/convert/audio_to_m4b', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "media_url": {"type": "string", "format": "uri"},
        "metadata": {"type": "object"},
        "audio_options": {"type": "object"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["media_url"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def convert_audio_to_m4b(job_id, data):
    """
    Handles both synchronous (no webhook_url) and asynchronous (with webhook_url) requests.
    If webhook_url is present, the existing async/queued pattern applies (the wrapper will manage queuing).
    If webhook_url is omitted, the request is processed synchronously and returns a JSON response
    consistent with other media endpoints.
    """
    media_url = data['media_url']
    metadata = data.get('metadata')
    audio_options = data.get('audio_options')
    webhook_url = data.get('webhook_url')
    client_id = data.get('id')

    logger.info(f"Job {job_id}: Received audio-to-m4b request for media URL: {media_url}")

    try:
        output_file = process_audio_to_m4b(media_url, job_id, metadata=metadata, audio_options=audio_options, webhook_url=webhook_url)
        logger.info(f"Job {job_id}: Audio to M4B conversion completed successfully: {output_file}")
 
        cloud_url = upload_file(output_file)
        logger.info(f"Job {job_id}: Converted M4B uploaded to cloud storage: {cloud_url}")
 
        # Build a consistent response payload (suitable for sync responses when no webhook is provided)
        response_payload = {
            "file_url": cloud_url,
            "duration": None,  # Duration can be added later via ffprobe/chapter parsing
            "format_info": {
                "bitrate": audio_options.get("bitrate", "64k") if audio_options else "64k",
                "channels": int(audio_options.get("channels", 1)) if audio_options else 1,
                "sample_rate": int(audio_options.get("sample_rate", 44100)) if audio_options else 44100
            }
        }
 
        return response_payload, "/v1/media/convert/audio_to_m4b", 200
 
    except Exception as e:
        logger.error(f"Job {job_id}: Error during audio to m4b conversion - {str(e)}")
        return {"error": str(e)}, "/v1/media/convert/audio_to_m4b", 500