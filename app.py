from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests
import os
import threading
import time
import uuid

app = Flask(__name__)
CORS(app)  # CORS enable karo taaki frontend se request accept ho

# Download ke liye folder setup karo
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# 3 minutes ke baad file delete karne ke liye function
def delete_file_after_delay(file_path, delay):
    time.sleep(delay)
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"File deleted: {file_path}")  # Debug ke liye

# Instagram video download karne ka route
@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        url = data.get('url')

        # ✅ URL validation
        if 'instagram.com' not in url:
            return jsonify({'error': 'Invalid URL'}), 400

        headers = {
            'User-Agent': 'Mozilla/5.0'  # ✅ User-Agent spoofing
        }

        # ✅ Video ko download karo
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch video'}), 400

        # ✅ Unique file name generate karo taaki overwrite na ho
        file_name = f"instagram_video_{uuid.uuid4().hex}.mp4"
        file_path = os.path.join(DOWNLOAD_FOLDER, file_name)

        with open(file_path, 'wb') as file:
            file.write(response.content)

        # ✅ Debug response
        print(f"Video saved at: {file_path}")

        # ✅ 3 minutes ke baad file delete karne ke liye thread start karo
        threading.Thread(target=delete_file_after_delay, args=(file_path, 180), daemon=True).start()

        # ✅ Direct download link generate karo
        download_link = f"{request.host_url}download-file/{file_name}"
        print({'download_link': download_link})  # Debug ke liye

        return jsonify({'download_link': download_link})

    except Exception as e:
        print(f"Error: {str(e)}")  # Debug ke liye
        return jsonify({'error': str(e)}), 500

# ✅ Downloaded file ko serve karne ke liye route
@app.route('/download-file/<filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
