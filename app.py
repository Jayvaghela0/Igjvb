from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import requests
from io import BytesIO

app = Flask(__name__)
CORS(app)

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    youtube_url = data.get("url")
    
    if not youtube_url:
        return jsonify({"error": "No URL provided"}), 400
    
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'noplaylist': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            download_url = info.get('url')
            
            if not download_url:
                return jsonify({"error": "Failed to get download URL"}), 500
            
            # Download the file through your server
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://www.youtube.com/'
            }
            
            response = requests.get(download_url, headers=headers, stream=True)
            
            if response.status_code != 200:
                return jsonify({"error": "Failed to fetch video content"}), 500
                
            # Stream the file to client
            file_data = BytesIO(response.content)
            return send_file(
                file_data,
                mimetype='video/mp4',
                as_attachment=True,
                download_name=f"{info.get('title', 'video')}.mp4"
            )
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
