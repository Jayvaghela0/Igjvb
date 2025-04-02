from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)  # CORS enable kar diya hai

# Cookies file ka path (GitHub repository me save kiya hua)
COOKIES_FILE = "cookies.txt"

@app.route('/')
def home():
    return "Welcome to YouTube Downloader Backend"

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    youtube_url = data.get("url")
    
    if not youtube_url:
        return jsonify({"error": "No URL provided"}), 400
    
    output_dir = "downloads"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Headers aur cookies set karna
    ydl_opts = {
        'format': 'best',
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'quiet': True,
        'noplaylist': True,
        'cookiefile': COOKIES_FILE,  # YouTube cookies ka use
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            download_url = info.get('url', None)
            if not download_url:
                return jsonify({"error": "Failed to fetch video URL"}), 500
            
            return jsonify({
                "title": info.get('title', 'Unknown Title'),
                "download_url": download_url
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
