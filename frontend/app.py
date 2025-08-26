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
        
        # Save to Firebase Firestore (background operation)
        firestore_id = None
        try:
            firestore_id = summ.save_summary_to_firestore(
                summary=summary,
                tags=['web-app', 'knowledge-extraction'],
                user_notes=f'Extracted via web app on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            )
            print(f"✓ Summary saved to Firestore with ID: {firestore_id}")
        except Exception as firestore_error:
            print(f"⚠️  Failed to save to Firestore: {firestore_error}")
            # Continue without failing the request
        
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
                'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'firestore_id': firestore_id  # Include for potential future use
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
    
    # Check Firebase connectivity
    firebase_available = False
    try:
        from storage import get_storage_client
        firebase_client = get_storage_client()
        stats = firebase_client.get_stats()
        firebase_available = True
    except Exception:
        pass
    
    return jsonify({
        'status': 'healthy',
        'openai_api_configured': api_available,
        'firebase_available': firebase_available,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/summaries', methods=['GET'])
def list_summaries():
    """List stored summaries with optional filtering"""
    try:
        from storage import get_storage_client
        
        # Get query parameters
        query = request.args.get('query', '').strip()
        video_id = request.args.get('video_id', '').strip()
        tags = request.args.getlist('tags')
        limit = min(int(request.args.get('limit', 20)), 100)  # Max 100 results
        
        # Build filters
        filters = {}
        if video_id:
            filters['video_id'] = video_id
        if tags:
            filters['tags'] = tags
        
        # Search segments
        firebase_client = get_storage_client()
        segments = firebase_client.search_segments(
            query=query if query else None,
            filters=filters if filters else None,
            limit=limit
        )
        
        # Format results (remove large text fields for list view)
        formatted_summaries = []
        for segment in segments:
            # Calculate fields on-demand
            video_id = segment.get('video_id', '')
            start_time = segment.get('start_time', '')
            end_time = segment.get('end_time', '')
            
            # Calculate duration from time strings
            duration = 0
            try:
                if start_time and end_time:
                    start_seconds = int(start_time.replace('s', '')) if 's' in start_time else 0
                    end_seconds = int(end_time.replace('s', '')) if 's' in end_time else 0
                    duration = end_seconds - start_seconds
            except:
                pass
            
            # Calculate entity counts on-demand
            entity_counts = {
                'books': len(segment.get('books', [])),
                'people': len(segment.get('people', [])),
                'places': len(segment.get('places', [])),
                'facts': len(segment.get('facts', [])),
                'topics': len(segment.get('topics', []))
            }
            
            # Construct URL on-demand
            url = f"https://www.youtube.com/watch?v={video_id}&t={start_time.replace('s', '')}" if video_id and start_time else ''
            
            formatted = {
                'id': segment.get('id'),
                'video_id': video_id,
                'url': url,
                'start_time': start_time,
                'end_time': end_time,
                'duration': duration,
                'tags': segment.get('tags', []),
                'entity_counts': entity_counts,
                'created_at': segment.get('created_at'),
                'summary': segment.get('summary', ''),
                'summary_preview': segment.get('summary', '')[:200] + '...' if len(segment.get('summary', '')) > 200 else segment.get('summary', ''),
                'facts': segment.get('facts', []),
                'books': segment.get('books', []),
                'people': segment.get('people', []),
                'places': segment.get('places', []),
                'topics': segment.get('topics', [])
            }
            formatted_summaries.append(formatted)
        
        return jsonify({
            'success': True,
            'data': {
                'summaries': formatted_summaries,
                'count': len(formatted_summaries),
                'query': query,
                'filters': filters
            }
        })
        
    except ImportError:
        return jsonify({
            'success': False,
            'error': 'Firebase storage not available'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/summaries/<summary_id>', methods=['GET'])
def get_summary(summary_id):
    """Get a specific summary by ID"""
    try:
        from storage import get_storage_client
        
        firebase_client = get_storage_client()
        segment = firebase_client.get_complete_segment(summary_id)
        
        if not segment:
            return jsonify({
                'success': False,
                'error': 'Summary not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': segment
        })
        
    except ImportError:
        return jsonify({
            'success': False,
            'error': 'Firebase storage not available'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/stats', methods=['GET'])
def get_storage_stats():
    """Get storage statistics"""
    try:
        from storage import get_storage_client
        
        firebase_client = get_storage_client()
        stats = firebase_client.get_stats()
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except ImportError:
        return jsonify({
            'success': False,
            'error': 'Firebase storage not available'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/videos/<video_id>/summaries', methods=['GET'])
def get_video_summaries(video_id):
    """Get all summaries for a specific video"""
    try:
        from storage import get_storage_client
        
        firebase_client = get_storage_client()
        segments = firebase_client.get_segments_by_video(video_id)
        
        return jsonify({
            'success': True,
            'data': {
                'video_id': video_id,
                'segments': segments,
                'count': len(segments)
            }
        })
        
    except ImportError:
        return jsonify({
            'success': False,
            'error': 'Firebase storage not available'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
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