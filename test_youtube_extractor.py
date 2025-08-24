"""
Test script for YouTube extractor
Demonstrates various usage scenarios
"""

from youtube_extractor import YouTubeExtractor


def test_url_parsing():
    """Test different YouTube URL formats"""
    extractor = YouTubeExtractor()
    
    test_urls = [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", None),
        ("https://youtu.be/dQw4w9WgXcQ", None),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42", 42),
        ("https://youtu.be/dQw4w9WgXcQ?t=89", 89),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=1m30s", 90),
        ("https://youtu.be/dQw4w9WgXcQ?t=2m15s", 135),
        ("https://www.youtube.com/embed/dQw4w9WgXcQ?start=60", 60),
    ]
    
    print("Testing URL parsing:")
    print("-" * 50)
    
    for url, expected_time in test_urls:
        try:
            video_id, start_time = extractor.parse_youtube_url(url)
            status = "✓" if start_time == expected_time else "✗"
            print(f"{status} URL: {url}")
            print(f"  Video ID: {video_id}, Start time: {start_time}s (expected: {expected_time}s)")
        except Exception as e:
            print(f"✗ Failed to parse: {url}")
            print(f"  Error: {e}")
        print()


def test_extraction_with_real_video():
    """Test extraction with a real video (if available)"""
    extractor = YouTubeExtractor()
    
    # Using a popular video that likely has transcripts
    # You can replace this with any YouTube video URL
    test_cases = [
        {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "duration": 30,
            "start_override": 10,
            "description": "Extract 30 seconds starting from 10s"
        },
        {
            "url": "https://youtu.be/dQw4w9WgXcQ?t=45",
            "duration": 20,
            "start_override": None,
            "description": "Extract 20 seconds from URL timestamp (45s)"
        },
    ]
    
    print("\nTesting transcript extraction:")
    print("-" * 50)
    
    for test in test_cases:
        print(f"\nTest: {test['description']}")
        print(f"URL: {test['url']}")
        
        try:
            segment = extractor.extract_segment(
                url=test['url'],
                duration=test['duration'],
                start_time_override=test['start_override']
            )
            
            print(f"✓ Successfully extracted segment")
            print(f"  Time range: {segment.start_time}s - {segment.end_time}s")
            print(f"  Transcript length: {len(segment.transcript)} characters")
            print(f"  Number of segments: {len(segment.raw_segments)}")
            
            # Show first 150 characters of transcript
            if segment.transcript:
                preview = segment.transcript[:150]
                if len(segment.transcript) > 150:
                    preview += "..."
                print(f"  Preview: {preview}")
            
        except Exception as e:
            print(f"✗ Failed to extract segment")
            print(f"  Error: {e}")


def demonstrate_usage():
    """Demonstrate the intended usage for the knowledge extraction app"""
    extractor = YouTubeExtractor()
    
    print("\n" + "="*60)
    print("DEMONSTRATION: Knowledge Extraction Use Case")
    print("="*60)
    
    # Your example URL
    url = "https://youtu.be/DAQJvGjlgVM?si=Tb0YiDbcU7_jyDFb&t=89"
    duration = 50
    
    print(f"\nInput:")
    print(f"  URL: {url}")
    print(f"  Duration: {duration} seconds")
    
    try:
        segment = extractor.extract_segment(url, duration=duration)
        
        # Prepare the data structure for the next step (NLP processing)
        extracted_data = {
            "url": segment.url,
            "start_time": f"{segment.start_time}s",
            "end_time": f"{segment.end_time}s",
            "transcript": segment.transcript,
            # These would be filled by the NLP component
            "books": [],
            "people": [],
            "places": [],
            "facts": []
        }
        
        print(f"\nOutput (ready for NLP processing):")
        print(f"  URL: {extracted_data['url']}")
        print(f"  Time range: {extracted_data['start_time']} - {extracted_data['end_time']}")
        print(f"  Transcript: {extracted_data['transcript'][:200]}...")
        print(f"\n  Next step: Pass transcript to NLP component for entity extraction")
        
    except Exception as e:
        print(f"\nError: {e}")
        print("\nNote: This error might occur if:")
        print("  1. The video doesn't exist")
        print("  2. The video has no available transcripts")
        print("  3. Network connection issues")
        print("  4. youtube-transcript-api is not installed (run: pip install youtube-transcript-api)")


if __name__ == "__main__":
    # Run tests
    test_url_parsing()
    
    print("\n" + "="*60)
    print("Note: The following tests require internet connection")
    print("and valid YouTube videos with transcripts available")
    print("="*60)
    
    test_extraction_with_real_video()
    demonstrate_usage()