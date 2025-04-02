from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)  # CORS enable kar diya hai

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
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'quiet': True,
        'noplaylist': True,
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
