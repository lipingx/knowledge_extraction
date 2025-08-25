"""
Flask Web Application for YouTube Knowledge Extraction
"""

from flask import Flask, render_template, request, jsonify
import os
import sys
import json
from datetime import datetime
import traceback

# Add parent directory to path to import from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from transcript_summarizer import TranscriptSummarizer

app = Flask(__name__)

# Initialize the summarizer
summarizer = None

def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    if 'youtube.com/watch?v=' in url:
        return url.split('v=')[1].split('&')[0]
    elif 'youtu.be/' in url:
        return url.split('youtu.be/')[1].split('?')[0]
    elif 'youtube.com/embed/' in url:
        return url.split('embed/')[1].split('?')[0]
    return ''

def get_summarizer():
    """Get or create summarizer instance"""
    global summarizer
    if summarizer is None:
        try:
            summarizer = TranscriptSummarizer()
        except Exception as e:
            print(f"Failed to initialize summarizer: {e}")
            summarizer = None
    return summarizer

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract_knowledge():
    """Extract knowledge from YouTube video"""
    try:
        data = request.json
        url = data.get('url', '').strip()
        start_time = data.get('start_time', '').strip()
        end_time = data.get('end_time', '').strip()
        duration = data.get('duration', '')
        
        if not url:
            return jsonify({
                'success': False,
                'error': 'Please provide a YouTube URL'
            })
        
        # Validate YouTube URL
        if 'youtube.com' not in url and 'youtu.be' not in url:
            return jsonify({
                'success': False,
                'error': 'Please provide a valid YouTube URL'
            })
        
        # Get summarizer
        summ = get_summarizer()
        if not summ:
            return jsonify({
                'success': False,
                'error': 'OpenAI API not configured. Please set your OPENAI_API_KEY.'
            })
        
        # Process duration
        duration_int = None
        if duration and duration.isdigit():
            duration_int = int(duration)
        
        # Set default values if empty
        if not start_time:
            start_time = None
        if not end_time:
            end_time = None
            
        print(f"Processing: URL={url}, start={start_time}, end={end_time}, duration={duration_int}")
        
        # Process the video
        summary = summ.process_video_segment(
            url=url,
            start_time=start_time,
            end_time=end_time,
            duration=duration_int
        )
        
        # Extract video ID for player
        video_id = extract_video_id(summary.url)
        
        # Format response
        result = {
            'success': True,
            'data': {
                'url': summary.url,
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
                'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error in extract_knowledge: {error_msg}")
        print(f"Traceback: {traceback.format_exc()}")
        
        # Handle specific error cases
        if "transcript" in error_msg.lower():
            error_msg = "This video doesn't have available transcripts. Please try a different video."
        elif "api" in error_msg.lower():
            error_msg = "OpenAI API error. Please check your API key and try again."
        elif "video" in error_msg.lower():
            error_msg = "Could not access this video. It might be private or unavailable."
        
        return jsonify({
            'success': False,
            'error': error_msg
        })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    # Check if OpenAI API key is available
    summ = get_summarizer()
    api_available = summ is not None
    
    return jsonify({
        'status': 'healthy',
        'openai_api_configured': api_available,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Check if running in development
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print("🚀 Starting YouTube Knowledge Extraction Web App")
    print("=" * 50)
    
    # Check API key
    summ = get_summarizer()
    if summ:
        print("✅ OpenAI API configured")
    else:
        print("⚠️  OpenAI API not configured")
        print("   Please set OPENAI_API_KEY in .env file or environment")
    
    port = int(os.getenv('PORT', 5002))
    print(f"📱 Web app will be available at: http://localhost:{port}")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)