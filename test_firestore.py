#!/usr/bin/env python3
"""
Test Firebase Firestore Integration
Tests connection, authentication, and basic CRUD operations
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any


def test_imports():
    """Test if all required imports are available"""
    print("🔍 Testing imports...")
    
    try:
        import firebase_admin
        print("✅ firebase_admin imported successfully")
    except ImportError as e:
        print(f"❌ firebase_admin import failed: {e}")
        print("   Run: pip install firebase-admin")
        return False
    
    try:
        from google.cloud import firestore
        print("✅ google.cloud.firestore imported successfully")
    except ImportError as e:
        print(f"❌ google.cloud.firestore import failed: {e}")
        return False
    
    try:
        # Add current directory to path for storage module
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        from storage import get_storage_client
        print("✅ storage module imported successfully")
    except ImportError as e:
        print(f"❌ storage module import failed: {e}")
        print(f"   Error details: {e}")
        return False
    
    return True


def test_environment():
    """Test environment variables and credentials"""
    print("\n🔍 Testing environment setup...")
    
    # Check for Firebase credentials
    firebase_creds = os.getenv('FIREBASE_CREDENTIALS_PATH')
    google_creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    if firebase_creds:
        print(f"✅ FIREBASE_CREDENTIALS_PATH: {firebase_creds}")
        if os.path.exists(firebase_creds):
            print("✅ Credentials file exists")
        else:
            print("❌ Credentials file not found")
    elif google_creds:
        print(f"✅ GOOGLE_APPLICATION_CREDENTIALS: {google_creds}")
        if os.path.exists(google_creds):
            print("✅ Credentials file exists")
        else:
            print("❌ Credentials file not found")
    else:
        print("⚠️  No Firebase credentials environment variables found")
        print("   Set FIREBASE_CREDENTIALS_PATH or GOOGLE_APPLICATION_CREDENTIALS")
    
    # Check current directory for potential credential files
    possible_creds = ['firebase-key.json', 'service-account.json', 'credentials.json']
    for cred_file in possible_creds:
        if os.path.exists(cred_file):
            print(f"📁 Found potential credentials file: {cred_file}")
    
    return True


def test_firebase_connection():
    """Test Firebase connection and authentication"""
    print("\n🔍 Testing Firebase connection...")
    
    try:
        # Ensure path is set
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
            
        from storage import get_storage_client
        
        print("   Creating storage client...")
        client = get_storage_client()
        print("✅ Storage client created successfully")
        
        print("   Testing database connection...")
        stats = client.get_stats()
        print("✅ Database connection successful")
        print(f"   Stats: {stats}")
        
        return client
        
    except Exception as e:
        print(f"❌ Firebase connection failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return None


def create_test_video_segment():
    """Create a test VideoSegment object"""
    # Ensure path is set
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
        
    from youtube_extractor import VideoSegment
    
    return VideoSegment(
        video_id="test123abc",
        url="https://youtube.com/watch?v=test123abc&t=0",
        start_time=0,
        end_time=120,
        transcript="This is a test transcript for Firebase storage testing. It contains sample content to verify that our storage system works correctly.",
        raw_segments=[
            {"start": 0.0, "duration": 5.0, "text": "This is a test transcript"},
            {"start": 5.0, "duration": 5.0, "text": "for Firebase storage testing."},
            {"start": 10.0, "duration": 5.0, "text": "It contains sample content"},
            {"start": 15.0, "duration": 5.0, "text": "to verify that our storage"},
            {"start": 20.0, "duration": 5.0, "text": "system works correctly."}
        ]
    )


def create_test_summary_data():
    """Create test summary data"""
    return {
        'video_id': 'test123abc',
        'url': 'https://youtube.com/watch?v=test123abc&t=0',
        'start_time': 0,
        'end_time': 120,
        'duration': 120,
        'transcription': 'This is a test transcript for Firebase storage testing. It contains sample content to verify that our storage system works correctly.',
        'summary': 'This is a test summary about Firebase storage testing and verification of the storage system functionality.',
        'books': ['Test Book 1', 'Firebase Guide'],
        'people': ['John Doe', 'Jane Smith'],
        'places': ['San Francisco', 'Silicon Valley'],
        'facts': [
            'Firebase is a Google Cloud service',
            'Firestore is a NoSQL database',
            'This is a test fact'
        ],
        'topics': ['Firebase', 'Testing', 'Storage', 'NoSQL'],
        'tags': ['test', 'firebase', 'storage-test'],
        'user_notes': 'Test data for Firebase integration verification',
        'character_count': 132,
        'entity_counts': {
            'books': 2,
            'people': 2,
            'places': 2,
            'facts': 3,
            'topics': 4
        },
        'processing_metadata': {
            'model_used': 'test-model',
            'extraction_type': 'test_extraction',
            'processed_at': datetime.now().isoformat()
        }
    }


def test_basic_operations(client):
    """Test basic CRUD operations"""
    print("\n🔍 Testing basic operations...")
    
    try:
        # Test 1: Save a video segment
        print("   Test 1: Saving video segment...")
        test_segment = create_test_video_segment()
        segment_id = client.save_segment(test_segment, tags=['test', 'integration'], user_notes='Test segment')
        print(f"✅ Segment saved with ID: {segment_id}")
        
        # Test 2: Retrieve the segment
        print("   Test 2: Retrieving video segment...")
        retrieved_segment = client.get_segment(segment_id)
        if retrieved_segment:
            print(f"✅ Segment retrieved: {retrieved_segment['video_id']}")
        else:
            print("❌ Failed to retrieve segment")
        
        # Test 3: Save a complete summary
        print("   Test 3: Saving complete summary...")
        test_summary = create_test_summary_data()
        summary_id = client.save_complete_summary(test_summary)
        print(f"✅ Summary saved with ID: {summary_id}")
        
        # Test 4: Retrieve the summary
        print("   Test 4: Retrieving complete summary...")
        retrieved_summary = client.get_complete_summary(summary_id)
        if retrieved_summary:
            print(f"✅ Summary retrieved: {retrieved_summary['video_id']}")
            print(f"   Transcript length: {len(retrieved_summary.get('transcription', ''))}")
        else:
            print("❌ Failed to retrieve summary")
        
        # Test 5: Search summaries
        print("   Test 5: Searching summaries...")
        search_results = client.search_complete_summaries(query='Firebase', limit=5)
        print(f"✅ Search completed: {len(search_results)} results found")
        
        # Test 6: Get updated statistics
        print("   Test 6: Getting updated statistics...")
        updated_stats = client.get_stats()
        print(f"✅ Updated stats: {updated_stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Operations test failed: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False


def test_transcript_summarizer_integration():
    """Test TranscriptSummarizer integration with Firestore"""
    print("\n🔍 Testing TranscriptSummarizer Firestore integration...")
    
    try:
        # Check if OpenAI API is available for full test
        if not os.getenv('OPENAI_API_KEY'):
            print("⚠️  OPENAI_API_KEY not set - skipping full summarizer test")
            print("   Testing only Firestore methods...")
            
            # Test just the Firestore methods without OpenAI
            # Ensure path is set
            import sys
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
                
            from transcript_summarizer import TranscriptSummarizer, TranscriptSummary
            
            summarizer = TranscriptSummarizer()
            
            # Create a mock summary
            mock_summary = TranscriptSummary(
                url="https://youtube.com/watch?v=test456def&t=0",
                start_time=30,
                end_time=90,
                transcription="Mock transcript for testing TranscriptSummarizer Firestore integration.",
                summary="Mock summary for testing purposes.",
                books=["Test Book"],
                people=["Test Person"],
                places=["Test Location"],
                facts=["Test fact about integration"],
                topics=["Testing", "Integration"]
            )
            
            # Test saving to Firestore
            summary_id = summarizer.save_summary_to_firestore(
                summary=mock_summary,
                tags=['test', 'mock', 'integration'],
                user_notes='Mock summary for testing'
            )
            print(f"✅ Mock summary saved with ID: {summary_id}")
            
            # Test retrieving from Firestore
            retrieved = summarizer.get_summary_from_firestore(summary_id)
            if retrieved:
                print(f"✅ Mock summary retrieved: {len(retrieved.get('transcription', ''))} chars")
            else:
                print("❌ Failed to retrieve mock summary")
            
            return True
        else:
            print("✅ OPENAI_API_KEY found - full integration test possible")
            return True
            
    except Exception as e:
        print(f"❌ TranscriptSummarizer integration test failed: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False


def main():
    """Run all tests"""
    print("🚀 Firebase Firestore Integration Test")
    print("=" * 50)
    
    # Test 1: Imports
    if not test_imports():
        print("\n❌ Import tests failed - please fix dependencies first")
        return
    
    # Test 2: Environment
    test_environment()
    
    # Test 3: Firebase connection
    client = test_firebase_connection()
    if not client:
        print("\n❌ Firebase connection failed - please check credentials")
        return
    
    # Test 4: Basic operations
    if not test_basic_operations(client):
        print("\n❌ Basic operations failed")
        return
    
    # Test 5: TranscriptSummarizer integration
    test_transcript_summarizer_integration()
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!")
    print("\n📋 Next steps:")
    print("1. If all tests passed: Your Firestore integration is working!")
    print("2. If tests failed: Check the error messages above")
    print("3. Make sure Firebase credentials are properly configured")
    print("4. Verify firebase-admin package is installed")


if __name__ == "__main__":
    main()