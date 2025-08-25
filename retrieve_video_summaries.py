#!/usr/bin/env python3
"""
Retrieve Video Summaries Script
Gets all knowledge summaries for a specific YouTube video
"""

import os
import sys
from datetime import datetime

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def get_video_id_from_url(url):
    """Extract video ID from YouTube URL"""
    if 'youtube.com/watch?v=' in url:
        return url.split('v=')[1].split('&')[0]
    elif 'youtu.be/' in url:
        return url.split('youtu.be/')[1].split('?')[0]
    elif 'youtube.com/embed/' in url:
        return url.split('embed/')[1].split('?')[0]
    else:
        return url  # Assume it's already a video ID

def format_timestamp(seconds):
    """Convert seconds to readable timestamp"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def format_date(timestamp):
    """Format Firebase timestamp for display"""
    if timestamp and hasattr(timestamp, 'strftime'):
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    return "Unknown"

def retrieve_video_summaries(video_input):
    """
    Retrieve all knowledge summaries for a video
    
    Args:
        video_input: YouTube URL or video ID
    """
    print("🔍 Retrieving Video Knowledge Summaries")
    print("=" * 50)
    
    # Extract video ID
    video_id = get_video_id_from_url(video_input)
    print(f"Video ID: {video_id}")
    
    try:
        # Import storage client
        from storage import get_storage_client
        
        # Initialize client
        print("Connecting to Firebase...")
        client = get_storage_client()
        print("✅ Connected to Firebase Firestore")
        
        # Get all segments for this video
        segments = client.get_segments_by_video(video_id)
        
        if not segments:
            print(f"\n❌ No segments found for video: {video_id}")
            print("This video hasn't been processed yet.")
            return
        
        print(f"\n✅ Found {len(segments)} segments for this video")
        print("=" * 50)
        
        # Display each segment
        for i, segment in enumerate(segments, 1):
            print(f"\n📝 SEGMENT #{i}")
            print("─" * 30)
            print(f"🆔 Segment ID: {segment.get('id', 'N/A')}")
            print(f"🕐 Time Range: {format_timestamp(segment.get('start_time', 0))} - {format_timestamp(segment.get('end_time', 0))}")
            print(f"⏱️  Duration: {segment.get('duration', 0)} seconds")
            print(f"📅 Created: {format_date(segment.get('created_at'))}")
            print(f"🏷️  Tags: {', '.join(segment.get('tags', []))}")
            
            print(f"\n📋 AI SUMMARY:")
            print(f"{segment.get('summary', 'No summary available')}")
            
            # Display extracted entities
            books = segment.get('books', [])
            if books:
                print(f"\n📚 BOOKS ({len(books)}):")
                for book in books:
                    print(f"  • {book}")
            
            people = segment.get('people', [])
            if people:
                print(f"\n👥 PEOPLE ({len(people)}):")
                for person in people:
                    print(f"  • {person}")
            
            places = segment.get('places', [])
            if places:
                print(f"\n📍 PLACES ({len(places)}):")
                for place in places:
                    print(f"  • {place}")
            
            facts = segment.get('facts', [])
            if facts:
                print(f"\n💡 KEY FACTS ({len(facts)}):")
                for fact in facts:
                    print(f"  • {fact}")
            
            topics = segment.get('topics', [])
            if topics:
                print(f"\n🏷️  TOPICS ({len(topics)}):")
                for topic in topics:
                    print(f"  • {topic}")
            
            # Show transcript preview
            transcript = segment.get('transcription', '')
            if transcript:
                print(f"\n📝 TRANSCRIPT PREVIEW:")
                preview = transcript[:200] + "..." if len(transcript) > 200 else transcript
                print(f"{preview}")
                print(f"   (Full transcript: {len(transcript)} characters)")
            
            if segment.get('user_notes'):
                print(f"\n📄 NOTES:")
                print(f"{segment.get('user_notes')}")
            
            print("\n" + "=" * 50)
        
        # Show segment statistics
        print(f"\n📊 SEGMENT STATISTICS:")
        total_duration = sum(s.get('duration', 0) for s in segments)
        total_chars = sum(len(s.get('transcription', '')) for s in segments)
        total_entities = sum(sum(s.get('entity_counts', {}).values()) for s in segments)
        
        print(f"📹 Total processed time: {format_timestamp(total_duration)}")
        print(f"📝 Total transcript characters: {total_chars:,}")
        print(f"🧠 Total extracted entities: {total_entities}")
        print(f"⚡ Average entities per minute: {total_entities / (total_duration / 60):.1f}" if total_duration > 0 else "")
        
    except ImportError as e:
        print(f"❌ Storage module not available: {e}")
        print("Make sure Firebase is properly configured.")
    except Exception as e:
        print(f"❌ Error retrieving summaries: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")

def main():
    """Main function with interactive input"""
    print("🎬 YouTube Knowledge Retrieval Tool")
    print("=" * 40)
    
    # Check if video ID/URL was provided as argument
    if len(sys.argv) > 1:
        video_input = sys.argv[1]
        print(f"Using provided video: {video_input}")
    else:
        # Interactive input
        print("Enter YouTube URL or Video ID:")
        print("Examples:")
        print("  • https://youtube.com/watch?v=rCtvAvZtJyE")
        print("  • rCtvAvZtJyE")
        print("  • test_video_123 (from our test)")
        print()
        
        video_input = input("Video URL/ID: ").strip()
        
        if not video_input:
            print("❌ No video provided!")
            return
    
    retrieve_video_summaries(video_input)

if __name__ == "__main__":
    main()