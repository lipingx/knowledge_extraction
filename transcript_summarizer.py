"""
Transcript Summarizer using OpenAI API
Processes video transcripts to extract summaries and key information
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
from openai import OpenAI
from youtube_extractor import YouTubeExtractor, VideoSegment


@dataclass
class TranscriptSummary:
    """Represents a summarized transcript with extracted information"""
    url: str
    start_time: str
    end_time: str
    transcription: str
    summary: str
    books: List[str] = None
    people: List[str] = None
    places: List[str] = None
    facts: List[str] = None
    topics: List[str] = None
    
    def __post_init__(self):
        """Initialize empty lists if None"""
        if self.books is None:
            self.books = []
        if self.people is None:
            self.people = []
        if self.places is None:
            self.places = []
        if self.facts is None:
            self.facts = []
        if self.topics is None:
            self.topics = []


class TranscriptSummarizer:
    """Summarizes transcripts using OpenAI API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the summarizer
        
        Args:
            api_key: OpenAI API key (if None, will look for OPENAI_API_KEY env var)
        """
        # Try to load from .env file first
        if not api_key and os.path.exists('.env'):
            try:
                with open('.env', 'r') as f:
                    for line in f:
                        if line.startswith('OPENAI_API_KEY='):
                            api_key = line.split('=', 1)[1].strip().strip('"\'')
                            break
            except:
                pass
        
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            # Will use OPENAI_API_KEY environment variable
            self.client = OpenAI()
    
    def create_summary_prompt(self, transcript: str, extract_entities: bool = True) -> str:
        """
        Create a prompt for summarizing transcript and extracting entities
        
        Args:
            transcript: The transcript text to analyze
            extract_entities: Whether to extract entities (books, people, places, facts)
            
        Returns:
            Formatted prompt string
        """
        base_prompt = f"""
Please analyze the following video transcript and provide a comprehensive summary along with extracted information.

TRANSCRIPT:
{transcript}

Please provide your response in the following JSON format:
{{
    "summary": "A concise 2-3 paragraph summary of the main points discussed",
    "books": ["list of books, publications, or written works mentioned"],
    "people": ["list of people's names mentioned (exclude generic references like 'my friend')"],
    "places": ["list of specific places, locations, cities, countries mentioned"],
    "facts": ["list of interesting facts, statistics, or claims made"],
    "topics": ["list of main topics or themes discussed"]
}}

Guidelines:
- For books: Include titles, author names if mentioned, academic papers, etc.
- For people: Include full names when available, exclude pronouns and generic references
- For places: Include specific locations, not general terms like "here" or "there"  
- For facts: Include statistics, research findings, specific claims, interesting insights
- For topics: Include main themes, subjects, concepts discussed
- Keep all lists concise and relevant
- If a category has no clear mentions, return an empty list

"""
        
        if not extract_entities:
            base_prompt = f"""
Please provide a comprehensive summary of the following video transcript.

TRANSCRIPT:
{transcript}

Please provide a 2-3 paragraph summary covering the main points, key insights, and important information discussed in the transcript.
"""
        
        return base_prompt
    
    def summarize_transcript(self, 
                           transcript: str, 
                           model: str = "gpt-4o-mini",
                           extract_entities: bool = True,
                           max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Summarize transcript using OpenAI API
        
        Args:
            transcript: The transcript text to summarize
            model: OpenAI model to use
            extract_entities: Whether to extract entities
            max_tokens: Maximum tokens in response
            
        Returns:
            Dictionary containing summary and extracted information
        """
        prompt = self.create_summary_prompt(transcript, extract_entities)
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing video transcripts and extracting key information. Always respond with valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.3,
                response_format={"type": "json_object"} if extract_entities else None
            )
            
            content = response.choices[0].message.content.strip()
            
            if extract_entities:
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    return {
                        "summary": content,
                        "books": [],
                        "people": [],
                        "places": [],
                        "facts": [],
                        "topics": []
                    }
            else:
                return {"summary": content}
                
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def process_video_segment(self, 
                            url: str, 
                            start_time: str = None, 
                            end_time: str = None,
                            duration: int = None,
                            model: str = "gpt-4o-mini") -> TranscriptSummary:
        """
        Process a YouTube video segment from URL to summary
        
        Args:
            url: YouTube video URL
            start_time: Start time in format '1:24:07' or seconds
            end_time: End time in format '1:24:07' or seconds  
            duration: Duration in seconds (ignored if end_time provided)
            model: OpenAI model to use
            
        Returns:
            TranscriptSummary object with all extracted information
        """
        # Extract transcript
        extractor = YouTubeExtractor()
        segment = extractor.extract_segment(
            url=url,
            start_time=start_time,
            end_time=end_time,
            duration=duration
        )
        
        # Summarize using OpenAI
        summary_data = self.summarize_transcript(
            transcript=segment.transcript,
            model=model,
            extract_entities=True
        )
        
        # Format time as strings
        start_str = f"{segment.start_time}s"
        end_str = f"{segment.end_time}s"
        
        # Create summary object
        return TranscriptSummary(
            url=segment.url,
            start_time=start_str,
            end_time=end_str,
            transcription=segment.transcript,
            summary=summary_data.get("summary", ""),
            books=summary_data.get("books", []),
            people=summary_data.get("people", []),
            places=summary_data.get("places", []),
            facts=summary_data.get("facts", []),
            topics=summary_data.get("topics", [])
        )
    
    def save_summary_to_file(self, summary: TranscriptSummary, filepath: str):
        """
        Save transcript summary to a structured file
        
        Args:
            summary: TranscriptSummary object
            filepath: Path to save the file
        """
        content = []
        content.append("YOUTUBE VIDEO KNOWLEDGE EXTRACTION")
        content.append("=" * 60)
        content.append(f"URL: {summary.url}")
        content.append(f"Time Range: {summary.start_time} - {summary.end_time}")
        content.append(f"Processed at: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append("")
        
        content.append("SUMMARY:")
        content.append("-" * 40)
        content.append(summary.summary)
        content.append("")
        
        if summary.books:
            content.append("BOOKS & PUBLICATIONS:")
            content.append("-" * 40)
            for book in summary.books:
                content.append(f"• {book}")
            content.append("")
        
        if summary.people:
            content.append("PEOPLE MENTIONED:")
            content.append("-" * 40)
            for person in summary.people:
                content.append(f"• {person}")
            content.append("")
        
        if summary.places:
            content.append("PLACES MENTIONED:")
            content.append("-" * 40)
            for place in summary.places:
                content.append(f"• {place}")
            content.append("")
        
        if summary.facts:
            content.append("KEY FACTS & INSIGHTS:")
            content.append("-" * 40)
            for fact in summary.facts:
                content.append(f"• {fact}")
            content.append("")
        
        if summary.topics:
            content.append("MAIN TOPICS:")
            content.append("-" * 40)
            for topic in summary.topics:
                content.append(f"• {topic}")
            content.append("")
        
        content.append("FULL TRANSCRIPT:")
        content.append("=" * 60)
        content.append(summary.transcription)
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
    
    def save_summary_as_json(self, summary: TranscriptSummary, filepath: str):
        """
        Save transcript summary as JSON
        
        Args:
            summary: TranscriptSummary object
            filepath: Path to save the JSON file
        """
        data = {
            "url": summary.url,
            "start_time": summary.start_time,
            "end_time": summary.end_time,
            "transcription": summary.transcription,
            "summary": summary.summary,
            "books": summary.books,
            "people": summary.people,
            "places": summary.places,
            "facts": summary.facts,
            "topics": summary.topics,
            "processed_at": __import__('datetime').datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def save_summary_to_firestore(self, summary: TranscriptSummary, tags: list = None, user_notes: str = "") -> str:
        """
        Save transcript summary to Firebase Firestore
        
        Args:
            summary: TranscriptSummary object
            tags: Optional list of tags for categorization
            user_notes: Optional user notes
            
        Returns:
            str: Document ID of saved summary
        """
        try:
            from storage import get_storage_client
            
            # Get Firebase storage client
            firebase_client = get_storage_client()
            
            # Extract video ID from URL
            video_id = summary.url.split('v=')[1].split('&')[0] if 'v=' in summary.url else 'unknown'
            
            # Create a comprehensive document for the summary (only essential fields)
            summary_data = {
                'video_id': video_id,
                'start_time': summary.start_time,
                'end_time': summary.end_time,
                'transcription': summary.transcription,
                'summary': summary.summary,
                'books': summary.books,
                'people': summary.people,
                'places': summary.places,
                'facts': summary.facts,
                'topics': summary.topics,
                'tags': tags or [],
                'user_notes': user_notes,
                'processing_metadata': {
                    'model_used': 'gpt-4o-mini',  # Could be made configurable
                    'extraction_type': 'full_knowledge_extraction',
                    'processed_at': __import__('datetime').datetime.now().isoformat()
                }
            }
            
            # Save to Firestore segments collection
            summary_id = firebase_client.save_complete_segment(summary_data)
            
            return summary_id
            
        except ImportError:
            raise ImportError("Firebase storage not available. Install firebase-admin to enable Firestore storage.")
        except Exception as e:
            raise Exception(f"Failed to save summary to Firestore: {str(e)}")
    
    def get_summary_from_firestore(self, summary_id: str) -> dict:
        """
        Retrieve a summary from Firebase Firestore
        
        Args:
            summary_id: Document ID of the summary
            
        Returns:
            dict: Summary data or None if not found
        """
        try:
            from storage import get_storage_client
            
            firebase_client = get_storage_client()
            return firebase_client.get_complete_segment(summary_id)
            
        except ImportError:
            raise ImportError("Firebase storage not available. Install firebase-admin to enable Firestore storage.")
        except Exception as e:
            raise Exception(f"Failed to retrieve summary from Firestore: {str(e)}")
    
    def search_summaries(self, query: str = None, filters: dict = None, limit: int = 20) -> list:
        """
        Search summaries in Firebase Firestore
        
        Args:
            query: Text to search in summaries
            filters: Dictionary of filters (tags, video_id, date_range, etc.)
            limit: Maximum results to return
            
        Returns:
            list: List of matching summary documents
        """
        try:
            from storage import get_storage_client
            
            firebase_client = get_storage_client()
            return firebase_client.search_segments(query, filters, limit)
            
        except ImportError:
            raise ImportError("Firebase storage not available. Install firebase-admin to enable Firestore storage.")
        except Exception as e:
            raise Exception(f"Failed to search summaries in Firestore: {str(e)}")


# Example usage
if __name__ == "__main__":
    import os
    from datetime import datetime
    
    # Check if API key is available
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  OPENAI_API_KEY environment variable not set!")
        print("Please set it with: export OPENAI_API_KEY='your-api-key-here'")
        exit(1)
    
    # Initialize summarizer
    summarizer = TranscriptSummarizer()
    
    # Example video URL and time range
    # url = "https://www.youtube.com/watch?v=rCtvAvZtJyE&t=126s"
    # start_time = "1:18:30"
    # end_time = "1:21:09"

    url = "https://www.youtube.com/watch?v=e7JNRf07bhA"
    start_time = "00:00:00"
    end_time = "1:21:09"

    
    try:
        print("Processing YouTube video segment...")
        print(f"URL: {url}")
        print(f"Time range: {start_time} - {end_time}")
        
        # Process the video segment
        summary = summarizer.process_video_segment(
            url=url,
            start_time=start_time,
            end_time=end_time
        )
        
        print(f"\n✅ Processing completed!")
        print(f"📊 Summary: {len(summary.summary)} characters")
        print(f"📚 Extracted: {len(summary.books)} books, {len(summary.people)} people, {len(summary.places)} places")
        print(f"📝 Facts: {len(summary.facts)}, Topics: {len(summary.topics)}")
        
        # Option 1: Save to Firebase Firestore (recommended)
        try:
            print("\nSaving to Firebase Firestore...")
            summary_id = summarizer.save_summary_to_firestore(
                summary=summary,
                tags=['example', 'knowledge-extraction', 'ai-analysis'],
                user_notes='Example complete knowledge extraction'
            )
            print(f"✓ Summary saved to Firestore with ID: {summary_id}")
            
        except ImportError:
            print("⚠️  Firebase storage not available. Install firebase-admin to enable Firestore storage.")
        except Exception as e:
            print(f"⚠️  Firebase storage error: {e}")
            print("Falling back to file storage...")
            
            # Option 2: Fallback to file storage
            os.makedirs("summaries", exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_id = summary.url.split('v=')[1].split('&')[0] if 'v=' in summary.url else 'video'
            
            # Save as text file
            txt_file = f"summaries/{video_id}_{timestamp}.txt"
            summarizer.save_summary_to_file(summary, txt_file)
            
            # Save as JSON file
            json_file = f"summaries/{video_id}_{timestamp}.json"
            summarizer.save_summary_as_json(summary, json_file)
            
            print(f"📄 Text summary: {txt_file}")
            print(f"📋 JSON data: {json_file}")
        
        # Display key results
        print(f"\n📊 SUMMARY:")
        print("-" * 50)
        print(summary.summary)
        
        if summary.books:
            print(f"\n📚 BOOKS ({len(summary.books)}):")
            for book in summary.books:
                print(f"  • {book}")
        
        if summary.people:
            print(f"\n👥 PEOPLE ({len(summary.people)}):")
            for person in summary.people:
                print(f"  • {person}")
        
        if summary.facts:
            print(f"\n💡 KEY FACTS ({len(summary.facts)}):")
            for fact in summary.facts:
                print(f"  • {fact}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure OPENAI_API_KEY is set")
        print("2. Check your internet connection")
        print("3. Verify the video has transcripts available")