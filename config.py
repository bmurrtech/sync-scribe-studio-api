# Copyright (c) 2025 Stephen G. Pope
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
import logging

# Configure logging for better debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_api_key():
    """Helper function to get the API key.
    
    This function checks for API keys in the following order:
    1. X_API_KEY environment variable (primary)
    2. API_KEY environment variable (fallback)
    
    Returns:
        str or None: The API key if available, None otherwise.
    """
    return os.getenv('X_API_KEY') or os.getenv('API_KEY')


# Retrieve the API key from environment variables
# This is done at module level for backward compatibility
API_KEY = get_api_key()
if not API_KEY:
    logger.warning(
        "X_API_KEY environment variable is not set. "
        "Some features may not work properly. "
        "Please set X_API_KEY or API_KEY environment variable."
    )

# Storage path setting
LOCAL_STORAGE_PATH = os.environ.get('LOCAL_STORAGE_PATH', '/tmp')

# GCP environment variables
GCP_SA_CREDENTIALS = os.environ.get('GCP_SA_CREDENTIALS', '')
GCP_BUCKET_NAME = os.environ.get('GCP_BUCKET_NAME', '')

def validate_env_vars(provider):

    """ Validate the necessary environment variables for the selected storage provider """
    required_vars = {
        'GCP': ['GCP_BUCKET_NAME', 'GCP_SA_CREDENTIALS'],
        'S3': ['S3_ENDPOINT_URL', 'S3_ACCESS_KEY', 'S3_SECRET_KEY', 'S3_BUCKET_NAME', 'S3_REGION'],
        'S3_DO': ['S3_ENDPOINT_URL', 'S3_ACCESS_KEY', 'S3_SECRET_KEY']
    }
    
    missing_vars = [var for var in required_vars[provider] if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing environment variables for {provider} storage: {', '.join(missing_vars)}")
