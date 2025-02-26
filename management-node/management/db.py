import mysql.connector
import time
from passlib.hash import pbkdf2_sha256

class Database:
    def __init__(self, host='database-service', user='root', password='root', database='musicdb'):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.cursor = None
        self.connect()
        
    def connect(self):
        """Establish connection to the database with retry logic"""
        max_retries = 30
        retry_interval = 2
        
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt+1}: Connecting to database at {self.host}...")
                self.connection = mysql.connector.connect(
                    host=self.host, 
                    user=self.user, 
                    password=self.password, 
                    database=self.database
                )
                print(f"Successfully connected to database on {self.host}")
                self.cursor = self.connection.cursor(dictionary=True)
                return True
            except mysql.connector.Error as err:
                print(f"Database connection attempt {attempt+1} failed: {err}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_interval} seconds...")
                    time.sleep(retry_interval)
                else:
                    print(f"Failed to connect to database after {max_retries} attempts")
                    raise

        
    ############################# USER MANAGEMENT #############################
    def create_user(self, username, password, email):
        password_hash = self._hash_password(password)
        
        self.cursor.execute("""
        INSERT INTO users (username, email, password_hash)
        VALUES (%s, %s, %s)
        """, (username, email, password_hash))
        
        # Get the last inserted ID
        user_id = self.cursor.lastrowid
        self.connection.commit()
        
        # Fetch the user data after insert
        self.cursor.execute("""
        SELECT user_id, username, email, created_at
        FROM users WHERE user_id = %s
        """, (user_id,))
        
        return self.cursor.fetchone()


    def authenticate_user(self, username, password):
        self.cursor.execute("""
        SELECT user_id, username, email, password_hash
        FROM users
        WHERE username = %s 
        """, (username,))
        user = self.cursor.fetchone()

        if user and self._verify_password(user['password_hash'], password):
                # Update last login time
                self.cursor.execute("""
                    UPDATE users
                    SET last_login = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                """, (user['user_id'],))
                self.connection.commit()
                return user
            
        return None

    def get_user_by_username(self, username):
        self.cursor.execute("""
        SELECT user_id, username, email
        FROM users
        WHERE username = %s
        """, (username,))
        return self.cursor.fetchone()
    
    def get_user_by_email(self, email):
        self.cursor.execute("""
        SELECT user_id, username, email
        FROM users
        WHERE email = %s
        """, (email,))
        return self.cursor.fetchone()
        
    def update_user(self, username, data):
        valid_fields = ['username', 'email']
        update_fields = []
        values = []

        for field in valid_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                values.append(data[field])

        if not update_fields:
            return None
        
        values.append(username)

        self.cursor.execute("""
        UPDATE users
        SET {}
        WHERE username = %s
        """.format(', '.join(update_fields)), tuple(values))
        self.connection.commit()
        return self.cursor.fetchone()
    
    def update_user_password(self, username, new_password):
        password_hash = self._hash_password(new_password)
        self.cursor.execute("""
        UPDATE users
        SET password_hash = %s
        WHERE username = %s
        """, (password_hash, username))
        self.connection.commit()
        return self.cursor.rowcount > 0
    
    def delete_user(self, username):
        self.cursor.execute("""
        DELETE FROM users
        WHERE username = %s
        """, (username,))
        self.connection.commit()
        return self.cursor.rowcount > 0
    
    def _hash_password(self, password):
        return pbkdf2_sha256.hash(password)
    
    def _verify_password(self, password_hash, password):
        return pbkdf2_sha256.verify(password, password_hash)


############################# END OF USER MANAGEMENT #############################

############################# MUSIC MANAGEMENT ##############################

    def get_all_songs(self):
        self.cursor.execute("""
                SELECT s.song_id, s.title, a.name as artist, al.title as album, 
                       s.duration, s.file_path, s.genre
                FROM songs s
                JOIN artists a ON s.artist_id = a.artist_id
                JOIN albums al ON s.album_id = al.album_id
                ORDER BY s.title
            """)
        return self.cursor.fetchall()   
    
    def get_song_by_id(self, song_id):
        self.cursor.execute("""
                SELECT s.song_id, s.title, a.name as artist, al.title as album, 
                       s.duration, s.file_path, s.genre
                FROM songs s
                JOIN artists a ON s.artist_id = a.artist_id
                JOIN albums al ON s.album_id = al.album_id
                WHERE s.song_id = %s
            """, (song_id,))
        return self.cursor.fetchone()
    
    def get_songs_by_artist(self, artist_id):
        self.cursor.execute("""
                SELECT s.song_id, s.title, al.title as album, 
                       s.duration, s.file_path, s.genre
                FROM songs s
                JOIN albums al ON s.album_id = al.album_id
                WHERE s.artist_id = %s
                ORDER BY al.title, s.title
            """, (artist_id,))
        return self.cursor.fetchall()
    
    def add_song(self, title, album_id, artist_id, duration, file_path, genre):
        self.cursor.execute("""
                INSERT INTO songs (title, album_id, artist_id, duration, file_path, genre)
                VALUES (%s, %s, %s, %s, %s, %s)
                """, (title, album_id, artist_id, duration, file_path, genre))
    
    # Get the last inserted ID
        song_id = self.cursor.lastrowid
        self.connection.commit()
        
        # Fetch complete song information including artist and album names
        self.cursor.execute("""
                SELECT s.song_id, s.title, a.name as artist, al.title as album, 
                    s.duration, s.file_path, s.genre
                FROM songs s
                JOIN artists a ON s.artist_id = a.artist_id
                JOIN albums al ON s.album_id = al.album_id
                WHERE s.song_id = %s
            """, (song_id,))
        
        return self.cursor.fetchone()
    


############################# END OF MUSIC MANAGEMENT #############################
