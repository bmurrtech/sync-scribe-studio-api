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



import os
import uuid
import requests
from urllib.parse import urlparse, parse_qs
import mimetypes

def get_extension_from_url(url):
    """Extract file extension from URL or content type.
    
    Args:
        url (str): The URL to extract the extension from
        
    Returns:
        str: The file extension including the dot (e.g., '.jpg')
        
    Raises:
        ValueError: If no valid extension can be determined from the URL or content type
    """
    # First try to get extension from URL
    parsed_url = urlparse(url)
    path = parsed_url.path
    if path:
        ext = os.path.splitext(path)[1].lower()
        if ext and ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.mp4', '.avi', '.mov', '.mp3', '.wav', '.m4a']:
            return ext

    # Check for common placeholder services
    if 'placeholder' in url.lower():
        # Default to PNG for placeholder images
        return '.png'
    
    # If no extension in URL, try to determine from content type
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; API-Client/1.0; +http://example.com/bot)'}
    try:
        response = requests.head(url, allow_redirects=True, timeout=5, headers=headers)
        content_type = response.headers.get('content-type', '').split(';')[0].strip()
        
        # Map common content types to extensions
        content_type_map = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'image/bmp': '.bmp',
            'video/mp4': '.mp4',
            'video/mpeg': '.mpeg',
            'video/quicktime': '.mov',
            'audio/mpeg': '.mp3',
            'audio/mp3': '.mp3',
            'audio/wav': '.wav',
            'audio/x-wav': '.wav',
            'audio/mp4': '.m4a',
        }
        
        if content_type in content_type_map:
            return content_type_map[content_type]
        
        # Fallback to mimetypes
        ext = mimetypes.guess_extension(content_type)
        if ext:
            return ext.lower()
    except Exception as e:
        # If HEAD request fails, try GET with range header
        try:
            response = requests.get(url, headers={'Range': 'bytes=0-0'}, timeout=5)
            content_type = response.headers.get('content-type', '').split(';')[0].strip()
            if 'image' in content_type:
                return '.jpg'  # Default to jpg for images
            elif 'video' in content_type:
                return '.mp4'  # Default to mp4 for videos
        except:
            pass

    # Last resort defaults based on URL patterns
    if any(img in url.lower() for img in ['image', 'img', 'photo', 'picture']):
        return '.jpg'
    elif any(vid in url.lower() for vid in ['video', 'vid', 'movie']):
        return '.mp4'
    elif any(aud in url.lower() for aud in ['audio', 'sound', 'music']):
        return '.mp3'
    
    # If we still can't determine the extension, default to .bin
    # This allows the download to proceed and the actual file type can be determined later
    return '.bin'

def download_file(url, storage_path="/tmp/"):
    """Download a file from URL to local storage."""
    # Create storage directory if it doesn't exist
    os.makedirs(storage_path, exist_ok=True)
    
    file_id = str(uuid.uuid4())
    extension = get_extension_from_url(url)
    local_filename = os.path.join(storage_path, f"{file_id}{extension}")

    headers = {'User-Agent': 'Mozilla/5.0 (compatible; API-Client/1.0; +http://example.com/bot)'}
    try:
        response = requests.get(url, stream=True, headers=headers)
        response.raise_for_status()

        with open(local_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        return local_filename
    except Exception as e:
        if os.path.exists(local_filename):
            os.remove(local_filename)
        raise e

