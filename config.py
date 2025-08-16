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

# Performance Profile System
# Options: 'speed', 'accuracy', 'balanced', 'custom'
ASR_PROFILE = os.environ.get('ASR_PROFILE', 'balanced').lower()

# Profile-based configurations
PROFILE_CONFIGS = {
    'speed': {
        'model_id': 'openai/whisper-small',
        'beam_size': 1,
        'best_of': 1,
        'temperature': 0.0,
        'temperature_increment_on_fallback': 0.0,
        'batch_size_cpu': 4,
        'batch_size_gpu': 16,
        'vad_min_silence_ms': 300,  # Aggressive silence detection
        'description': 'Optimized for speed and real-time processing'
    },
    'accuracy': {
        'model_id': 'openai/whisper-large-v3-turbo',  # Use turbo for production accuracy
        'beam_size': 3,
        'best_of': 5,
        'temperature': 0.0,
        'temperature_increment_on_fallback': 0.2,
        'batch_size_cpu': 2,
        'batch_size_gpu': 12,  # Turbo is more VRAM efficient
        'vad_min_silence_ms': 500,  # Conservative silence detection
        'description': 'High accuracy with optimized speed using large-v3-turbo'
    },
    'accuracy-turbo': {
        'model_id': 'openai/whisper-large-v3-turbo',  # Fast + accurate
        'beam_size': 2,  # Slightly reduced for speed
        'best_of': 3,  # Reduced for faster processing
        'temperature': 0.0,
        'temperature_increment_on_fallback': 0.1,
        'batch_size_cpu': 3,
        'batch_size_gpu': 16,  # Higher batch for speed
        'vad_min_silence_ms': 350,  # Faster VAD processing
        'description': 'Maximum speed with large-v3-turbo, best of both worlds'
    },
    'balanced': {
        'model_id': 'openai/whisper-small',
        'beam_size': 2,  # Small increase from beam=1 for better quality
        'best_of': 2,
        'temperature': 0.0,
        'temperature_increment_on_fallback': 0.1,
        'batch_size_cpu': 4,
        'batch_size_gpu': 12,
        'vad_min_silence_ms': 400,  # Balanced silence detection
        'description': 'Good balance of speed and accuracy'
    }
}

# Get profile configuration
_profile_config = PROFILE_CONFIGS.get(ASR_PROFILE, PROFILE_CONFIGS['balanced'])

# Faster-Whisper ASR Settings with profile-based defaults
ASR_MODEL_ID = os.environ.get('ASR_MODEL_ID', _profile_config['model_id'])
ASR_DEVICE = os.environ.get('ASR_DEVICE', 'auto')  # Options: 'cpu', 'cuda', 'auto'
ASR_COMPUTE_TYPE = os.environ.get('ASR_COMPUTE_TYPE', 'auto')  # Options: 'int8', 'int8_float32', 'float16', 'float32', 'auto'
ASR_BEAM_SIZE = int(os.environ.get('ASR_BEAM_SIZE', str(_profile_config['beam_size'])))
ASR_BEST_OF = int(os.environ.get('ASR_BEST_OF', str(_profile_config['best_of'])))
ASR_TEMPERATURE = float(os.environ.get('ASR_TEMPERATURE', str(_profile_config['temperature'])))
ASR_TEMPERATURE_INCREMENT = float(os.environ.get('ASR_TEMPERATURE_INCREMENT_ON_FALLBACK', str(_profile_config['temperature_increment_on_fallback'])))

# Performance-optimized batch sizes and threading based on profile
_device_type = ASR_DEVICE if ASR_DEVICE != 'auto' else 'gpu'  # Assume GPU for auto
_default_batch_size = str(_profile_config[f'batch_size_cpu' if _device_type == 'cpu' else 'batch_size_gpu'])
ASR_BATCH_SIZE = int(os.environ.get('ASR_BATCH_SIZE', _default_batch_size))
ASR_NUM_WORKERS = int(os.environ.get('ASR_NUM_WORKERS', '1'))  # Reduced to 1 for better GPU utilization

# VAD settings from profile
ASR_VAD_MIN_SILENCE_MS = int(os.environ.get('ASR_VAD_MIN_SILENCE_MS', str(_profile_config['vad_min_silence_ms'])))
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
