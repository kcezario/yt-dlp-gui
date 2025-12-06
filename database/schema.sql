-- Schema do banco de dados YT-Downloader Pro
-- Tabelas: videos, playlists, playlist_videos, history, settings

-- Tabela de Vídeos
CREATE TABLE IF NOT EXISTS videos (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    duration INTEGER,
    channel TEXT,
    upload_date TEXT,
    url TEXT NOT NULL,
    file_path TEXT,
    thumbnail_url TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Playlists
CREATE TABLE IF NOT EXISTS playlists (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Relacionamento Playlist-Vídeo
CREATE TABLE IF NOT EXISTS playlist_videos (
    playlist_id TEXT NOT NULL,
    video_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (playlist_id, video_id),
    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
);

-- Tabela de Histórico de Downloads
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT,
    playlist_id TEXT,
    status TEXT NOT NULL, -- 'pending', 'downloading', 'completed', 'failed'
    file_path TEXT,
    file_size INTEGER,
    download_started_at TIMESTAMP,
    download_completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE SET NULL,
    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE SET NULL
);

-- Tabela de Configurações
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_videos_url ON videos(url);
CREATE INDEX IF NOT EXISTS idx_history_video_id ON history(video_id);
CREATE INDEX IF NOT EXISTS idx_history_status ON history(status);
CREATE INDEX IF NOT EXISTS idx_history_created_at ON history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_playlist_videos_playlist_id ON playlist_videos(playlist_id);
CREATE INDEX IF NOT EXISTS idx_playlist_videos_video_id ON playlist_videos(video_id);

