#!/usr/bin/env python3
"""
Debug Firestore Contents
Lists all documents in all collections
"""

import os
import sys

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def debug_firestore():
    """Debug what's actually in Firestore"""
    try:
        from storage import get_storage_client
        
        print("🔍 Debugging Firestore Contents")
        print("=" * 40)
        
        client = get_storage_client()
        db = client.db
        
        # List all collections
        collections = list(db.collections())
        print(f"Found {len(collections)} collections:")
        
        for collection in collections:
            print(f"\n📁 Collection: {collection.id}")
            print("─" * 30)
            
            # Get all documents in this collection
            docs = list(collection.stream())
            print(f"Documents: {len(docs)}")
            
            for i, doc in enumerate(docs[:5]):  # Show first 5 docs
                data = doc.to_dict()
                print(f"\n  Document #{i+1}: {doc.id}")
                
                # Show key fields
                if 'video_id' in data:
                    print(f"    video_id: {data['video_id']}")
                if 'url' in data:
                    print(f"    url: {data['url'][:50]}...")
                if 'summary' in data:
                    print(f"    summary: {data['summary'][:80]}...")
                if 'transcription' in data:
                    print(f"    transcript: {len(data['transcription'])} chars")
                if 'created_at' in data:
                    print(f"    created_at: {data['created_at']}")
                if 'tags' in data:
                    print(f"    tags: {data['tags']}")
            
            if len(docs) > 5:
                print(f"    ... and {len(docs) - 5} more documents")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")

if __name__ == "__main__":
    debug_firestore()