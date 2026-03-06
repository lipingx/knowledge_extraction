# Project Overview: YouTube Knowledge Extraction

## 1. Project Goal
The goal of this project is to extract structured knowledge from YouTube videos. It allows users to:
-   Input a YouTube video URL (with optional start time and duration).
-   Extract the transcript for the specified segment.
-   Summarize the content using AI (OpenAI GPT-4o-mini).
-   Extract specific entities: Books, People, Places, Facts, and Topics.
-   Save the extracted information to a database (Firebase Firestore) or local files.
-   View the results through a web interface.

## 2. Architecture & Tech Stack

### Backend
-   **Language**: Python
-   **Core Framework**: Flask (for the web application)
-   **Key Libraries**:
    -   `youtube-transcript-api`: Fetches transcripts from YouTube videos.
    -   `openai`: Uses GPT models for summarization and entity extraction.
    -   `firebase-admin`: Interacts with Firebase Firestore for data persistence.
    -   `requests`: Calls the WeChat Official Account HTTP APIs.
    -   `python-dotenv`: Manages environment variables.

### Frontend
-   **Location**: `frontend/` directory.
-   **Tech**: HTML, CSS, JavaScript (Vanilla).
-   **Features**:
    -   Video preview with embedded player.
    -   Real-time URL parsing.
    -   Display of extracted summaries and entities.

### Database
-   **System**: Firebase Firestore (NoSQL).
-   **Data Structure**:
    -   `videos`: Stores video metadata.
    -   `segments`: Stores extracted segments with transcripts and summaries.

## 3. Key Components

### `youtube_extractor.py`
-   **Purpose**: Handles the low-level interaction with YouTube.
-   **Key Class**: `YouTubeExtractor`
-   **Functions**:
    -   `parse_youtube_url(url)`: Extracts video ID and start time from various URL formats.
    -   `extract_segment(url, duration, ...)`: Fetches the transcript for a specific time range.

### `transcript_summarizer.py`
-   **Purpose**: Processes the raw transcript to generate insights.
-   **Key Class**: `TranscriptSummarizer`
-   **Functions**:
    -   `process_video_segment(...)`: Orchestrates extraction and summarization.
    -   `summarize_transcript(...)`: Calls OpenAI API to get a structured summary (JSON).
    -   `save_summary_to_firestore(...)`: Saves the result to Firebase.

### `frontend/app.py`
-   **Purpose**: The Flask web server entry point.
-   **Routes**: Handles HTTP requests from the frontend to trigger extraction and retrieval.

### `publish_to_wechat.py`
-   **Purpose**: Publishes prepared article files to a WeChat Official Account.
-   **Functions**:
    -   Reads a local article and converts it into WeChat-friendly HTML.
    -   Uploads a cover image or reuses an existing `thumb_media_id`.
    -   Creates a draft and optionally submits it for publishing.

## 4. How to Run

### Prerequisites
1.  Python 3.x installed.
2.  Firebase project set up (with `serviceAccountKey.json` if using local admin SDK).
3.  OpenAI API key.

### Setup
1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2.  Set environment variables (create a `.env` file):
    ```
    OPENAI_API_KEY=your_api_key
    GOOGLE_APPLICATION_CREDENTIALS=path/to/serviceAccountKey.json
    ```

### Running the Web App
The web application is located in the `frontend` directory.
```bash
python frontend/app.py
```
Access the app at `http://localhost:5002` (or the port specified in `app.py`).

## 5. How to Test

The project includes several test scripts to verify functionality.

### Unit & Integration Tests
Run these scripts directly with Python:

-   **Test YouTube Extraction**:
    ```bash
    python test_youtube_extractor.py
    ```
    *Verifies URL parsing and transcript fetching.*

-   **Test Summarization**:
    ```bash
    python test_summarizer.py
    ```
    *Verifies OpenAI integration (requires API key).*

-   **Test Firestore**:
    ```bash
    python test_firestore.py
    ```
    *Verifies database operations (requires Firebase credentials).*

### Manual Testing
1.  Run the web app (`python frontend/app.py`).
2.  Open the browser to the local server.
3.  Paste a YouTube URL (e.g., a TED talk).
4.  Click "Extract".
5.  Verify that the video plays, the transcript is shown, and the summary/entities appear.
