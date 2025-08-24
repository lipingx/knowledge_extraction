"""
Test script demonstrating the new time format functionality
"""

from youtube_extractor import YouTubeExtractor

def test_time_formats():
    extractor = YouTubeExtractor()
    
    # Test video URL
    url = "https://www.youtube.com/watch?v=2lAe1cqCOXo"
    
    print("="*60)
    print("Testing Different Time Format Inputs")
    print("="*60)
    
    # Test 1: Using HH:MM:SS format with start and end time
    print("\n1. Using HH:MM:SS format (start_time='0:00:10', end_time='0:00:40')")
    try:
        segment = extractor.extract_segment(
            url, 
            start_time="0:00:10",  # 10 seconds
            end_time="0:00:40"     # 40 seconds
        )
        print(f"   ✓ Time range: {segment.start_time}s - {segment.end_time}s")
        print(f"   ✓ Duration: {segment.end_time - segment.start_time} seconds")
        print(f"   ✓ Transcript length: {len(segment.transcript)} characters")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: Using MM:SS format
    print("\n2. Using MM:SS format (start_time='1:30', end_time='2:00')")
    try:
        segment = extractor.extract_segment(
            url,
            start_time="1:30",   # 1 minute 30 seconds = 90 seconds
            end_time="2:00"      # 2 minutes = 120 seconds
        )
        print(f"   ✓ Time range: {segment.start_time}s - {segment.end_time}s")
        print(f"   ✓ Duration: {segment.end_time - segment.start_time} seconds")
        print(f"   ✓ Transcript length: {len(segment.transcript)} characters")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 3: Using H:MM:SS format (single digit hour)
    print("\n3. Using H:MM:SS format (start_time='1:24:07', end_time='1:25:00')")
    try:
        segment = extractor.extract_segment(
            url,
            start_time="1:24:07",  # 1 hour, 24 minutes, 7 seconds = 5047 seconds
            end_time="1:25:00"     # 1 hour, 25 minutes = 5100 seconds
        )
        print(f"   ✓ Time range: {segment.start_time}s - {segment.end_time}s")
        print(f"   ✓ Duration: {segment.end_time - segment.start_time} seconds")
        print(f"   ✓ Transcript length: {len(segment.transcript)} characters")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 4: Mix of formats - string start_time with duration
    print("\n4. String start_time with duration (start_time='0:30', duration=20)")
    try:
        segment = extractor.extract_segment(
            url,
            start_time="0:30",  # 30 seconds
            duration=20         # 20 seconds duration
        )
        print(f"   ✓ Time range: {segment.start_time}s - {segment.end_time}s")
        print(f"   ✓ Duration: {segment.end_time - segment.start_time} seconds")
        print(f"   ✓ Transcript length: {len(segment.transcript)} characters")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 5: Only start_time (gets rest of video)
    print("\n5. Only start_time, no end_time or duration (start_time='3:30')")
    try:
        segment = extractor.extract_segment(
            url,
            start_time="3:30"  # 3 minutes 30 seconds = 210 seconds
        )
        print(f"   ✓ Time range: {segment.start_time}s - {segment.end_time}s")
        print(f"   ✓ Duration: {segment.end_time - segment.start_time} seconds")
        print(f"   ✓ Transcript length: {len(segment.transcript)} characters")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "="*60)
    print("All time format tests completed!")
    print("="*60)


def test_parsing():
    """Test the time parsing function directly"""
    extractor = YouTubeExtractor()
    
    print("\n" + "="*60)
    print("Testing Time Parsing Function")
    print("="*60)
    
    test_cases = [
        ("89", 89),
        ("1:30", 90),
        ("2:45", 165),
        ("1:00:00", 3600),
        ("1:24:07", 5047),
        ("2:30:45", 9045),
        ("45s", 45),
        ("2m30s", 150),
        ("1h30m", 5400),
        ("1h30m45s", 5445),
    ]
    
    for time_str, expected in test_cases:
        result = extractor._parse_time_param(time_str)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{time_str}' -> {result}s (expected: {expected}s)")


if __name__ == "__main__":
    # Test time parsing
    test_parsing()
    
    # Test with real video extraction
    print("\n")
    test_time_formats()