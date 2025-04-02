from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import yt_dlp
import os
import re
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
DOWNLOAD_FOLDER = "downloads"
COOKIES_FILE = "cookies.txt"
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB limit for uploads

# Ensure directories exist
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def validate_youtube_url(url):
    """Validate YouTube URL"""
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    return re.match(youtube_url, url) is not None

def get_ydl_options():
    """Return YouTube DL options with cookies if available"""
    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        'quiet': True,
        'noplaylist': True,
        'extract_flat': False,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'referer': 'https://www.youtube.com/',
    }
    
    if os.path.exists(COOKIES_FILE):
        ydl_opts['cookiefile'] = COOKIES_FILE
        print(f"Using cookies from {COOKIES_FILE}")
    else:
        print("Warning: No cookies.txt file found")
    
    return ydl_opts

@app.route('/')
def home():
    return {
        "status": "running",
        "service": "YouTube Downloader API",
        "version": "1.2",
        "timestamp": datetime.now().isoformat()
    }

@app.route('/info', methods=['GET', 'POST'])
def video_info():
    """Get video information without downloading"""
    if request.method == 'GET':
        youtube_url = request.args.get('url')
    else:
        data = request.get_json(silent=True) or {}
        youtube_url = data.get('url')
    
    if not youtube_url:
        return jsonify({"error": "No YouTube URL provided"}), 400
    
    if not validate_youtube_url(youtube_url):
        return jsonify({"error": "Invalid YouTube URL"}), 400
    
    try:
        with yt_dlp.YoutubeDL(get_ydl_options()) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            
            response = {
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "duration": info.get('duration'),
                "uploader": info.get('uploader'),
                "view_count": info.get('view_count'),
                "formats": [],
                "webpage_url": info.get('webpage_url')
            }
            
            for fmt in info.get('formats', []):
                if fmt.get('url'):
                    response['formats'].append({
                        "format_id": fmt.get('format_id'),
                        "ext": fmt.get('ext'),
                        "resolution": fmt.get('resolution'),
                        "filesize": fmt.get('filesize'),
                        "url": fmt.get('url')
                    })
            
            return jsonify(response)
    
    except yt_dlp.utils.DownloadError as e:
        return jsonify({"error": f"YouTube DL error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/download', methods=['GET', 'POST'])
def download_video():
    """Download video in requested format"""
    if request.method == 'GET':
        youtube_url = request.args.get('url')
        format_id = request.args.get('format')
    else:
        data = request.get_json(silent=True) or {}
        youtube_url = data.get('url')
        format_id = data.get('format')
    
    if not youtube_url:
        return jsonify({"error": "No YouTube URL provided"}), 400
    
    try:
        ydl_opts = get_ydl_options()
        if format_id:
            ydl_opts['format'] = format_id
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            filename = ydl.prepare_filename(info)
            
            return jsonify({
                "status": "success",
                "title": info.get('title'),
                "filename": os.path.basename(filename),
                "download_url": f"/downloads/{os.path.basename(filename)}",
                "file_size": os.path.getsize(filename)
            })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/downloads/<path:filename>')
def serve_file(filename):
    """Serve downloaded files"""
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
