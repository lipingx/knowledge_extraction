"""
Firebase Configuration for Knowledge Extraction App
Handles Firebase Admin SDK initialization and configuration
"""

import os
import json
from typing import Dict, Any
import firebase_admin
from firebase_admin import credentials, firestore, storage
from google.cloud.firestore import Client


class FirebaseConfig:
    """Manages Firebase configuration and initialization"""
    
    def __init__(self, credentials_path: str = None, project_id: str = None):
        """
        Initialize Firebase configuration
        
        Args:
            credentials_path: Path to service account key JSON file
            project_id: Firebase project ID (optional if in credentials)
        """
        self.project_id = project_id or "knowledgeextraction-e9429"
        self.credentials_path = credentials_path
        self.app = None
        self.db = None
        self.storage_bucket = None
        
    def initialize_firebase(self) -> bool:
        """
        Initialize Firebase Admin SDK
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if Firebase is already initialized
            if firebase_admin._apps:
                self.app = firebase_admin.get_app()
                print("Firebase already initialized")
            else:
                # Initialize Firebase Admin SDK
                if self.credentials_path and os.path.exists(self.credentials_path):
                    # Use service account key file
                    cred = credentials.Certificate(self.credentials_path)
                    self.app = firebase_admin.initialize_app(cred, {
                        'projectId': self.project_id,
                        'storageBucket': f'{self.project_id}.firebasestorage.app'
                    })
                else:
                    # Use default credentials (for Google Cloud environment)
                    cred = credentials.ApplicationDefault()
                    self.app = firebase_admin.initialize_app(cred, {
                        'projectId': self.project_id,
                        'storageBucket': f'{self.project_id}.firebasestorage.app'
                    })
                
                print(f"Firebase initialized for project: {self.project_id}")
            
            # Initialize Firestore client
            self.db = firestore.client()
            
            # Initialize Storage bucket
            self.storage_bucket = storage.bucket()
            
            return True
            
        except Exception as e:
            print(f"Failed to initialize Firebase: {e}")
            return False
    
    def get_firestore_client(self) -> Client:
        """
        Get Firestore client instance
        
        Returns:
            Client: Firestore client
        """
        if not self.db:
            self.initialize_firebase()
        return self.db
    
    def get_storage_bucket(self):
        """
        Get Firebase Storage bucket instance
        
        Returns:
            Bucket: Storage bucket
        """
        if not self.storage_bucket:
            self.initialize_firebase()
        return self.storage_bucket
    
    def test_connection(self) -> bool:
        """
        Test Firebase connection
        
        Returns:
            bool: True if connection successful
        """
        try:
            # Test Firestore connection
            collections = list(self.db.collections())
            print(f"Successfully connected to Firestore. Found {len(collections)} collections.")
            
            # Test Storage connection
            bucket_name = self.storage_bucket.name
            print(f"Successfully connected to Storage bucket: {bucket_name}")
            
            return True
            
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False


# Global Firebase config instance
firebase_config = None

def get_firebase_config(credentials_path: str = None) -> FirebaseConfig:
    """
    Get or create Firebase configuration instance
    
    Args:
        credentials_path: Path to service account key file
        
    Returns:
        FirebaseConfig: Firebase configuration instance
    """
    global firebase_config
    
    if firebase_config is None:
        firebase_config = FirebaseConfig(credentials_path)
        firebase_config.initialize_firebase()
    
    return firebase_config


# Environment variable names for configuration
ENV_VARS = {
    'FIREBASE_CREDENTIALS_PATH': 'Path to Firebase service account key file',
    'FIREBASE_PROJECT_ID': 'Firebase project ID',
    'GOOGLE_APPLICATION_CREDENTIALS': 'Google Cloud credentials (alternative to FIREBASE_CREDENTIALS_PATH)'
}


def setup_environment_variables():
    """Print instructions for setting up environment variables"""
    print("Firebase Environment Variables Setup:")
    print("=" * 50)
    
    for var, description in ENV_VARS.items():
        current_value = os.getenv(var, 'Not set')
        print(f"{var}: {description}")
        print(f"  Current value: {current_value}")
        print()
    
    print("Setup Instructions:")
    print("1. Download service account key from Firebase Console")
    print("2. Save it as 'firebase-key.json' in the storage/ folder")
    print("3. Set environment variable:")
    print("   export FIREBASE_CREDENTIALS_PATH='/path/to/firebase-key.json'")
    print("4. Or use Google Cloud default credentials if running on GCP")


if __name__ == "__main__":
    # Test Firebase configuration
    print("Testing Firebase Configuration...")
    print("-" * 40)
    
    # Show current environment
    setup_environment_variables()
    
    # Try to initialize Firebase
    try:
        config = get_firebase_config()
        if config.test_connection():
            print("✓ Firebase configuration successful!")
        else:
            print("✗ Firebase configuration failed!")
    except Exception as e:
        print(f"✗ Error: {e}")
        print("\nPlease ensure you have:")
        print("1. Installed firebase-admin: pip install firebase-admin")
        print("2. Downloaded your service account key from Firebase Console")
        print("3. Set the FIREBASE_CREDENTIALS_PATH environment variable")