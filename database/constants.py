"""Constantes SQL para operações no banco de dados."""

# Queries para tabela de vídeos
SQL_INSERT_VIDEO = """
    INSERT INTO videos (
        id, title, duration, channel, upload_date, url,
        file_path, thumbnail_url, description
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        title = excluded.title,
        duration = excluded.duration,
        channel = excluded.channel,
        upload_date = excluded.upload_date,
        url = excluded.url,
        file_path = excluded.file_path,
        thumbnail_url = excluded.thumbnail_url,
        description = excluded.description,
        updated_at = CURRENT_TIMESTAMP
"""

SQL_SELECT_VIDEO_BY_ID = "SELECT * FROM videos WHERE id = ?"

# Queries para tabela de playlists
SQL_INSERT_PLAYLIST = """
    INSERT INTO playlists (id, title, description, url)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        title = excluded.title,
        description = excluded.description,
        url = excluded.url,
        updated_at = CURRENT_TIMESTAMP
"""

SQL_INSERT_PLAYLIST_VIDEO = """
    INSERT INTO playlist_videos (playlist_id, video_id, position)
    VALUES (?, ?, ?)
    ON CONFLICT(playlist_id, video_id) DO UPDATE SET
        position = excluded.position
"""

SQL_SELECT_PLAYLIST_ITEMS = """
    SELECT v.*, pv.position
    FROM videos v
    INNER JOIN playlist_videos pv ON v.id = pv.video_id
    WHERE pv.playlist_id = ?
    ORDER BY pv.position ASC
"""

# Queries para tabela de histórico
SQL_INSERT_HISTORY = """
    INSERT INTO history (
        video_id, playlist_id, status, file_path, file_size,
        download_started_at, download_completed_at, error_message
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""

SQL_SELECT_HISTORY = """
    SELECT h.*, v.title as video_title, v.url as video_url,
           p.title as playlist_title
    FROM history h
    LEFT JOIN videos v ON h.video_id = v.id
    LEFT JOIN playlists p ON h.playlist_id = p.id
    ORDER BY h.created_at DESC
    LIMIT ?
"""

SQL_SELECT_HISTORY_BY_VIDEO_ID = """
    SELECT id FROM history 
    WHERE video_id = ? 
    ORDER BY created_at DESC 
    LIMIT 1
"""

SQL_UPDATE_HISTORY = """
    UPDATE history 
    SET status = ?, download_completed_at = ?, 
        file_path = ?, file_size = ?, error_message = ?
    WHERE id = ?
"""

SQL_DELETE_HISTORY = "DELETE FROM history WHERE id = ?"

