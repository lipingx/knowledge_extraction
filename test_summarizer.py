"""
Test script for transcript summarizer
Demonstrates how to use OpenAI API to summarize YouTube transcripts
"""

import os
from transcript_summarizer import TranscriptSummarizer


def test_basic_summarization():
    """Test basic summarization functionality"""
    print("="*60)
    print("TESTING BASIC SUMMARIZATION")
    print("="*60)
    
    # Sample transcript for testing
    sample_transcript = """
    Hi everyone, today I want to talk about the book "Atomic Habits" by James Clear. 
    This book really changed how I think about building good habits. James Clear mentions 
    that small changes compound over time. He talks about the 1% better rule, where if you 
    get just 1% better every day, you'll be 37 times better by the end of the year.
    
    I was in San Francisco last week, and I met with Dr. Sarah Johnson, a researcher at 
    Stanford University who studies habit formation. She told me that 95% of people who 
    start a new habit quit within 66 days. That's a fascinating statistic.
    
    The key insight from the book is that you should focus on systems, not goals. 
    For example, instead of saying "I want to lose 20 pounds", you should say 
    "I want to become a person who exercises regularly". This shift in identity is powerful.
    """
    
    try:
        summarizer = TranscriptSummarizer()
        
        print("📝 Analyzing sample transcript...")
        result = summarizer.summarize_transcript(sample_transcript)
        
        print("✅ Summarization successful!")
        print("\n📊 RESULTS:")
        print("-" * 40)
        
        for key, value in result.items():
            if isinstance(value, list):
                print(f"{key.upper()}: {len(value)} items")
                for item in value:
                    print(f"  • {item}")
            else:
                print(f"{key.upper()}:")
                print(f"  {value}")
            print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True


def test_youtube_integration():
    """Test integration with YouTube extractor"""
    print("\n" + "="*60)
    print("TESTING YOUTUBE INTEGRATION")  
    print("="*60)
    
    try:
        summarizer = TranscriptSummarizer()
        
        # Use a shorter segment for testing (to save on API costs)
        url = "https://www.youtube.com/watch?v=2lAe1cqCOXo"
        start_time = "0:10"  # 10 seconds
        end_time = "1:00"    # 1 minute (50 second segment)
        
        print(f"📺 Processing YouTube video segment...")
        print(f"   URL: {url}")
        print(f"   Time: {start_time} - {end_time}")
        
        summary = summarizer.process_video_segment(
            url=url,
            start_time=start_time, 
            end_time=end_time
        )
        
        print("✅ YouTube processing successful!")
        print(f"\n📊 RESULTS:")
        print("-" * 40)
        print(f"URL: {summary.url}")
        print(f"Time Range: {summary.start_time} - {summary.end_time}")
        print(f"Transcript Length: {len(summary.transcription)} characters")
        print(f"\nSUMMARY:")
        print(summary.summary[:200] + "..." if len(summary.summary) > 200 else summary.summary)
        
        # Show extracted entities
        entities = [
            ("Books", summary.books),
            ("People", summary.people), 
            ("Places", summary.places),
            ("Facts", summary.facts),
            ("Topics", summary.topics)
        ]
        
        for name, items in entities:
            if items:
                print(f"\n{name}: {len(items)} found")
                for item in items:
                    print(f"  • {item}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True


def test_file_saving():
    """Test saving functionality"""
    print("\n" + "="*60)
    print("TESTING FILE SAVING")
    print("="*60)
    
    try:
        from transcript_summarizer import TranscriptSummary
        import tempfile
        
        # Create a sample summary for testing
        sample_summary = TranscriptSummary(
            url="https://www.youtube.com/watch?v=test",
            start_time="0s",
            end_time="60s", 
            transcription="This is a test transcript for saving functionality.",
            summary="This is a test summary.",
            books=["Test Book by Author"],
            people=["John Doe", "Jane Smith"],
            places=["New York", "California"],
            facts=["Interesting fact about testing"],
            topics=["Testing", "File Operations"]
        )
        
        summarizer = TranscriptSummarizer()
        
        # Test text file saving
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            txt_file = f.name
        
        summarizer.save_summary_to_file(sample_summary, txt_file)
        print(f"✅ Text file saved: {txt_file}")
        
        # Test JSON file saving  
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_file = f.name
        
        summarizer.save_summary_as_json(sample_summary, json_file)
        print(f"✅ JSON file saved: {json_file}")
        
        # Show file contents (first few lines)
        with open(txt_file, 'r') as f:
            lines = f.readlines()[:10]
            print(f"\n📄 Text file preview:")
            for line in lines:
                print(f"   {line.rstrip()}")
        
        # Cleanup
        os.unlink(txt_file)
        os.unlink(json_file)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True


def main():
    """Run all tests"""
    print("🧪 TRANSCRIPT SUMMARIZER TEST SUITE")
    print("=" * 60)
    
    # Check API key
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  OPENAI_API_KEY environment variable not set!")
        print("Please set it with: export OPENAI_API_KEY='your-api-key-here'")
        print("\nTo run tests without OpenAI API, only file saving test will work.")
        
        # Run only file saving test
        test_file_saving()
        return
    
    # Run all tests
    tests = [
        ("Basic Summarization", test_basic_summarization),
        ("YouTube Integration", test_youtube_integration), 
        ("File Saving", test_file_saving)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, "✅ PASSED" if success else "❌ FAILED"))
        except Exception as e:
            results.append((test_name, f"❌ ERROR: {str(e)}"))
    
    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    for test_name, result in results:
        print(f"{test_name}: {result}")
    
    print(f"\nℹ️  Note: These tests use OpenAI API and may incur small costs")
    print(f"💰 Estimated cost: ~$0.01-0.05 per test run")


if __name__ == "__main__":
    main()