"""
YouTube Video Description Extractor
Extracts video description, title, and chapter timestamps from YouTube videos
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import subprocess
import sys

@dataclass
class VideoChapter:
    """Represents a video chapter with timestamp and title"""
    start_time: str
    title: str
    start_seconds: int

@dataclass
class VideoInfo:
    """Represents YouTube video information"""
    video_id: str
    title: str
    description: str
    duration: int
    chapters: List[VideoChapter]
    channel: str
    upload_date: str

class YouTubeDescriptionExtractor:
    """Extracts video description and chapter information from YouTube videos"""
    
    def __init__(self):
        self.check_ytdlp_installed()
    
    def check_ytdlp_installed(self):
        """Check if yt-dlp is installed"""
        try:
            subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  yt-dlp not found. Installing...")
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'yt-dlp'], check=True)
                print("✅ yt-dlp installed successfully")
            except subprocess.CalledProcessError:
                raise Exception("Failed to install yt-dlp. Please install manually: pip install yt-dlp")
    
    def extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'youtube\.com/watch\?v=([^&]+)',
            r'youtu\.be/([^?]+)',
            r'youtube\.com/embed/([^?]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError("Could not extract video ID from URL")
    
    def time_to_seconds(self, time_str: str) -> int:
        """Convert time string (HH:MM:SS, MM:SS, or SS) to seconds"""
        parts = time_str.split(':')
        if len(parts) == 3:  # HH:MM:SS
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:  # MM:SS
            return int(parts[0]) * 60 + int(parts[1])
        else:  # SS
            return int(parts[0])
    
    def parse_chapters_from_description(self, description: str) -> List[VideoChapter]:
        """Parse chapter timestamps from video description"""
        chapters = []
        
        # Pattern to match timestamps like "00:00 Title", "1:23 Title", "12:34:56 Title"
        timestamp_pattern = r'(\d{1,2}:?\d{0,2}:?\d{2})\s+(.+?)(?=\n|\r|\Z|(?:\d{1,2}:?\d{0,2}:?\d{2}))'
        
        lines = description.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for timestamp at the beginning of the line
            match = re.match(r'^(\d{1,2}:?\d{0,2}:?\d{2})\s+(.+)', line)
            if match:
                time_str = match.group(1)
                title = match.group(2).strip()
                
                # Clean up the title (remove extra whitespace, formatting)
                title = re.sub(r'\s+', ' ', title)
                
                try:
                    start_seconds = self.time_to_seconds(time_str)
                    chapters.append(VideoChapter(
                        start_time=time_str,
                        title=title,
                        start_seconds=start_seconds
                    ))
                except ValueError:
                    continue
        
        # Sort chapters by start time
        chapters.sort(key=lambda x: x.start_seconds)
        return chapters
    
    def extract_video_info(self, url: str) -> VideoInfo:
        """Extract complete video information including description and chapters"""
        try:
            # Use yt-dlp to extract video metadata
            cmd = [
                'yt-dlp',
                '--dump-json',
                '--no-download',
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            video_data = json.loads(result.stdout)
            
            # Extract basic info
            video_id = video_data.get('id', '')
            title = video_data.get('title', '')
            description = video_data.get('description', '')
            duration = video_data.get('duration', 0)
            channel = video_data.get('uploader', '')
            upload_date = video_data.get('upload_date', '')
            
            # Parse chapters from description
            chapters = self.parse_chapters_from_description(description)
            
            # If yt-dlp found chapters, use those instead
            if 'chapters' in video_data and video_data['chapters']:
                chapters = []
                for chapter in video_data['chapters']:
                    start_seconds = int(chapter.get('start_time', 0))
                    title = chapter.get('title', '')
                    
                    # Convert seconds back to time string
                    hours = start_seconds // 3600
                    minutes = (start_seconds % 3600) // 60
                    seconds = start_seconds % 60
                    
                    if hours > 0:
                        time_str = f"{hours}:{minutes:02d}:{seconds:02d}"
                    else:
                        time_str = f"{minutes}:{seconds:02d}"
                    
                    chapters.append(VideoChapter(
                        start_time=time_str,
                        title=title,
                        start_seconds=start_seconds
                    ))
            
            return VideoInfo(
                video_id=video_id,
                title=title,
                description=description,
                duration=duration,
                chapters=chapters,
                channel=channel,
                upload_date=upload_date
            )
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to extract video info: {e.stderr}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse video data: {e}")
    
    def get_description_only(self, url: str) -> str:
        """Quick method to get just the description"""
        video_info = self.extract_video_info(url)
        return video_info.description
    
    def get_chapters_only(self, url: str) -> List[VideoChapter]:
        """Quick method to get just the chapters"""
        video_info = self.extract_video_info(url)
        return video_info.chapters
    
    def print_video_info(self, video_info: VideoInfo):
        """Pretty print video information"""
        print("=" * 60)
        print(f"📺 TITLE: {video_info.title}")
        print(f"🆔 VIDEO ID: {video_info.video_id}")
        print(f"📺 CHANNEL: {video_info.channel}")
        print(f"⏱️ DURATION: {video_info.duration} seconds")
        print(f"📅 UPLOAD DATE: {video_info.upload_date}")
        print("=" * 60)
        
        if video_info.chapters:
            print(f"📑 CHAPTERS ({len(video_info.chapters)}):")
            print("-" * 40)
            for chapter in video_info.chapters:
                print(f"{chapter.start_time} {chapter.title}")
            print()
        else:
            print("📑 No chapters found in video")
            print()
        
        print("📝 DESCRIPTION:")
        print("-" * 40)
        # Show first 500 characters of description
        description_preview = video_info.description[:500]
        if len(video_info.description) > 500:
            description_preview += "..."
        print(description_preview)
        print()

# Example usage and testing
if __name__ == "__main__":
    # Test with the cancer video from your example
    test_url = "https://www.youtube.com/watch?v=VaVC3PAWqLk"
    
    extractor = YouTubeDescriptionExtractor()
    
    print("🚀 YouTube Description Extractor")
    print("=" * 50)
    
    # Interactive mode
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter YouTube URL: ").strip()
    
    if not url:
        print("❌ No URL provided")
        sys.exit(1)
    
    try:
        print(f"🔍 Extracting info from: {url}")
        video_info = extractor.extract_video_info(url)
        extractor.print_video_info(video_info)
        
        # Save to JSON file
        output_file = f"video_info_{video_info.video_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            # Convert dataclasses to dict for JSON serialization
            data = {
                'video_id': video_info.video_id,
                'title': video_info.title,
                'description': video_info.description,
                'duration': video_info.duration,
                'channel': video_info.channel,
                'upload_date': video_info.upload_date,
                'chapters': [
                    {
                        'start_time': ch.start_time,
                        'title': ch.title,
                        'start_seconds': ch.start_seconds
                    }
                    for ch in video_info.chapters
                ]
            }
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Video info saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)