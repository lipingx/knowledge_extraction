 the Flask app automatically uses files in static/ and templates/. Here's how the web app works at a high level:

  Flask File Structure

  - templates/ - HTML templates rendered by Flask (line 41: render_template('index.html'))
  - static/ - CSS, JavaScript, images served directly by Flask
  - Flask automatically serves these without explicit routes

  App Architecture

  Frontend (Browser):
  1. User visits http://localhost:5002
  2. Gets templates/index.html with embedded static/js/app.js and static/css/style.css
  3. JavaScript handles URL input, video preview, form submission

  Backend (Flask):
  1. GET / - Serves main page (index.html)
  2. POST /extract - Processes YouTube URL, calls OpenAI, returns JSON
  3. GET /health - Health check endpoint

  Request Flow

  Browser → Flask → TranscriptSummarizer → YouTube API + OpenAI → Flask → Browser

  Processing Chain:
  1. User enters YouTube URL in web form
  2. JavaScript sends POST to /extract endpoint
  3. Flask calls TranscriptSummarizer.process_video_segment()
  4. Summarizer fetches transcript + calls OpenAI for entity extraction
  5. Flask returns structured JSON (books, people, facts, etc.)
  6. JavaScript updates page with results + embedded video player

  The app is a single-page application with real-time video preview and knowledge extraction.