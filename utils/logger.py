"""Sistema de logging centralizado da aplicação."""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from config import Config


def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Retorna um logger configurado para a aplicação.

    Args:
        name: Nome do logger (geralmente __name__ do módulo).
        log_file: Caminho opcional para arquivo de log. Se None, usa Config.LOG_FILE.

    Returns:
        Logger configurado com handlers de console e arquivo.
    """
    logger = logging.getLogger(name)
    
    # Evita adicionar handlers múltiplas vezes
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO))
    
    # Formato das mensagens
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Handler para console
    if Config.LOG_CONSOLE:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Handler para arquivo
    log_path = log_file or Config.LOG_FILE
    log_dir = Path(log_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

