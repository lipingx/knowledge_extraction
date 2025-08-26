#!/usr/bin/env python3
"""
Store specific YouTube video segment with AI knowledge extraction
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from transcript_summarizer import TranscriptSummarizer


def store_video_segment():
    """Store YouTube video segment: rCtvAvZtJyE from 1:03:03 to 1:05:18"""
    
    # Video details
    video_url = "https://www.youtube.com/watch?v=rCtvAvZtJyE"
    start_time = "1:03:03"  # 1 hour, 3 minutes, 3 seconds
    end_time = "1:05:18"    # 1 hour, 5 minutes, 18 seconds
    
    print("🎥 YouTube Video Segment Storage")
    print("=" * 50)
    print(f"Video URL: {video_url}")
    print(f"Time Range: {start_time} - {end_time}")
    print(f"Duration: ~2 minutes 15 seconds")
    
    try:
        # Initialize transcript summarizer
        print("\n📝 Initializing AI transcript summarizer...")
        summarizer = TranscriptSummarizer()
        
        # Process the video segment
        print(f"\n🔍 Processing video segment...")
        print(f"   - Fetching transcript from YouTube")
        print(f"   - Extracting segment: {start_time} to {end_time}")
        print(f"   - Running AI analysis for knowledge extraction")
        
        summary = summarizer.process_video_segment(
            url=video_url,
            start_time=start_time,
            end_time=end_time
        )
        
        print(f"\n✅ Video segment processed successfully!")
        print(f"📊 Results:")
        print(f"   - Transcript: {len(summary.transcription)} characters")
        print(f"   - Summary: {len(summary.summary)} characters")
        print(f"   - Books: {len(summary.books)} extracted")
        print(f"   - People: {len(summary.people)} mentioned")
        print(f"   - Places: {len(summary.places)} mentioned")
        print(f"   - Facts: {len(summary.facts)} extracted")
        print(f"   - Topics: {len(summary.topics)} identified")
        
        # Save to Firebase Firestore
        print(f"\n💾 Saving to Firebase Firestore...")
        segment_id = summarizer.save_summary_to_firestore(
            summary=summary,
            tags=['user-request', 'knowledge-extraction', 'video-rCtvAvZtJyE'],
            user_notes=f'User requested segment from {start_time} to {end_time}'
        )
        
        print(f"✅ Successfully saved to Firestore!")
        print(f"📋 Segment ID: {segment_id}")
        
        # Display extracted content preview
        print(f"\n📖 Content Preview:")
        print(f"=" * 30)
        
        if summary.summary:
            print(f"📝 SUMMARY:")
            print(f"{summary.summary[:300]}...")
            print()
        
        if summary.books:
            print(f"📚 BOOKS ({len(summary.books)}):")
            for book in summary.books[:3]:  # Show first 3
                print(f"   • {book}")
            if len(summary.books) > 3:
                print(f"   ... and {len(summary.books) - 3} more")
            print()
        
        if summary.people:
            print(f"👥 PEOPLE ({len(summary.people)}):")
            for person in summary.people[:5]:  # Show first 5
                print(f"   • {person}")
            if len(summary.people) > 5:
                print(f"   ... and {len(summary.people) - 5} more")
            print()
        
        if summary.facts:
            print(f"💡 KEY FACTS ({len(summary.facts)}):")
            for fact in summary.facts[:3]:  # Show first 3
                print(f"   • {fact}")
            if len(summary.facts) > 3:
                print(f"   ... and {len(summary.facts) - 3} more")
            print()
        
        if summary.topics:
            print(f"🏷️  TOPICS ({len(summary.topics)}):")
            for topic in summary.topics:
                print(f"   • {topic}")
            print()
        
        print(f"🎉 Storage completed successfully!")
        print(f"📊 The segment has been saved with cleaned Firebase structure")
        print(f"🔍 You can retrieve it using segment ID: {segment_id}")
        
    except Exception as e:
        print(f"❌ Error processing video segment: {e}")
        import traceback
        print(f"\nFull error details:")
        traceback.print_exc()
        
        print(f"\nTroubleshooting tips:")
        print(f"1. Check your internet connection")
        print(f"2. Verify OpenAI API key is set")
        print(f"3. Ensure the video has available transcripts")
        print(f"4. Check Firebase credentials are configured")


if __name__ == "__main__":
    store_video_segment()