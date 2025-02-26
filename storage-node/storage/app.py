from flask import Flask, request, jsonify, send_file
import os
import uuid
from storage.file_storage import FileStorage
app = Flask(__name__)

STORAGE_PATH = "/storage"
MAX_CONTENT_LENGTH = 100 * 1024 * 1024 # 100MB

os.makedirs(STORAGE_PATH, exist_ok=True)
file_storage = FileStorage(STORAGE_PATH)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        file_id = str(uuid.uuid4())
        metadata = file_storage.save_file(file_id, file)
        return jsonify(metadata), 201
    
    return jsonify({"error": "File upload failed"}), 500

@app.route('/files/<file_id>', methods=['GET'])
def download_file(file_id):
        try:
            file_path, filename = file_storage.get_file_path(file_id)
            return send_file(file_path, as_attachment=True, download_name=filename)
        except FileNotFoundError:
            return jsonify({"error": "File not found"}), 404
        
@app.route('/metadata/<file_id>', methods=['GET']   )
def get_metadata(file_id):
    try:
        metadata = file_storage.get_metadata(file_id)
        return jsonify(metadata), 200
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404
    
@app.route('/files', methods=['GET'])
def list_files(limit=100, offset=0):
    try:
        limit = request.args.get('limit', 20)
        offset = request.args.get('offset', 0)
        files = file_storage.list_files(limit, offset)
        return jsonify({
            "files": files,
            "limit": limit,
            "offset": offset,
            "total": len(files)
        }), 200
    except Exception as e:
        return jsonify({"error listing files": str(e)}), 500
    
@app.route('/files/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    try:
        file_storage.delete_file(file_id)
        return jsonify({"message": "File deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error deleting file": str(e)}), 500
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8083)
    