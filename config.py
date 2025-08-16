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
import logging

# Retrieve the API key from environment variables
API_KEY = os.environ.get('API_KEY')
if not API_KEY:
    raise ValueError("API_KEY environment variable is not set")

# Storage path setting
LOCAL_STORAGE_PATH = os.environ.get('LOCAL_STORAGE_PATH', '/tmp')

# GCP environment variables
GCP_SA_CREDENTIALS = os.environ.get('GCP_SA_CREDENTIALS', '')
GCP_BUCKET_NAME = os.environ.get('GCP_BUCKET_NAME', '')

# Feature Flags
# ASR (Automatic Speech Recognition) Configuration
# Faster-Whisper is now the default ASR backend for better performance
# To use legacy OpenAI Whisper, explicitly set ENABLE_OPENAI_WHISPER=true
ENABLE_OPENAI_WHISPER = os.environ.get('ENABLE_OPENAI_WHISPER', 'false').lower() == 'true'

# Faster-Whisper ASR Settings
# Optimized defaults based on CPU vs GPU performance best practices
ASR_MODEL_ID = os.environ.get('ASR_MODEL_ID', 'openai/whisper-small')  # Better accuracy/performance balance than base
ASR_DEVICE = os.environ.get('ASR_DEVICE', 'auto')  # Options: 'cpu', 'cuda', 'auto'
ASR_COMPUTE_TYPE = os.environ.get('ASR_COMPUTE_TYPE', 'auto')  # Options: 'int8', 'int8_float32', 'float16', 'float32', 'auto'
ASR_BEAM_SIZE = int(os.environ.get('ASR_BEAM_SIZE', '1'))  # Reduced from 5 to 1 for speed optimization

# Performance-optimized batch sizes and threading
_default_batch_size = '8' if ASR_DEVICE == 'cpu' else '16' if ASR_DEVICE != 'auto' else '12'  # Increased for better GPU utilization
ASR_BATCH_SIZE = int(os.environ.get('ASR_BATCH_SIZE', _default_batch_size))  # Batch size for processing
ASR_NUM_WORKERS = int(os.environ.get('ASR_NUM_WORKERS', '2'))  # Audio loading workers (CPU threads)
ASR_CACHE_DIR = os.environ.get('ASR_CACHE_DIR', os.path.join(LOCAL_STORAGE_PATH, 'asr_cache'))

def validate_env_vars(provider):

    """ Validate the necessary environment variables for the selected storage provider """
    if provider == 'GCP':
        # For GCP, we need bucket name and either GCP_SA_CREDENTIALS or GCP_SA_KEY_BASE64
        if not os.getenv('GCP_BUCKET_NAME'):
            raise ValueError(f"Missing environment variable for GCP storage: GCP_BUCKET_NAME")
        if not os.getenv('GCP_SA_CREDENTIALS') and not os.getenv('GCP_SA_KEY_BASE64'):
            raise ValueError(f"Missing environment variables for GCP storage: GCP_SA_CREDENTIALS or GCP_SA_KEY_BASE64")
        return  # Valid GCP config
    
    required_vars = {
        'S3': ['S3_ENDPOINT_URL', 'S3_ACCESS_KEY', 'S3_SECRET_KEY', 'S3_BUCKET_NAME', 'S3_REGION'],
        'S3_DO': ['S3_ENDPOINT_URL', 'S3_ACCESS_KEY', 'S3_SECRET_KEY']
    }
    
    if provider in required_vars:
        missing_vars = [var for var in required_vars[provider] if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing environment variables for {provider} storage: {', '.join(missing_vars)}")
