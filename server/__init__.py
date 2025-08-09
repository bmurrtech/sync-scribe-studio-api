"""
Server package initialization
Loads dotenv early to ensure environment variables are available
"""

from dotenv import load_dotenv

# Load environment variables early at package import
load_dotenv()
