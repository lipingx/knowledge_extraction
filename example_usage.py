"""
Complete example showing how to use the YouTube knowledge extraction system
"""

import os
from transcript_summarizer import TranscriptSummarizer


def main():
    """Demonstrate complete workflow"""
    print("🎬 YOUTUBE KNOWLEDGE EXTRACTION SYSTEM")
    print("=" * 60)
    
    # Check if API key is set
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  To use OpenAI summarization, set OPENAI_API_KEY:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        print("\nFor now, showing structure without API call...")
        
        # Show what the output would look like
        show_sample_output()
        return
    
    # Initialize the summarizer
    summarizer = TranscriptSummarizer()
    
    # Example: Your original use case
    url = "https://youtu.be/DAQJvGjlgVM?si=Tb0YiDbcU7_jyDFb&t=89"
    start_time = "1:29"  # 1 minute 29 seconds (89 seconds)  
    duration = 50        # 50 seconds
    
    print(f"📺 Processing YouTube video...")
    print(f"   URL: {url}")
    print(f"   Start: {start_time}")
    print(f"   Duration: {duration} seconds")
    print()
    
    try:
        # Process the video segment
        print("🔄 Extracting transcript...")
        summary = summarizer.process_video_segment(
            url=url,
            start_time=start_time,
            duration=duration
        )
        
        print("✅ Processing complete!")
        
        # Display results in your desired format
        print("\n" + "=" * 60)
        print("📋 EXTRACTED KNOWLEDGE")
        print("=" * 60)
        
        result = {
            'url': summary.url,
            'start_time': summary.start_time,
            'end_time': summary.end_time,
            'transcription': summary.transcription[:200] + "..." if len(summary.transcription) > 200 else summary.transcription,
            'summary': summary.summary,
            'books': summary.books,
            'people': summary.people,
            'places': summary.places,
            'facts': summary.facts
        }
        
        # Print in the format you requested
        print(f"URL: {result['url']}")
        print(f"Start Time: {result['start_time']}")
        print(f"End Time: {result['end_time']}")
        print(f"Transcription: {result['transcription']}")
        print(f"Summary: {result['summary']}")
        print(f"Books: {', '.join(result['books']) if result['books'] else 'None found'}")
        print(f"People: {', '.join(result['people']) if result['people'] else 'None found'}")  
        print(f"Places: {', '.join(result['places']) if result['places'] else 'None found'}")
        print(f"Facts: {', '.join(result['facts']) if result['facts'] else 'None found'}")
        
        # Save to file
        os.makedirs("knowledge_notes", exist_ok=True)
        
        timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
        video_id = summary.url.split('v=')[1].split('&')[0] if 'v=' in summary.url else 'video'
        
        # Save as structured text note
        note_file = f"knowledge_notes/note_{video_id}_{timestamp}.txt"
        with open(note_file, 'w', encoding='utf-8') as f:
            f.write(f"URL: {result['url']}\n")
            f.write(f"Start Time: {result['start_time']}\n")
            f.write(f"End Time: {result['end_time']}\n")
            f.write(f"Transcription: {summary.transcription}\n")
            f.write(f"Summary: {result['summary']}\n")
            f.write(f"Books: {', '.join(result['books']) if result['books'] else 'None found'}\n")
            f.write(f"People: {', '.join(result['people']) if result['people'] else 'None found'}\n")
            f.write(f"Places: {', '.join(result['places']) if result['places'] else 'None found'}\n") 
            f.write(f"Facts: {', '.join(result['facts']) if result['facts'] else 'None found'}\n")
        
        print(f"\n💾 Knowledge note saved to: {note_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nPossible issues:")
        print("1. Check your OPENAI_API_KEY is valid")
        print("2. Ensure the video has transcripts available")
        print("3. Check your internet connection")


def show_sample_output():
    """Show what the output format looks like"""
    print("\n📋 SAMPLE OUTPUT FORMAT:")
    print("=" * 60)
    
    sample = {
        'url': 'https://youtu.be/DAQJvGjlgVM?si=Tb0YiDbcU7_jyDFb&t=89',
        'start_time': '89s',
        'end_time': '139s',
        'transcription': 'At Claude Code, we believe that AI should augment human capabilities...',
        'summary': 'Discussion about AI development and human-computer interaction principles.',
        'books': ['The Design of Everyday Things'],
        'people': ['Andrew Ng', 'Geoffrey Hinton'],
        'places': ['Stanford University', 'Silicon Valley'],
        'facts': ['90% of AI projects fail due to poor human-computer interface design']
    }
    
    for key, value in sample.items():
        if isinstance(value, list):
            print(f"{key}: {', '.join(value) if value else 'None found'}")
        else:
            print(f"{key}: {value}")
    
    print("\n💡 This is the structure your notes will have!")


if __name__ == "__main__":
    main()