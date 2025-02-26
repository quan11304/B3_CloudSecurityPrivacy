from flask import Flask, jsonify, request
from db import Database
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
import os

app = Flask(__name__)

app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'hsw109')  # Change this in production!
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600  # Token expires in 1 hour
app.config['JWT_TOKEN_LOCATION'] = ['headers']

db = Database()
jwt = JWTManager(app)

########################################################
# Users management
########################################################

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = db.authenticate_user(data['username'], data['password'])
    if user:
        access_token = create_access_token(identity=user['username'])
        return jsonify({
            "user_id": user['user_id'],
            "message": "User logged in successfully",
            "access_token": access_token
        }), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401
    
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    
    if db.get_user_by_username(data['username']):
        return jsonify({"error": "Username already exists"}), 409
    
    if db.get_user_by_email(data['email']):
        return jsonify({"error": "Email already exists"}), 409
    
    user = db.create_user(
        data['username'],
        data['password'],
        data['email']
    )
    
    return jsonify({
        "user_id": user['user_id'],
        "username": user['username'],
        "message": "User registered successfully"
    }), 201

@app.route('/check-admin', methods=['GET'])
@jwt_required()
def check_admin():
    username = get_jwt_identity()
    if username != 'admin':
        return jsonify({"error": "Not admin!!!"}), 401
    return jsonify({"message": "Admin user"}), 200
    
@app.route('/users/me', methods=['GET'])
@jwt_required()
def get_current_user():
    username = get_jwt_identity()
    user = db.get_user_by_username(username)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify(user), 200

@app.route('/users/me', methods=['PUT'])
@jwt_required()
def update_user():
    """Update user profile"""
    username = get_jwt_identity()
    data = request.json
    
    # Prevent updating username or email to existing ones
    if 'username' in data:
        existing_user = db.get_user_by_username(data['username'])
        if existing_user and existing_user['username'] != username:
            return jsonify({"error": "Username already exists"}), 409
    
    if 'email' in data:
        existing_user = db.get_user_by_email(data['email'])
        if existing_user and existing_user['username'] != username:
            return jsonify({"error": "Email already exists"}), 409
    
    # Update user
    updated_user = db.update_user(username, data)
    
    if not updated_user:
        return jsonify({"error": "User not found"}), 404
        
    return jsonify(updated_user), 200

@app.route('/users/me/password', methods=['PUT'])
@jwt_required()
def change_password():
    """Change user password"""
    username = get_jwt_identity()
    data = request.json
    
    # Validate required fields
    if 'current_password' not in data or 'new_password' not in data:
        return jsonify({"error": "Current password and new password required"}), 400
    
    # Verify current password
    user = db.get_user_by_username(username)
    if not user or not db.verify_password(user['password_hash'], data['current_password']):
        return jsonify({"error": "Current password is incorrect"}), 401
    
    # Update password
    success = db.update_password(username, data['new_password'])
    
    if not success:
        return jsonify({"error": "Failed to update password"}), 500
    
    return jsonify({"message": "Password updated successfully"}), 200

########################################################
# Songs management
########################################################

@app.route('/songs', methods=['GET'])
def get_songs():
    """Get all songs"""
    songs = db.get_all_songs()
    return jsonify(songs)

@app.route('/songs/<int:song_id>', methods=['GET'])
def get_song(song_id):
    """Get a specific song"""
    song = db.get_song_by_id(song_id)
    if song:
        return jsonify(song)
    return jsonify({"error": "Song not found"}), 404

@app.route('/artists/<int:artist_id>/songs', methods=['GET'])
def get_artist_songs(artist_id):
    """Get all songs by an artist"""
    songs = db.get_songs_by_artist(artist_id)
    return jsonify(songs)

@app.route('/api/add_song', methods=['POST'])
@jwt_required()
def add_song():
    """Add a new song"""
    username = get_jwt_identity()
    if username != 'admin':
        return jsonify({"error": "Not admin!!!"}), 401
    
    data = request.json
    required_fields = ['title', 'album_id', 'artist_id', 'duration', 'file_path', 'genre']
    
    # Check if all required fields are present
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Add the song and get the returned dictionary
    song_data = db.add_song(
        data['title'],
        data['album_id'],
        data['artist_id'],
        data['duration'],
        data['file_path'],
        data['genre']
    )
    
    return jsonify(song_data), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8084)