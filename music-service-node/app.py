from flask import Flask, jsonify, request, Response, stream_with_context, render_template, redirect
import requests
import logging
import subprocess
import os
import tempfile

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('music-service-node')

app = Flask(__name__)

STREAMING_QUALITY = {
    'low': {'bitrate': '64k', 'format': 'mp3'},
    'medium': {'bitrate': '128k', 'format': 'mp3'},
    'high': {'bitrate': '320k', 'format': 'mp3'}
}


@app.route('/')
def index():
    return render_template('index.html')
 
@app.route('/login', methods=['POST'])
def login():
    data = {
        'username': request.form.get('username'),
        'password': request.form.get('password')
    }
    response = requests.post("http://management-user-service:8084/login", json=data)
    
    if response.status_code == 200:
        # Get the JWT token from management service response
        access_token = response.json().get('access_token')
        # Create response and set cookie
        resp = redirect('/dashboard')
        resp.set_cookie('session_token', access_token, httponly=True)
        return resp
    else:
        return render_template('index.html', message="Invalid username or password"), 401
    
@app.route('/dashboard', methods=['GET'])
def dashboard():
    return render_template('dashboard.html')

@app.route('/register', methods=['POST'])
def register():
    # Get form data instead of JSON data
    data = {
        'username': request.form.get('username'),
        'password': request.form.get('password'),
        'email': request.form.get('email')
    }
    
    required_fields = ['username', 'password', 'email']
    
    for field in required_fields:
        if not data[field]:
            return render_template('index.html', message=f"Missing required field: {field}"), 400
            
    response = requests.post("http://management-user-service:8084/register", json=data)
    if response.status_code == 200 or response.status_code == 201:
        return render_template('index.html', message="User registered successfully")
    else:
        return render_template('index.html', message=response.content.decode('utf-8'))

@app.route('/users/me', methods=['GET'])
def get_current_user():
    response = requests.get("http://management-user-service:8084/users/me")
    return response.json(), response.status_code

@app.route('/users/me', methods=['PUT'])
def update_user():
    # Get form data instead of JSON data
    data = {
        'username': request.form.get('username'),
        'password': request.form.get('password')
    }
    response = requests.put("http://management-user-service:8084/users/me", json=data)
    return response.json(), response.status_code

@app.route('/users/me/password', methods=['PUT'])
def change_password():
    # Get form data instead of JSON data
    data = {
        'username': request.form.get('username'),
        'password': request.form.get('password')
    }
    response = requests.put("http://management-user-service:8084/users/me/password", json=data)
    return response.json(), response.status_code

########################################################
# Songs management
########################################################

@app.route('/songs', methods=['GET'])
def get_songs():
    response = requests.get("http://management-user-service:8084/songs")
    return render_template('dashboard.html', songs=response.json())

@app.route('/songs/<int:song_id>', methods=['GET']) 
def get_song(song_id):
    response = requests.get(f"http://management-user-service:8084/songs/{song_id}")
    return response.json(), response.status_code

@app.route('/artists/<int:artist_id>/songs', methods=['GET'])
def get_artist_songs(artist_id):
    response = requests.get(f"http://management-user-service:8084/artists/{artist_id}/songs")
    return response.json(), response.status_code

@app.route('/song', methods=['GET'])
def get_songs_by_limit_and_offset():
    data = request.json
    limit = data.get('limit', 10)
    offset = data.get('offset', 0)
    try:
        response = requests.get("http://storage-service:8083/files", params={"limit": limit, "offset": offset})
        return response.json(), response.status_code
    except Exception as e:
        logger.error(f"Error getting songs: {str(e)}")
        return jsonify({"error": "Error getting songs"}), 500

@app.route('/download/<int:song_id>', methods=['GET'])
def download_song(song_id):
    try:
        response = requests.get(f"http://storage-service:8083/files/{song_id}")
        return response.json(), response.status_code
    except Exception as e:
        logger.error(f"Error downloading song: {str(e)}")
        return jsonify({"error": "Error downloading song"}), 500
    
@app.route('/upload', methods=['POST'])
def upload_song():
    try:
        # Get JWT token from cookie and ensure proper Bearer format
        auth_token = request.cookies.get('session_token')
        if not auth_token:
            return jsonify({"error": "Missing Authorization"}), 401
        
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        # Upload to storage service first
        response_storage = requests.post(
            "http://storage-service:8083/upload", 
            files={"file": file}
        )
        if response_storage.status_code != 201:
            return response_storage.json(), response_storage.status_code
        
        # Forward auth header to management service
        metadata = {
            'title': request.form.get('title', file.filename),
            'artist_id': request.form.get('artist_id'),
            'album_id': request.form.get('album_id'),
            'genre': request.form.get('genre'),
            'duration': request.form.get('duration'),
            'file_path': response_storage.json()['id']
        }
        
        response_db = requests.post(
            "http://management-user-service:8084/api/add_song", 
            json=metadata,
            headers=headers
        )
        return response_db.json(), response_db.status_code

    except Exception as e:
        logger.error(f"Error uploading song: {str(e)}")
        return jsonify({"error": "Error uploading song"}), 500
       
@app.route('/api/stream/<int:song_id>', methods=['GET'])
def stream_song(song_id):
    try:
        quality = request.args.get('quality', 'medium')
        response = requests.get(f"http://management-user-service:8084/songs/{song_id}")
        song = response.json()
        if not song:
            return jsonify({"error": "Song not found"}), 404
        
        file_id = song['file_path'].split('/')[-1]
        storage_url = f"http://storage-service:8083/files/{file_id}"

        quality_settings = STREAMING_QUALITY[quality]

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name

            with requests.get(storage_url, stream=True) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)

        def generate():
            try:
                cmd = [
                    'ffmpeg',
                    '-i', temp_path,
                    '-b:a', quality_settings['bitrate'],
                    '-f', quality_settings['format'],
                    '-'
                ]

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                while True:
                    data = process.stdout.read(4096)
                    if not data:
                        break
                    yield data

                process.wait()
                os.unlink(temp_path)
            except Exception as e:
                logger.error(f"Error in transcoding: {e}")
                if os.path.exists(temp_path):
                    os.unlink(temp_path)    

        return Response(
            stream_with_context(generate()),
            content_type=f'audio/{quality_settings["format"]}'
        )
    except Exception as e:
        logger.error(f"Error streaming song: {str(e)}")
        return jsonify({"error": "Error streaming song"}), 500
                
        

@app.route('/metadata/<int:song_id>', methods=['GET'])
def get_song_metadata(song_id):
    try:
        response = requests.get(f"http://storage-service:8083/metadata/{song_id}")
        return response.json(), response.status_code
    except Exception as e:
        logger.error(f"Error getting song metadata: {str(e)}")
        return jsonify({"error": "Error getting song metadata"}), 500
    
@app.route('/delete/<int:song_id>', methods=['DELETE'])
def delete_song(song_id):
    try:
        response = requests.delete(f"http://storage-service:8083/files/{song_id}")
        return response.json(), response.status_code
    except Exception as e:
        logger.error(f"Error deleting song: {str(e)}")
        return jsonify({"error": "Error deleting song"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)