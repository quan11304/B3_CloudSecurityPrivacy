from flask import Flask, jsonify, request, Response, stream_with_context, render_template, redirect
import requests
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('music-service-node')

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    response = requests.post("http://management-user-service:8084/login", json=data)
    if response.status_code == 200:
        return render_template('dashboard.html')
    else:
        return render_template('index.html', message="Invalid username or password")
    
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
    data = request.json
    response = requests.put("http://management-user-service:8084/users/me", json=data)
    return response.json(), response.status_code

@app.route('/users/me/password', methods=['PUT'])
def change_password():
    data = request.json
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

@app.route('/songs', methods=['POST'])
def add_song():
    data = request.json
    response = requests.post("http://management-user-service:8084/songs", data=data)
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
        file = request.files['file']
        response = requests.post("http://storage-service:8083/upload", files={"file": file})
        return response.json(), response.status_code
    except Exception as e:
        logger.error(f"Error uploading song: {str(e)}")
        return jsonify({"error": "Error uploading song"}), 500

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