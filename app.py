from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import yt_dlp
import os
import re

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
DOWNLOAD_FOLDER = "downloads"
ALLOWED_HOSTS = ['your-frontend-domain.com', 'localhost']  # Add your allowed domains here

# Ensure download directory exists
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def validate_youtube_url(url):
    """Basic YouTube URL validation"""
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    return re.match(youtube_regex, url) is not None

@app.route('/')
def home():
    return "Welcome to YouTube Downloader Backend"

@app.route('/download', methods=['GET', 'POST'])
def download_video():
    # Handle both GET and POST requests
    if request.method == 'GET':
        youtube_url = request.args.get('url')
    else:
        data = request.get_json(silent=True) or {}
        youtube_url = data.get('url')
    
    if not youtube_url:
        return jsonify({"error": "No URL provided"}), 400
    
    if not validate_youtube_url(youtube_url):
        return jsonify({"error": "Invalid YouTube URL"}), 400
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        'quiet': True,
        'noplaylist': True,
        'extract_flat': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract video info without downloading
            info = ydl.extract_info(youtube_url, download=False)
            
            # Prepare response data
            response_data = {
                "title": info.get('title', 'Unknown Title'),
                "thumbnail": info.get('thumbnail'),
                "duration": info.get('duration'),
                "formats": []
            }
            
            # Get available formats
            if 'formats' in info:
                for fmt in info['formats']:
                    if fmt.get('url'):
                        response_data['formats'].append({
                            "format_id": fmt.get('format_id'),
                            "ext": fmt.get('ext'),
                            "quality": fmt.get('resolution', fmt.get('format_note', 'unknown')),
                            "url": fmt['url']
                        })
            
            # If no formats found, try to get the direct URL
            if not response_data['formats'] and info.get('url'):
                response_data['download_url'] = info['url']
            
            return jsonify(response_data)
            
    except yt_dlp.utils.DownloadError as e:
        return jsonify({"error": f"YouTube DL error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/downloads/<filename>', methods=['GET'])
def serve_download(filename):
    """Serve downloaded files"""
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
