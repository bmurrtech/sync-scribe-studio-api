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
import json
import base64
import logging
from google.oauth2 import service_account
from google.cloud import storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GCS environment variables
GCP_BUCKET_NAME = os.getenv('GCP_BUCKET_NAME')
STORAGE_PATH = "/tmp/"
gcs_client = None

def initialize_gcp_client():
    # Try multiple ways to get GCP credentials
    GCP_SA_CREDENTIALS = os.getenv('GCP_SA_CREDENTIALS')
    GCP_SA_KEY_BASE64 = os.getenv('GCP_SA_KEY_BASE64')
    
    credentials_json = None
    
    # First try GCP_SA_CREDENTIALS (direct JSON)
    if GCP_SA_CREDENTIALS:
        try:
            # Check if it's already valid JSON
            credentials_json = GCP_SA_CREDENTIALS
            json.loads(credentials_json)  # Validate it's proper JSON
        except json.JSONDecodeError:
            logger.warning("GCP_SA_CREDENTIALS is not valid JSON")
            credentials_json = None
    
    # If no direct credentials, try base64 encoded
    if not credentials_json and GCP_SA_KEY_BASE64:
        try:
            # Decode base64 to get JSON string
            credentials_json = base64.b64decode(GCP_SA_KEY_BASE64).decode('utf-8')
            json.loads(credentials_json)  # Validate it's proper JSON
            logger.info("Using base64 decoded GCP credentials")
        except Exception as e:
            logger.warning(f"Failed to decode GCP_SA_KEY_BASE64: {e}")
            credentials_json = None
    
    if not credentials_json:
        logger.warning("No valid GCP credentials found. Skipping GCS client initialization.")
        return None

    # Define the required scopes for Google Cloud Storage
    GCS_SCOPES = ['https://www.googleapis.com/auth/devstorage.full_control']

    try:
        credentials_info = json.loads(credentials_json)
        gcs_credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=GCS_SCOPES
        )
        logger.info("Successfully initialized GCS client")
        return storage.Client(credentials=gcs_credentials)
    except Exception as e:
        logger.error(f"Failed to initialize GCS client: {e}")
        return None

# Initialize the GCS client
gcs_client = initialize_gcp_client()

def upload_to_gcs(file_path, bucket_name=GCP_BUCKET_NAME):
    if not gcs_client:
        raise ValueError("GCS client is not initialized. Skipping file upload.")

    try:
        logger.info(f"Uploading file to Google Cloud Storage: {file_path}")
        bucket = gcs_client.bucket(bucket_name)
        blob = bucket.blob(os.path.basename(file_path))
        blob.upload_from_filename(file_path)
        logger.info(f"File uploaded successfully to GCS: {blob.public_url}")
        return blob.public_url
    except Exception as e:
        logger.error(f"Error uploading file to GCS: {e}")
        raise
