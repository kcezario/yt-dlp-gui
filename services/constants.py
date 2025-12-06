"""Constantes para serviços de download e processamento."""

# Formatos suportados
SUPPORTED_FORMATS = ["mp3", "mp4"]

# Opções base do yt-dlp
YDL_OPTS_BASE = {
    "quiet": True,
    "no_warnings": True,
}

# Opções para extração de informações (sem download)
YDL_OPTS_EXTRACT_INFO = {
    "quiet": True,
    "no_warnings": True,
}

# Opções para extração de playlist (extract_flat)
YDL_OPTS_EXTRACT_PLAYLIST = {
    "quiet": True,
    "no_warnings": True,
    "extract_flat": True,
}

# Opções para contornar bloqueios do YouTube
YDL_EXTRACTOR_ARGS_YOUTUBE = {
    "youtube": {
        "player_client": ["android", "web"],
    }
}

# Headers HTTP para parecer um navegador real
YDL_HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

# Opções para download de áudio (MP3)
FFMPEG_AUDIO_OPTS = {
    "format": "bestaudio/best",
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "192",
    }],
}

# Opções para download de vídeo (MP4)
FFMPEG_VIDEO_OPTS = {
    "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    "merge_output_format": "mp4",
}

# Template de nome de arquivo
FILENAME_TEMPLATE = "%(title)s.%(ext)s"

