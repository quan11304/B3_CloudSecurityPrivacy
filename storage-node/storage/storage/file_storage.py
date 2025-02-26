import os
import time
import mimetypes
from werkzeug.utils import secure_filename

class FileStorage:
    def __init__(self, storage_path):
        self.storage_path = storage_path
        
    def save_file(self, file_id, file):
        filename = secure_filename(file.filename)
        _, ext = os.path.splitext(filename)

        file_path = os.path.join(self.storage_path, f"{file_id}{ext}")
        file.save(file_path)

        file_size = os.path.getsize(file_path)
        created_at = int(time.time())

        return {
            "id": file_id,
            "filename": filename,
            "size": file_size,
            "created_at": created_at,
            "content_type": mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        }
    
    def get_file_path(self, file_id):
        file_path = os.path.join(self.storage_path, f"{file_id}")
        if not os.path.exists(file_path):
            return None, None
        
        _, ext = os.path.splitext(file_path)
        filename = f"{file_id}{ext}"
        return file_path, filename
    
    def get_metadata(self, file_id):
        file_path, filename = self.get_file_path(file_id)
        stats = os.stat(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        return {
            "id": file_id,
            "filename": filename,
            "size": stats.st_size,
            "created_at": stats.st_ctime,
            "updated_at": stats.st_mtime,
            "content_type": mime_type
        }
    
    def list_files(self, limit=100, offset=0):
        files = []

        all_files = []
        for filename in os.listdir(self.storage_path):
            file_path = os.path.join(self.storage_path, filename)
            if os.path.isfile(file_path):
                file_id, _ = os.path.splitext(filename)
                all_files.append(file_id)

        paginated_files = all_files[offset:offset+limit]

        for file_id in paginated_files:
            try:
                metadata = self.get_metadata(file_id)
                files.append(metadata)
            except Exception:
                continue

        return files
    
    
    def delete_file(self, file_id):
        file_path, _ = self.get_file_path(file_id)
        os.remove(file_path)
        return True
        
