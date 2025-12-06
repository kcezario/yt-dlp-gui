"""Módulo de validação de URLs e dados de entrada."""

import re
from typing import Optional, Tuple
from urllib.parse import urlparse

from utils.logger import get_logger

log = get_logger(__name__)

# Padrões regex para URLs suportadas
YOUTUBE_PATTERNS = [
    r"(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})",
    r"(?:https?://)?(?:www\.)?youtube\.com/playlist\?list=([a-zA-Z0-9_-]+)",
    r"(?:https?://)?(?:www\.)?youtube\.com/channel/([a-zA-Z0-9_-]+)",
    r"(?:https?://)?(?:www\.)?youtube\.com/user/([a-zA-Z0-9_-]+)",
]

# Padrão genérico para URLs válidas
URL_PATTERN = re.compile(
    r"^https?://"  # http:// ou https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domínio
    r"localhost|"  # localhost
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP
    r"(?::\d+)?"  # porta opcional
    r"(?:/?|[/?]\S+)$",  # caminho opcional
    re.IGNORECASE
)


def is_valid_url(url: str) -> bool:
    """
    Valida se uma string é uma URL válida.
    
    Args:
        url: String a ser validada.
        
    Returns:
        True se a URL é válida, False caso contrário.
    """
    if not url or not isinstance(url, str):
        return False
    
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def is_youtube_url(url: str) -> bool:
    """
    Valida se uma URL é do YouTube.
    
    Args:
        url: URL a ser validada.
        
    Returns:
        True se a URL é do YouTube, False caso contrário.
    """
    if not url or not isinstance(url, str):
        return False
    
    url_lower = url.lower().strip()
    
    # Verifica domínios do YouTube
    youtube_domains = [
        "youtube.com",
        "youtu.be",
        "www.youtube.com",
        "m.youtube.com",
    ]
    
    if not any(domain in url_lower for domain in youtube_domains):
        return False
    
    # Verifica padrões específicos do YouTube
    for pattern in YOUTUBE_PATTERNS:
        if re.search(pattern, url_lower):
            return True
    
    return False


def validate_download_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Valida uma URL para download.
    
    Args:
        url: URL a ser validada.
        
    Returns:
        Tupla (is_valid, error_message).
        is_valid: True se a URL é válida para download.
        error_message: Mensagem de erro se inválida, None se válida.
    """
    if not url or not url.strip():
        return False, "Por favor, insira uma URL."
    
    url = url.strip()
    
    # Verifica se é uma URL válida
    if not is_valid_url(url):
        return False, (
            "URL inválida.\n\n"
            "Por favor, insira uma URL válida do YouTube.\n"
            "Exemplos:\n"
            "• https://www.youtube.com/watch?v=VIDEO_ID\n"
            "• https://youtu.be/VIDEO_ID"
        )
    
    # Verifica se é do YouTube (yt-dlp suporta outros sites, mas focamos no YouTube)
    if not is_youtube_url(url):
        return False, (
            "URL não é do YouTube.\n\n"
            "Atualmente, apenas URLs do YouTube são suportadas.\n"
            "Por favor, insira uma URL válida do YouTube."
        )
    
    return True, None

