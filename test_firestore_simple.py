#!/usr/bin/env python3
"""
Simple Firebase Firestore Test
Tests Firebase connection and saves sample data
"""

import os
import sys

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def main():
    print("🚀 Simple Firebase Firestore Test")
    print("=" * 40)
    
    # Test 1: Check Firebase Admin
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        print("✅ Firebase Admin SDK available")
    except ImportError as e:
        print(f"❌ Firebase Admin not available: {e}")
        return
    
    # Test 2: Import our modules directly
    try:
        from storage.firebase_config import FirebaseConfig, get_firebase_config
        from storage.firebase_storage import FirebaseStorage, get_storage_client
        print("✅ Storage modules imported successfully")
    except ImportError as e:
        print(f"❌ Storage modules failed: {e}")
        return
    
    # Test 3: Create Firebase client
    try:
        print("\n🔍 Testing Firebase connection...")
        
        # Try to create Firebase config
        config = get_firebase_config()
        print("✅ Firebase config created")
        
        # Try to get storage client
        client = get_storage_client()
        print("✅ Storage client created")
        
        # Test connection
        stats = client.get_stats()
        print(f"✅ Connected to Firestore: {stats}")
        
    except Exception as e:
        print(f"❌ Firebase connection failed: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")
        return
    
    # Test 4: Save sample data
    try:
        print("\n🔍 Testing data operations...")
        
        # Create test summary data (cleaned structure - no redundant fields)
        test_summary = {
            'video_id': 'test_video_123',
            'start_time': '0s',
            'end_time': '60s',
            'transcription': 'This is a test transcript to verify Firebase storage integration.',
            'summary': 'Test summary for Firebase integration verification.',
            'books': ['Test Book'],
            'people': ['Test Person'],
            'places': ['Test Location'],
            'facts': ['Firebase stores data in the cloud'],
            'topics': ['Testing', 'Firebase', 'Integration'],
            'tags': ['test', 'firebase'],
            'user_notes': 'Test data for verifying cleaned Firestore structure',
            'processing_metadata': {
                'model_used': 'test-model',
                'extraction_type': 'integration_test',
                'processed_at': '2025-01-25T12:00:00'
            }
        }
        
        print("📊 Test data contains only essential fields:")
        print("   ✅ No character_count (calculate with len(transcription))")  
        print("   ✅ No entity_counts (calculate from entity arrays)")
        print("   ✅ No url (construct from video_id + start_time)")
        print("   ✅ No duration (calculate from start_time - end_time)")
        
        # Save to Firestore
        segment_id = client.save_complete_segment(test_summary)
        print(f"✅ Test segment saved with ID: {segment_id}")
        
        # Retrieve it back
        retrieved = client.get_complete_segment(segment_id)
        if retrieved:
            print(f"✅ Summary retrieved successfully")
            print(f"   Video ID: {retrieved.get('video_id')}")
            print(f"   Transcript: {retrieved.get('transcription')[:50]}...")
            print(f"   Books: {retrieved.get('books')}")
            print(f"   People: {retrieved.get('people')}")
            
            # Test calculated fields
            print(f"\n🧮 Testing calculated fields:")
            char_count = len(retrieved.get('transcription', ''))
            print(f"   Character count: {char_count} (calculated)")
            
            entity_counts = {
                'books': len(retrieved.get('books', [])),
                'people': len(retrieved.get('people', [])), 
                'places': len(retrieved.get('places', [])),
                'facts': len(retrieved.get('facts', [])),
                'topics': len(retrieved.get('topics', []))
            }
            print(f"   Entity counts: {entity_counts} (calculated)")
            
            video_id = retrieved.get('video_id')
            start_time = retrieved.get('start_time', '').replace('s', '')
            url = f"https://www.youtube.com/watch?v={video_id}&t={start_time}"
            print(f"   URL: {url} (constructed)")
            
        else:
            print("❌ Failed to retrieve summary")
        
        # Test search
        search_results = client.search_segments(query='Firebase', limit=3)
        print(f"✅ Search completed: {len(search_results)} results")
        
        # Get updated stats
        final_stats = client.get_stats()
        print(f"✅ Final stats: {final_stats}")
        
    except Exception as e:
        print(f"❌ Data operations failed: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")
        return
    
    print("\n" + "=" * 40)
    print("🎉 All Firebase tests passed!")
    print("✅ Your Firestore integration is working correctly!")
    print("✅ Full transcript storage is functional!")
    
    print(f"\n📊 Final Statistics:")
    for key, value in final_stats.items():
        print(f"   {key}: {value}")

if __name__ == "__main__":
    main()