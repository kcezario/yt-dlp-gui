"""Configurações globais da aplicação."""

import os
from pathlib import Path
from typing import Optional


class Config:
    """Classe centralizada para configurações da aplicação."""

    # Caminho padrão de downloads
    DEFAULT_DOWNLOAD_PATH: str = str(Path.home() / "Downloads" / "yt-downloads")

    # Caminho do banco de dados
    DB_PATH: str = os.getenv("DB_PATH", "data/yt_downloader.db")

    # Configurações de log
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")
    LOG_CONSOLE: bool = os.getenv("LOG_CONSOLE", "true").lower() == "true"

    # Configurações de download
    FFMPEG_PATH: Optional[str] = os.getenv("FFMPEG_PATH", None)
    
    # Formatos suportados
    SUPPORTED_FORMATS: list[str] = ["mp3", "mp4"]
    
    # Limite padrão de histórico
    HISTORY_LIMIT_DEFAULT: int = 50

    @classmethod
    def ensure_directories(cls) -> None:
        """Garante que os diretórios necessários existam."""
        os.makedirs(os.path.dirname(cls.DB_PATH) if os.path.dirname(cls.DB_PATH) else ".", exist_ok=True)
        os.makedirs(os.path.dirname(cls.LOG_FILE) if os.path.dirname(cls.LOG_FILE) else ".", exist_ok=True)
        os.makedirs(cls.DEFAULT_DOWNLOAD_PATH, exist_ok=True)

