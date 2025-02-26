-- Simple music database initialization script
USE musicdb;

-- Users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
);

-- Artists table
CREATE TABLE artists (
    artist_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    bio TEXT
);

-- Albums table
CREATE TABLE albums (
    album_id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    artist_id INTEGER REFERENCES artists(artist_id),
    release_year INTEGER,
    cover_art_path VARCHAR(255)
);

-- Songs table
CREATE TABLE songs (
    song_id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    album_id INTEGER REFERENCES albums(album_id),
    artist_id INTEGER REFERENCES artists(artist_id),
    duration INTEGER NOT NULL, -- in seconds
    file_path VARCHAR(255) NOT NULL,
    genre VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Playlists table
CREATE TABLE playlists (
    playlist_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Playlist songs junction table
CREATE TABLE playlist_songs (
    playlist_id INTEGER REFERENCES playlists(playlist_id),
    song_id INTEGER REFERENCES songs(song_id),
    position INTEGER NOT NULL,
    PRIMARY KEY (playlist_id, song_id)
);

-- Insert sample data
INSERT INTO artists (name, bio) VALUES 
('The Beatles', 'Legendary rock band from Liverpool'),
('Queen', 'British rock band formed in 1970'),
('Michael Jackson', 'King of Pop');

INSERT INTO albums (title, artist_id, release_year) VALUES 
('Abbey Road', 1, 1969),
('A Night at the Opera', 2, 1975),
('Thriller', 3, 1982);

INSERT INTO songs (title, album_id, artist_id, duration, file_path, genre) VALUES 
('Come Together', 1, 1, 259, '/come_together.mp3', 'Rock'),
('Something', 1, 1, 182, '/something.mp3', 'Rock'),
('Bohemian Rhapsody', 2, 2, 355, '/bohemian_rhapsody.mp3', 'Rock'),
('Thriller', 3, 3, 357, '/thriller.mp3', 'Pop'),
('Billie Jean', 3, 3, 294, '/billie_jean.mp3', 'Pop');

-- Create admin user
