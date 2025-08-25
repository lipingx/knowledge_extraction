"""
Storage module for Knowledge Extraction App
Provides Firebase integration for storing video segments and knowledge data
"""

from .firebase_config import FirebaseConfig, get_firebase_config, setup_environment_variables
from .firebase_storage import FirebaseStorage, get_storage_client

__all__ = [
    'FirebaseConfig',
    'get_firebase_config', 
    'setup_environment_variables',
    'FirebaseStorage',
    'get_storage_client'
]