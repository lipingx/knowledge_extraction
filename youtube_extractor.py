"""
YouTube Data Extraction Module
Handles fetching transcriptions and extracting time-based segments from YouTube videos
"""

import re
from typing import Dict, Optional, Tuple, List
from urllib.parse import urlparse, parse_qs
from dataclasses import dataclass
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter


@dataclass
class VideoSegment:
    """Represents a segment of a YouTube video with transcript"""
    video_id: str
    url: str
    start_time: int  # in seconds
    end_time: int    # in seconds
    transcript: str
    raw_segments: List[Dict]  # Original transcript segments with timestamps


class YouTubeExtractor:
    """Extracts transcripts and segments from YouTube videos"""
    
    def __init__(self):
        self.formatter = TextFormatter()
        self.api = YouTubeTranscriptApi()
    
    def parse_youtube_url(self, url: str) -> Tuple[str, Optional[int]]:
        """
        Parse YouTube URL to extract video ID and start time
        
        Args:
            url: YouTube URL (various formats supported)
            
        Returns:
            Tuple of (video_id, start_time_in_seconds)
        """
        # Handle different YouTube URL formats
        parsed = urlparse(url)
        
        video_id = None
        start_time = None
        
        # youtube.com/watch?v=VIDEO_ID
        if parsed.hostname in ['www.youtube.com', 'youtube.com']:
            if parsed.path == '/watch':
                query_params = parse_qs(parsed.query)
                video_id = query_params.get('v', [None])[0]
                # Check for time parameter (t=89 or t=1m29s)
                time_param = query_params.get('t', [None])[0]
                if time_param:
                    start_time = self._parse_time_param(time_param)
        
        # youtu.be/VIDEO_ID
        elif parsed.hostname in ['youtu.be', 'www.youtu.be']:
            video_id = parsed.path.lstrip('/')
            query_params = parse_qs(parsed.query)
            time_param = query_params.get('t', [None])[0]
            if time_param:
                start_time = self._parse_time_param(time_param)
        
        # Handle embedded URLs
        elif 'youtube.com/embed/' in url:
            match = re.search(r'embed/([a-zA-Z0-9_-]+)', url)
            if match:
                video_id = match.group(1)
                # Check for start parameter in embedded URLs
                query_params = parse_qs(parsed.query)
                start_param = query_params.get('start', [None])[0]
                if start_param:
                    start_time = int(start_param)
        
        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {url}")
        
        return video_id, start_time
    
    def _parse_time_param(self, time_str: str) -> int:
        """
        Parse time parameter from various formats (89, 1m29s, 1:24:07, etc.)
        
        Args:
            time_str: Time string in various formats
            
        Returns:
            Time in seconds
        """
        if not time_str:
            return 0
        
        # Convert to string if needed
        time_str = str(time_str)
        
        # Pure seconds (e.g., "89")
        if time_str.isdigit():
            return int(time_str)
        
        # Format: HH:MM:SS or MM:SS or H:MM:SS
        if ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 3:
                # HH:MM:SS or H:MM:SS
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(parts[2])
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:
                # MM:SS
                minutes = int(parts[0])
                seconds = int(parts[1])
                return minutes * 60 + seconds
        
        # Format: 1h2m3s or 2m3s or 3s
        total_seconds = 0
        
        # Hours
        hours_match = re.search(r'(\d+)h', time_str)
        if hours_match:
            total_seconds += int(hours_match.group(1)) * 3600
        
        # Minutes
        minutes_match = re.search(r'(\d+)m', time_str)
        if minutes_match:
            total_seconds += int(minutes_match.group(1)) * 60
        
        # Seconds - be more specific to avoid matching minute digits
        seconds_match = re.search(r'(\d+)s', time_str)
        if seconds_match:
            total_seconds += int(seconds_match.group(1))
        elif not hours_match and not minutes_match:
            # If no h, m, or s markers, treat as pure seconds
            pure_number = re.match(r'^(\d+)$', time_str)
            if pure_number:
                total_seconds += int(pure_number.group(1))
        
        return total_seconds
    
    def fetch_transcript(self, video_id: str, languages: List[str] = None) -> List[Dict]:
        """
        Fetch transcript for a YouTube video
        
        Args:
            video_id: YouTube video ID
            languages: Preferred languages (default: ['en'])
            
        Returns:
            List of transcript segments with timestamps
        """
        if languages is None:
            languages = ['en']
        
        try:
            # Get available transcripts
            transcript_list = self.api.list(video_id)
            
            # Try to find a transcript in preferred languages
            try:
                # Try to find manually created transcript first
                transcript = transcript_list.find_manually_created_transcript(languages)
            except:
                try:
                    # Fall back to auto-generated transcript
                    transcript = transcript_list.find_generated_transcript(languages)
                except:
                    # Use first available transcript if no match
                    transcript = transcript_list.find_transcript([])
            
            # Fetch the actual transcript content
            return transcript.fetch()
            
        except Exception as e:
            raise Exception(f"Failed to fetch transcript: {str(e)}")
    
    def extract_segment(self, 
                       url: str, 
                       duration: int = None,
                       start_time: str = None,
                       end_time: str = None) -> VideoSegment:
        """
        Extract a segment of transcript from a YouTube video
        
        Args:
            url: YouTube video URL
            duration: Duration in seconds (ignored if end_time is provided)
            start_time: Start time in format '1:24:07' or seconds (overrides URL timestamp)
            end_time: End time in format '1:24:07' or seconds
            
        Returns:
            VideoSegment object with extracted transcript
        """
        # Parse URL
        video_id, url_start_time = self.parse_youtube_url(url)
        
        # Determine actual start time
        if start_time is not None:
            # Parse start_time if it's a string format like '1:24:07'
            if isinstance(start_time, str):
                start_seconds = self._parse_time_param(start_time)
            else:
                start_seconds = start_time
        else:
            start_seconds = url_start_time if url_start_time is not None else 0
        
        # Fetch full transcript
        transcript_segments = self.fetch_transcript(video_id)
        
        # Calculate end time
        if end_time is not None:
            # Parse end_time if it's a string format like '1:24:07'
            if isinstance(end_time, str):
                end_seconds = self._parse_time_param(end_time)
            else:
                end_seconds = end_time
        elif duration:
            end_seconds = start_seconds + duration
        else:
            # Get entire video from start_time
            if transcript_segments:
                last_segment = transcript_segments[-1]
                # Handle both dict and object formats
                if hasattr(last_segment, 'start'):
                    end_seconds = last_segment.start + (last_segment.duration if hasattr(last_segment, 'duration') else 0)
                else:
                    end_seconds = last_segment['start'] + last_segment.get('duration', 0)
            else:
                end_seconds = start_seconds
        
        # Extract relevant segments
        relevant_segments = []
        combined_text = []
        
        for segment in transcript_segments:
            # Handle both dict and object formats
            if hasattr(segment, 'start'):
                # Object format (newer API)
                segment_start = segment.start
                segment_end = segment_start + (segment.duration if hasattr(segment, 'duration') else 0)
                text = segment.text
                # Convert to dict for storage
                segment_dict = {
                    'start': segment_start,
                    'duration': segment.duration if hasattr(segment, 'duration') else 0,
                    'text': text
                }
            else:
                # Dict format (older API or different response)
                segment_start = segment['start']
                segment_end = segment_start + segment.get('duration', 0)
                text = segment['text']
                segment_dict = segment
            
            # Check if segment overlaps with our time range
            if segment_end >= start_seconds and segment_start <= end_seconds:
                relevant_segments.append(segment_dict)
                combined_text.append(text)
        
        # Combine transcript text
        transcript_text = ' '.join(combined_text)
        
        # Create clean URL without time parameter for storage
        clean_url = url.split('&t=')[0].split('?t=')[0]
        # Add our specific timestamp
        if '?' in clean_url:
            final_url = f"{clean_url}&t={start_seconds}"
        else:
            final_url = f"{clean_url}?t={start_seconds}"
        
        return VideoSegment(
            video_id=video_id,
            url=final_url,
            start_time=start_seconds,
            end_time=end_seconds,
            transcript=transcript_text,
            raw_segments=relevant_segments
        )
    
    def format_segment_with_timestamps(self, segment: VideoSegment) -> str:
        """
        Format segment with detailed timestamps for each subtitle
        
        Args:
            segment: VideoSegment object
            
        Returns:
            Formatted string with timestamps
        """
        lines = []
        lines.append(f"Video ID: {segment.video_id}")
        lines.append(f"URL: {segment.url}")
        lines.append(f"Segment: {segment.start_time}s - {segment.end_time}s")
        lines.append("\nTranscript with timestamps:")
        lines.append("-" * 40)
        
        for seg in segment.raw_segments:
            timestamp = self._seconds_to_timestamp(seg['start'])
            lines.append(f"[{timestamp}] {seg['text']}")
        
        return '\n'.join(lines)
    
    def _seconds_to_timestamp(self, seconds: float) -> str:
        """Convert seconds to readable timestamp format (MM:SS or HH:MM:SS)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"


# Example usage
if __name__ == "__main__":
    extractor = YouTubeExtractor()
    
    # Test with a known video that typically has transcripts
    # Using a TED talk as they usually have good transcripts
    # url = "https://www.youtube.com/watch?v=2lAe1cqCOXo"
    url = "https://www.youtube.com/watch?v=rCtvAvZtJyE&t=126s"
    
    # Example 1: Using time format strings
    start_time = "1:24:07"  # 1 hour, 24 minutes, 7 seconds
    end_time = "1:25:00"    # 1 hour, 25 minutes, 0 seconds
    
    try:
        print("Test 1: Using time format strings (HH:MM:SS)")
        print(f"Start: {start_time}, End: {end_time}")
        segment = extractor.extract_segment(url, start_time=start_time, end_time=end_time)
        
        print("Extracted Segment:")
        print(f"Video ID: {segment.video_id}")
        print(f"URL: {segment.url}")
        print(f"Time: {segment.start_time}s - {segment.end_time}s")
        print(f"Transcript preview: {segment.transcript[:200]}...")  # First 200 chars
        print(f"Full transcript length: {len(segment.transcript)} characters")
        print("\n" + "="*50 + "\n")
        
        # Show with detailed timestamps (first 5 segments)
        if segment.raw_segments:
            print("First few segments with timestamps:")
            for seg in segment.raw_segments[:5]:
                timestamp = extractor._seconds_to_timestamp(seg['start'])
                print(f"[{timestamp}] {seg['text']}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: The video might not have transcripts available.")
        print("Try with a different YouTube video URL that has captions/subtitles.")