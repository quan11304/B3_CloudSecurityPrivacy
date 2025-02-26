from flask import Flask, jsonify, request
from db import Database
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
import os

app = Flask(__name__)
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
        access_token = create_access_token(identity=user['user_id'])
        return jsonify({"user_id": user['user_id'], "message": "User logged in successfully", "access_token": access_token}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401
    
@app.route('/register', methods=['POST'])
def register():
    data = request.json

    required_fields = ['username', 'password', 'email']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    if db.get_user_by_username(data['username']):
        return jsonify({"error": "Username already exists"}), 409
    
    if db.get_user_by_email(data['email']):
        return jsonify({"error": "Email already exists"}), 409
    
    user = db.create_user(
        data['username'],
        data['email'],
        data['password']
    )
    
    return jsonify({
        "user_id": user['user_id'],
        "username": user['username'],
        "message": "User registered successfully"
    }), 201

@app.route('/users/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = db.get_user_by_id(user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    user.pop('password')

    return jsonify({
        "user_id": user['user_id'],
        "username": user['username'],
        "email": user['email']
    }), 200

@app.route('/users/me', methods=['PUT'])
@jwt_required()
def update_user():
    """Update user profile"""
    user_id = get_jwt_identity()
    data = request.json
    
    # Prevent updating username or email to existing ones
    if 'username' in data:
        existing_user = db.get_user_by_username(data['username'])
        if existing_user and existing_user['user_id'] != user_id:
            return jsonify({"error": "Username already exists"}), 409
    
    if 'email' in data:
        existing_user = db.get_user_by_email(data['email'])
        if existing_user and existing_user['user_id'] != user_id:
            return jsonify({"error": "Email already exists"}), 409
    
    # Update user
    updated_user = db.update_user(user_id, data)
    
    if not updated_user:
        return jsonify({"error": "User not found"}), 404
    
    # Remove sensitive information
    updated_user.pop('password_hash', None)
    
    return jsonify(updated_user), 200

@app.route('/users/me/password', methods=['PUT'])
@jwt_required()
def change_password():
    """Change user password"""
    user_id = get_jwt_identity()
    data = request.json
    
    # Validate required fields
    if 'current_password' not in data or 'new_password' not in data:
        return jsonify({"error": "Current password and new password required"}), 400
    
    # Verify current password
    user = db.get_user_by_id(user_id)
    if not user or not db.verify_password(user['password_hash'], data['current_password']):
        return jsonify({"error": "Current password is incorrect"}), 401
    
    # Update password
    success = db.update_password(user_id, data['new_password'])
    
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

@app.route('/songs', methods=['POST'])
@jwt_required()
def add_song():
    """Add a new song"""
    data = request.json
    required_fields = ['title', 'album_id', 'artist_id', 'duration', 'file_path', 'genre']
    
    # Check if all required fields are present
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Add the song
    song_id = db.add_song(
        data['title'],
        data['album_id'],
        data['artist_id'],
        data['duration'],
        data['file_path'],
        data['genre']
    )
    
    return jsonify({"song_id": song_id, "message": "Song added successfully"}), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8084)