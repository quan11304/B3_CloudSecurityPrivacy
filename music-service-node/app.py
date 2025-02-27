from flask import Flask, jsonify, request, Response, stream_with_context, render_template, redirect
import requests
import logging
import subprocess
import os
import tempfile
import datetime

# Cấu hình logging
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

# Hàm gửi log đến Logstash
def send_log_to_logstash(log_data):
    logstash_url = "http://logstash:5000"  # Địa chỉ Logstash trong Docker network
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(logstash_url, json=log_data, headers=headers)
        response.raise_for_status()
        logger.info(f"Log sent to Logstash: {log_data}")
    except Exception as e:
        logger.error(f"Failed to send log to Logstash: {str(e)}")

# Middleware để log mọi request
@app.before_request
def log_request():
    log_data = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "level": "INFO",
        "message": f"Incoming request: {request.method} {request.path}",
        "app": "music-service",
        "ip": request.remote_addr,
        "user_agent": request.headers.get('User-Agent')
    }
    send_log_to_logstash(log_data)

# Middleware để log mọi response
@app.after_request
def log_response(response):
    log_data = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "level": "INFO",
        "message": f"Outgoing response: {response.status}",
        "app": "music-service",
        "ip": request.remote_addr,
        "user_agent": request.headers.get('User-Agent')
    }
    send_log_to_logstash(log_data)
    return response

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

    log_data = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "app": "music-service",
        "ip": request.remote_addr,
        "user_agent": request.headers.get('User-Agent'),
        "username": data.get('username')
    }
    
    if response.status_code == 200:
        access_token = response.json().get('access_token')
        
        # 📌 Log đăng nhập thành công
        log_data.update({
            "level": "INFO",
            "message": "User login successful"
        })
        send_log_to_logstash(log_data)  # Gửi log đến Logstash
        
        resp = redirect('/dashboard')
        resp.set_cookie('session_token', access_token, httponly=True)
        return resp
    else:
        # 📌 Log đăng nhập thất bại
        log_data.update({
            "level": "WARNING",
            "message": "User login failed"
        })
        send_log_to_logstash(log_data)  # Gửi log đến Logstash
        
        return render_template('index.html', message="Invalid username or password"), 401


@app.route('/dashboard', methods=['GET'])
def dashboard():
    response = requests.get("http://management-user-service:8084/songs")
    return render_template('dashboard.html', songs=response.json())

@app.route('/admin-dashboard', methods=['GET'])
def admin_dashboard():
    auth_token = request.cookies.get('session_token')
    if not auth_token:
        return jsonify({"error": "Missing Authorization"}), 401
    
    headers = {'Authorization': f'Bearer {auth_token}'}
    response = requests.get("http://management-user-service:8084/check-admin", headers=headers)
    if response.status_code != 200:
        return jsonify({"error": "Not admin!!!"}), 401
    
    return render_template('admin.html')

@app.route('/register', methods=['POST'])
def register():
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
    auth_token = request.cookies.get('session_token')
    if not auth_token:
        return jsonify({"error": "Missing Authorization"}), 401
    
    headers = {'Authorization': f'Bearer {auth_token}'}
    response = requests.get("http://management-user-service:8084/users/me", headers=headers)
    return render_template('user.html', user_info=response.json())

@app.route('/users/me', methods=['PUT'])
def update_user():
    auth_token = request.cookies.get('session_token')
    if not auth_token:
        return jsonify({"error": "Missing Authorization"}), 401
    
    headers = {'Authorization': f'Bearer {auth_token}'}
    data = {
        'username': request.form.get('username'),
        'password': request.form.get('password')
    }

    response = requests.put("http://management-user-service:8084/users/me", json=data, headers=headers)
    return response.json(), response.status_code

@app.route('/users/me/password', methods=['PUT'])
def change_password():
    auth_token = request.cookies.get('session_token')
    if not auth_token:
        return jsonify({"error": "Missing Authorization"}), 401
    
    headers = {'Authorization': f'Bearer {auth_token}'}
    data = {
        'username': request.form.get('username'),
        'password': request.form.get('password')
    }
    response = requests.put("http://management-user-service:8084/users/me/password", json=data, headers=headers)
    return response.json(), response.status_code

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
    data = {
        'limit': request.args.get('limit', 10),
        'offset': request.args.get('offset', 0)
    }
    try:
        response = requests.get("http://storage-service:8083/files", params=data)
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
        auth_token = request.cookies.get('session_token')
        if not auth_token:
            return jsonify({"error": "Missing Authorization"}), 401

        headers = {'Authorization': f'Bearer {auth_token}'}
        
        # Kiểm tra xem có file không
        if 'file' not in request.files:
            log_data = {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "level": "WARNING",
                "message": "Song upload failed - No file provided",
                "app": "music-service",
                "ip": request.remote_addr,
                "user_agent": request.headers.get('User-Agent'),
                "username": request.form.get('username')
            }
            send_log_to_logstash(log_data)
            return jsonify({"error": "No file part"}), 400

        file = request.files['file']
        if file.filename == '':
            log_data = {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "level": "WARNING",
                "message": "Song upload failed - No filename",
                "app": "music-service",
                "ip": request.remote_addr,
                "user_agent": request.headers.get('User-Agent'),
                "username": request.form.get('username')
            }
            send_log_to_logstash(log_data)
            return jsonify({"error": "No selected file"}), 400

        # Upload file lên storage-service
        response_storage = requests.post(
            "http://storage-service:8083/upload", 
            files={"file": file}
        )
        if response_storage.status_code != 201:
            log_data = {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "level": "ERROR",
                "message": "Song upload failed - Storage service error",
                "app": "music-service",
                "ip": request.remote_addr,
                "user_agent": request.headers.get('User-Agent'),
                "username": request.form.get('username'),
                "error_details": response_storage.text
            }
            send_log_to_logstash(log_data)
            return response_storage.json()

        # Lưu metadata của bài hát
        metadata = {
            'title': request.form.get('title', file.filename),
            'artist_id': request.form.get('artist_id'),
            'album_id': request.form.get('album_id'),
            'genre': request.form.get('genre'),
            'duration': request.form.get('duration'),
            'file_path': response_storage.json().get('id')
        }

        response_db = requests.post(
            "http://management-user-service:8084/api/add_song", 
            json=metadata,
            headers=headers
        )

        if response_db.status_code == 201:
            log_data = {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": f"Song uploaded successfully - {metadata['title']}",
                "app": "music-service",
                "ip": request.remote_addr,
                "user_agent": request.headers.get('User-Agent'),
                "username": request.form.get('username'),
                "song_metadata": metadata
            }
            send_log_to_logstash(log_data)
        else:
            log_data = {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "level": "ERROR",
                "message": "Song metadata upload failed",
                "app": "music-service",
                "ip": request.remote_addr,
                "user_agent": request.headers.get('User-Agent'),
                "username": request.form.get('username'),
                "error_details": response_db.text
            }
            send_log_to_logstash(log_data)

        return render_template('admin.html', song=response_db.json())

    except Exception as e:
        log_data = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "level": "ERROR",
            "message": "Unexpected error during song upload",
            "app": "music-service",
            "ip": request.remote_addr,
            "user_agent": request.headers.get('User-Agent'),
            "username": request.form.get('username'),
            "error_details": str(e)
        }
        send_log_to_logstash(log_data)
        
        logger.error(f"Error uploading song: {str(e)}")
        return jsonify({"error": "Error uploading song"}), 500
       
@app.route('/api/stream/<int:song_id>', methods=['GET'])
def stream_song(song_id):
    try:
        quality = request.args.get('quality', 'medium')

        # Lấy token từ cookie
        auth_token = request.cookies.get('session_token')
        username = "unknown"

        if auth_token:
            # Gửi request để lấy thông tin user từ token
            user_info = requests.get("http://management-user-service:8084/users/me", 
                                     headers={"Authorization": f"Bearer {auth_token}"})
            if user_info.status_code == 200:
                username = user_info.json().get('username', 'unknown')

        # Lấy thông tin bài hát từ management-user-service
        response = requests.get(f"http://management-user-service:8084/songs/{song_id}")
        if response.status_code != 200:
            log_data = {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "level": "WARNING",
                "message": f"User attempted to stream non-existent song - ID {song_id}",
                "app": "music-service",
                "ip": request.remote_addr,
                "user_agent": request.headers.get('User-Agent'),
                "username": username
            }
            send_log_to_logstash(log_data)
            return jsonify({"error": "Song not found"}), 404

        song = response.json()
        file_id = song.get('file_path')
        if not file_id:
            return jsonify({"error": "Song file not found"}), 404

        storage_url = f"http://storage-service:8083/files/{file_id}"
        quality_settings = STREAMING_QUALITY[quality]

        # Log khi user bắt đầu nghe nhạc
        log_data = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "level": "INFO",
            "message": f"User started streaming song - ID {song_id}, Quality {quality}",
            "app": "music-service",
            "ip": request.remote_addr,
            "user_agent": request.headers.get('User-Agent'),
            "username": username,
            "song_id": song_id,
            "song_title": song.get('title', 'Unknown'),
            "stream_quality": quality
        }
        send_log_to_logstash(log_data)

        # Lưu file tạm để stream với FFmpeg
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
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

                for chunk in iter(lambda: process.stdout.read(4096), b""):
                    yield chunk

                process.stdout.close()
                process.wait()
                os.unlink(temp_path)
            except Exception as e:
                logger.error(f"Error in transcoding: {e}")
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        return Response(
            stream_with_context(generate()),
            content_type=f"audio/{quality_settings['format']}"
        )

    except Exception as e:
        log_data = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "level": "ERROR",
            "message": f"Error while streaming song - ID {song_id}",
            "app": "music-service",
            "ip": request.remote_addr,
            "user_agent": request.headers.get('User-Agent'),
            "username": username,
            "error_details": str(e)
        }
        send_log_to_logstash(log_data)
        
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
        auth_token = request.cookies.get('session_token')
        if not auth_token:
            return jsonify({"error": "Missing Authorization"}), 401

        headers = {'Authorization': f'Bearer {auth_token}'}

        # Gửi request xóa bài hát đến storage-service
        response = requests.delete(f"http://storage-service:8083/files/{song_id}", headers=headers)

        log_data = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "app": "music-service",
            "ip": request.remote_addr,
            "user_agent": request.headers.get('User-Agent'),
            "username": request.form.get('username'),
            "song_id": song_id
        }

        if response.status_code == 200:
            log_data.update({
                "level": "INFO",
                "message": f"Song deleted successfully - ID {song_id}"
            })
            send_log_to_logstash(log_data)  # Gửi log thành công
            return response.json(), 200
        else:
            log_data.update({
                "level": "WARNING",
                "message": f"Song deletion failed - ID {song_id}",
                "error_details": response.text
            })
            send_log_to_logstash(log_data)  # Gửi log thất bại
            return response.json(), response.status_code

    except Exception as e:
        log_data = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "level": "ERROR",
            "message": f"Unexpected error during song deletion - ID {song_id}",
            "app": "music-service",
            "ip": request.remote_addr,
            "user_agent": request.headers.get('User-Agent'),
            "username": request.form.get('username'),
            "error_details": str(e)
        }
        send_log_to_logstash(log_data)  # Gửi log lỗi hệ thống
        
        logger.error(f"Error deleting song: {str(e)}")
        return jsonify({"error": "Error deleting song"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)