// YouTube Knowledge Extraction Web App JavaScript

class YouTubeExtractor {
    constructor() {
        this.form = document.getElementById('extractForm');
        this.loadingState = document.getElementById('loadingState');
        this.resultsSection = document.getElementById('resultsSection');
        this.errorSection = document.getElementById('errorSection');
        this.extractBtn = document.getElementById('extractBtn');
        this.videoPreview = document.getElementById('videoPreview');
        this.urlInput = document.getElementById('youtube-url');
        
        this.currentResults = null;
        this.currentVideoData = null;
        this.previewVideoData = null;
        
        this.init();
    }
    
    init() {
        // Form submission
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.extractKnowledge();
        });
        
        // Retry button
        document.getElementById('retryBtn').addEventListener('click', () => {
            this.hideError();
        });
        
        // Transcript toggle
        document.getElementById('transcriptToggle').addEventListener('click', () => {
            this.toggleTranscript();
        });
        
        // Export buttons
        document.getElementById('exportJson').addEventListener('click', () => {
            this.exportResults('json');
        });
        
        document.getElementById('exportText').addEventListener('click', () => {
            this.exportResults('text');
        });
        
        // Video player controls
        document.getElementById('embedBtn').addEventListener('click', () => {
            this.loadEmbeddedVideo();
        });
        
        document.getElementById('youtubeBtn').addEventListener('click', () => {
            this.openInYouTube();
        });
        
        document.getElementById('timestampBtn').addEventListener('click', () => {
            this.jumpToTimestamp();
        });
        
        // Preview controls
        document.getElementById('previewEmbedBtn').addEventListener('click', () => {
            this.loadPreviewEmbed();
        });
        
        document.getElementById('previewYoutubeBtn').addEventListener('click', () => {
            this.openPreviewInYouTube();
        });
        
        // URL input monitoring
        this.setupURLMonitoring();
        
        // Auto-resize URL input
        this.setupAutoResize();
    }
    
    setupAutoResize() {
        this.urlInput.addEventListener('paste', () => {
            setTimeout(() => {
                if (this.urlInput.value.length > 50) {
                    this.urlInput.style.height = 'auto';
                    this.urlInput.style.height = Math.min(this.urlInput.scrollHeight, 100) + 'px';
                }
            }, 10);
        });
    }
    
    setupURLMonitoring() {
        let debounceTimer;
        
        const handleURLChange = () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                const url = this.urlInput.value.trim();
                if (this.isValidYouTubeURL(url)) {
                    this.showVideoPreview(url);
                } else if (url === '') {
                    this.hideVideoPreview();
                }
            }, 500); // 500ms debounce
        };
        
        // Monitor various input events
        this.urlInput.addEventListener('input', handleURLChange);
        this.urlInput.addEventListener('paste', () => {
            // Handle paste with slight delay to get pasted content
            setTimeout(handleURLChange, 10);
        });
        this.urlInput.addEventListener('blur', handleURLChange);
    }
    
    isValidYouTubeURL(url) {
        return url && (url.includes('youtube.com') || url.includes('youtu.be')) && url.length > 10;
    }
    
    async extractKnowledge() {
        const formData = new FormData(this.form);
        const data = {
            url: formData.get('url').trim(),
            start_time: formData.get('start_time').trim(),
            end_time: formData.get('end_time').trim(),
            duration: formData.get('duration').trim()
        };
        
        // Validation
        if (!data.url) {
            this.showError('Please enter a YouTube URL');
            return;
        }
        
        if (!data.url.includes('youtube.com') && !data.url.includes('youtu.be')) {
            this.showError('Please enter a valid YouTube URL');
            return;
        }
        
        this.showLoading();
        
        try {
            const response = await fetch('/extract', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showResults(result.data);
            } else {
                this.showError(result.error);
            }
            
        } catch (error) {
            console.error('Error:', error);
            this.showError('Network error. Please check your connection and try again.');
        }
    }
    
    showLoading() {
        this.hideAllSections();
        this.loadingState.classList.remove('hidden');
        this.extractBtn.disabled = true;
        this.extractBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>Processing...</span>';
    }
    
    showResults(data) {
        this.hideAllSections();
        this.currentResults = data;
        
        // Extract and store video information
        this.currentVideoData = this.extractVideoInfo(data.url, data.start_time, data.end_time);
        
        // Update meta info
        const metaInfo = document.getElementById('metaInfo');
        const timeRange = data.start_time !== data.end_time ? 
            `${data.start_time} - ${data.end_time}` : 
            `From ${data.start_time}`;
        metaInfo.innerHTML = `
            <div><strong>Time Range:</strong> ${timeRange}</div>
            <div><strong>Processed:</strong> ${data.processed_at}</div>
        `;
        
        // Setup video player
        this.setupVideoPlayer(data);
        
        // Update summary
        document.getElementById('summaryContent').textContent = data.summary || 'No summary available';
        
        // Update entity lists
        this.updateEntityList('booksList', 'booksCount', data.books);
        this.updateEntityList('peopleList', 'peopleCount', data.people);
        this.updateEntityList('placesList', 'placesCount', data.places);
        this.updateEntityList('factsList', 'factsCount', data.facts);
        this.updateEntityList('topicsList', 'topicsCount', data.topics);
        
        // Update transcript
        document.getElementById('transcriptText').textContent = data.transcription || 'No transcript available';
        
        this.resultsSection.classList.remove('hidden');
        this.resetButton();
        
        // Scroll to results
        this.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    updateEntityList(listId, countId, items) {
        const listElement = document.getElementById(listId);
        const countElement = document.getElementById(countId);
        
        listElement.innerHTML = '';
        countElement.textContent = items ? items.length : 0;
        
        if (items && items.length > 0) {
            items.forEach(item => {
                const li = document.createElement('li');
                li.textContent = item;
                listElement.appendChild(li);
            });
        }
    }
    
    showError(message) {
        this.hideAllSections();
        document.getElementById('errorMessage').textContent = message;
        this.errorSection.classList.remove('hidden');
        this.resetButton();
        
        // Scroll to error
        this.errorSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    hideError() {
        this.errorSection.classList.add('hidden');
    }
    
    hideAllSections() {
        this.loadingState.classList.add('hidden');
        this.resultsSection.classList.add('hidden');
        this.errorSection.classList.add('hidden');
    }
    
    showVideoPreview(url) {
        // Extract video info for preview
        this.previewVideoData = this.extractVideoInfoForPreview(url);
        
        if (!this.previewVideoData.videoId) {
            this.hideVideoPreview();
            return;
        }
        
        // Update preview info
        document.getElementById('previewVideoId').textContent = `Video ID: ${this.previewVideoData.videoId}`;
        document.getElementById('previewDirectLink').href = this.previewVideoData.cleanUrl;
        
        // Show preview section
        this.videoPreview.classList.remove('hidden');
        
        // Load embedded player by default
        this.loadPreviewEmbed();
        
        // Scroll to preview
        this.videoPreview.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    hideVideoPreview() {
        this.videoPreview.classList.add('hidden');
        this.previewVideoData = null;
        
        // Clear iframe
        const previewFrame = document.getElementById('previewFrame');
        previewFrame.src = '';
    }
    
    extractVideoInfoForPreview(url) {
        // Extract video ID from URL
        let videoId = '';
        if (url.includes('youtube.com/watch?v=')) {
            videoId = url.split('v=')[1].split('&')[0];
        } else if (url.includes('youtu.be/')) {
            videoId = url.split('youtu.be/')[1].split('?')[0];
        }
        
        return {
            videoId: videoId,
            originalUrl: url,
            cleanUrl: `https://www.youtube.com/watch?v=${videoId}`,
            embedUrl: `https://www.youtube.com/embed/${videoId}?autoplay=0&rel=0`
        };
    }
    
    loadPreviewEmbed() {
        if (!this.previewVideoData) {
            return;
        }
        
        const previewFrame = document.getElementById('previewFrame');
        const embedBtn = document.getElementById('previewEmbedBtn');
        const youtubeBtn = document.getElementById('previewYoutubeBtn');
        
        // Update button states
        embedBtn.classList.add('active');
        youtubeBtn.classList.remove('active');
        
        // Load embedded video
        previewFrame.src = this.previewVideoData.embedUrl;
        
        this.showToast('Video preview loaded');
    }
    
    openPreviewInYouTube() {
        if (!this.previewVideoData) {
            return;
        }
        
        const embedBtn = document.getElementById('previewEmbedBtn');
        const youtubeBtn = document.getElementById('previewYoutubeBtn');
        
        // Update button states
        embedBtn.classList.remove('active');
        youtubeBtn.classList.add('active');
        
        // Open in YouTube
        window.open(this.previewVideoData.cleanUrl, '_blank');
        
        this.showToast('Opening in YouTube...');
        
        // Reset button state after a moment
        setTimeout(() => {
            embedBtn.classList.add('active');
            youtubeBtn.classList.remove('active');
        }, 1000);
    }
    
    resetButton() {
        this.extractBtn.disabled = false;
        this.extractBtn.innerHTML = '<i class="fas fa-magic"></i><span>Extract Knowledge</span>';
    }
    
    toggleTranscript() {
        const transcriptContent = document.getElementById('transcriptContent');
        const toggleBtn = document.getElementById('transcriptToggle');
        const icon = toggleBtn.querySelector('i');
        
        if (transcriptContent.classList.contains('collapsed')) {
            transcriptContent.classList.remove('collapsed');
            icon.style.transform = 'rotate(0deg)';
            toggleBtn.classList.remove('collapsed');
        } else {
            transcriptContent.classList.add('collapsed');
            icon.style.transform = 'rotate(-90deg)';
            toggleBtn.classList.add('collapsed');
        }
    }
    
    exportResults(format) {
        if (!this.currentResults) {
            this.showError('No results to export');
            return;
        }
        
        const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
        const filename = `youtube_extraction_${timestamp}`;
        
        if (format === 'json') {
            this.downloadFile(
                JSON.stringify(this.currentResults, null, 2),
                `${filename}.json`,
                'application/json'
            );
        } else if (format === 'text') {
            const textContent = this.formatAsText(this.currentResults);
            this.downloadFile(
                textContent,
                `${filename}.txt`,
                'text/plain'
            );
        }
    }
    
    formatAsText(data) {
        const lines = [];
        lines.push('YOUTUBE KNOWLEDGE EXTRACTION RESULTS');
        lines.push('=' .repeat(50));
        lines.push(`URL: ${data.url}`);
        lines.push(`Time Range: ${data.start_time} - ${data.end_time}`);
        lines.push(`Processed: ${data.processed_at}`);
        lines.push('');
        
        lines.push('SUMMARY:');
        lines.push('-'.repeat(20));
        lines.push(data.summary || 'No summary available');
        lines.push('');
        
        if (data.books && data.books.length > 0) {
            lines.push(`BOOKS & PUBLICATIONS (${data.books.length}):`);
            lines.push('-'.repeat(30));
            data.books.forEach(book => lines.push(`• ${book}`));
            lines.push('');
        }
        
        if (data.people && data.people.length > 0) {
            lines.push(`PEOPLE MENTIONED (${data.people.length}):`);
            lines.push('-'.repeat(25));
            data.people.forEach(person => lines.push(`• ${person}`));
            lines.push('');
        }
        
        if (data.places && data.places.length > 0) {
            lines.push(`PLACES MENTIONED (${data.places.length}):`);
            lines.push('-'.repeat(25));
            data.places.forEach(place => lines.push(`• ${place}`));
            lines.push('');
        }
        
        if (data.facts && data.facts.length > 0) {
            lines.push(`KEY FACTS & INSIGHTS (${data.facts.length}):`);
            lines.push('-'.repeat(30));
            data.facts.forEach(fact => lines.push(`• ${fact}`));
            lines.push('');
        }
        
        if (data.topics && data.topics.length > 0) {
            lines.push(`MAIN TOPICS (${data.topics.length}):`);
            lines.push('-'.repeat(20));
            data.topics.forEach(topic => lines.push(`• ${topic}`));
            lines.push('');
        }
        
        lines.push('FULL TRANSCRIPT:');
        lines.push('=' .repeat(50));
        lines.push(data.transcription || 'No transcript available');
        
        return lines.join('\\n');
    }
    
    downloadFile(content, filename, contentType) {
        const blob = new Blob([content], { type: contentType });
        const url = window.URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        window.URL.revokeObjectURL(url);
        
        // Show success message
        this.showToast(`Downloaded ${filename}`);
    }
    
    showToast(message) {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #28a745;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 500;
            z-index: 10000;
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.3s ease;
        `;
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateY(0)';
        }, 10);
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(20px)';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);
    }
    
    // Video Player Methods
    extractVideoInfo(url, startTime, endTime) {
        // Extract video ID from URL
        let videoId = '';
        if (url.includes('youtube.com/watch?v=')) {
            videoId = url.split('v=')[1].split('&')[0];
        } else if (url.includes('youtu.be/')) {
            videoId = url.split('youtu.be/')[1].split('?')[0];
        }
        
        // Convert time strings to seconds for calculations
        const startSeconds = this.parseTimeToSeconds(startTime);
        const endSeconds = this.parseTimeToSeconds(endTime);
        
        return {
            videoId: videoId,
            originalUrl: url,
            startTime: startTime,
            endTime: endTime,
            startSeconds: startSeconds,
            endSeconds: endSeconds,
            cleanUrl: `https://www.youtube.com/watch?v=${videoId}`,
            timestampUrl: `https://www.youtube.com/watch?v=${videoId}&t=${startSeconds}s`,
            embedUrl: `https://www.youtube.com/embed/${videoId}?start=${startSeconds}&end=${endSeconds}&autoplay=0&rel=0`
        };
    }
    
    parseTimeToSeconds(timeStr) {
        // Remove 's' suffix if present
        timeStr = timeStr.replace('s', '');
        
        // If it's already a number, return it
        if (!isNaN(timeStr)) {
            return parseInt(timeStr);
        }
        
        // Parse HH:MM:SS or MM:SS format
        const parts = timeStr.split(':');
        let seconds = 0;
        
        if (parts.length === 3) {
            // HH:MM:SS
            seconds = parseInt(parts[0]) * 3600 + parseInt(parts[1]) * 60 + parseInt(parts[2]);
        } else if (parts.length === 2) {
            // MM:SS
            seconds = parseInt(parts[0]) * 60 + parseInt(parts[1]);
        }
        
        return seconds;
    }
    
    formatSecondsToTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    }
    
    setupVideoPlayer(data) {
        if (!this.currentVideoData || !this.currentVideoData.videoId) {
            return;
        }
        
        // Update time display
        const timeRange = document.getElementById('timeRange');
        const startFormatted = this.formatSecondsToTime(this.currentVideoData.startSeconds);
        const endFormatted = this.formatSecondsToTime(this.currentVideoData.endSeconds);
        timeRange.textContent = `${startFormatted} - ${endFormatted}`;
        
        // Update links
        const directLink = document.getElementById('directLink');
        const timestampLink = document.getElementById('timestampLink');
        
        directLink.href = this.currentVideoData.cleanUrl;
        timestampLink.href = this.currentVideoData.timestampUrl;
        
        // Reset video player state
        this.resetVideoPlayer();
    }
    
    resetVideoPlayer() {
        const videoFrame = document.getElementById('videoFrame');
        const videoPlaceholder = document.getElementById('videoPlaceholder');
        const embedBtn = document.getElementById('embedBtn');
        const buttons = document.querySelectorAll('.video-btn');
        
        // Reset button states
        buttons.forEach(btn => btn.classList.remove('active'));
        embedBtn.classList.add('active');
        
        // Auto-load embedded player by default
        this.loadEmbeddedVideo();
    }
    
    loadEmbeddedVideo() {
        if (!this.currentVideoData) {
            this.showToast('No video data available');
            return;
        }
        
        const videoFrame = document.getElementById('videoFrame');
        const videoPlaceholder = document.getElementById('videoPlaceholder');
        const embedBtn = document.getElementById('embedBtn');
        const buttons = document.querySelectorAll('.video-btn');
        
        // Update button states
        buttons.forEach(btn => btn.classList.remove('active'));
        embedBtn.classList.add('active');
        
        // Load embedded video
        videoFrame.src = this.currentVideoData.embedUrl;
        videoFrame.classList.remove('hidden');
        videoPlaceholder.classList.add('hidden');
        
        this.showToast('Video loaded successfully');
    }
    
    openInYouTube() {
        if (!this.currentVideoData) {
            this.showToast('No video data available');
            return;
        }
        
        const youtubeBtn = document.getElementById('youtubeBtn');
        const buttons = document.querySelectorAll('.video-btn');
        
        // Update button states
        buttons.forEach(btn => btn.classList.remove('active'));
        youtubeBtn.classList.add('active');
        
        // Open in YouTube
        window.open(this.currentVideoData.cleanUrl, '_blank');
        
        this.showToast('Opening in YouTube...');
        
        // Reset button state after a moment
        setTimeout(() => {
            buttons.forEach(btn => btn.classList.remove('active'));
            document.getElementById('embedBtn').classList.add('active');
        }, 1000);
    }
    
    jumpToTimestamp() {
        if (!this.currentVideoData) {
            this.showToast('No video data available');
            return;
        }
        
        const timestampBtn = document.getElementById('timestampBtn');
        const buttons = document.querySelectorAll('.video-btn');
        
        // Update button states
        buttons.forEach(btn => btn.classList.remove('active'));
        timestampBtn.classList.add('active');
        
        // Open YouTube with timestamp
        window.open(this.currentVideoData.timestampUrl, '_blank');
        
        this.showToast('Opening at timestamp...');
        
        // Reset button state after a moment
        setTimeout(() => {
            buttons.forEach(btn => btn.classList.remove('active'));
            document.getElementById('embedBtn').classList.add('active');
        }, 1000);
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new YouTubeExtractor();
    
    // Add some helpful features
    addURLPatternHelper();
    addKeyboardShortcuts();
});

function addURLPatternHelper() {
    const urlInput = document.getElementById('youtube-url');
    const helpText = document.createElement('small');
    helpText.textContent = 'Supports: youtube.com/watch?v=... or youtu.be/... URLs';
    helpText.style.color = 'var(--text-muted)';
    helpText.style.marginTop = '5px';
    helpText.style.display = 'block';
    
    urlInput.parentNode.appendChild(helpText);
}

function addKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + Enter to submit form
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            const form = document.getElementById('extractForm');
            if (!document.getElementById('extractBtn').disabled) {
                form.dispatchEvent(new Event('submit'));
            }
        }
        
        // Escape to hide error
        if (e.key === 'Escape') {
            const errorSection = document.getElementById('errorSection');
            if (!errorSection.classList.contains('hidden')) {
                errorSection.classList.add('hidden');
            }
        }
    });
}