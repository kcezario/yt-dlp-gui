"""Data Access Objects (DAOs) para operações CRUD no banco de dados."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from database.connection import DBConnection
from database.constants import (
    SQL_DELETE_HISTORY,
    SQL_INSERT_HISTORY,
    SQL_INSERT_PLAYLIST,
    SQL_INSERT_PLAYLIST_VIDEO,
    SQL_INSERT_VIDEO,
    SQL_SELECT_HISTORY,
    SQL_SELECT_HISTORY_BY_VIDEO_ID,
    SQL_SELECT_PLAYLIST_ITEMS,
    SQL_SELECT_VIDEO_BY_ID,
    SQL_UPDATE_HISTORY,
)
from utils.logger import get_logger

log = get_logger(__name__)


class VideoDAO:
    """DAO para operações relacionadas a vídeos."""

    def __init__(self, db: DBConnection) -> None:
        """
        Inicializa o DAO de vídeos.
        
        Args:
            db: Instância da conexão com o banco de dados.
        """
        self.db = db

    def upsert(self, data: Dict[str, Any]) -> None:
        """
        Insere ou atualiza um vídeo no banco de dados.
        
        Args:
            data: Dicionário com os dados do vídeo. Deve conter:
                - id: ID único do vídeo (obrigatório)
                - title: Título do vídeo (obrigatório)
                - duration: Duração em segundos (opcional)
                - channel: Nome do canal (opcional)
                - upload_date: Data de upload (opcional)
                - url: URL do vídeo (obrigatório)
                - file_path: Caminho do arquivo baixado (opcional)
                - thumbnail_url: URL da miniatura (opcional)
                - description: Descrição do vídeo (opcional)
        """
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(SQL_INSERT_VIDEO, (
                data.get("id"),
                data.get("title"),
                data.get("duration"),
                data.get("channel"),
                data.get("upload_date"),
                data.get("url"),
                data.get("file_path"),
                data.get("thumbnail_url"),
                data.get("description"),
            ))
            self.db.connection.commit()
            log.debug(f"Vídeo {data.get('id')} inserido/atualizado com sucesso")
        except Exception as e:
            log.error(f"Erro ao inserir/atualizar vídeo: {e}")
            self.db.connection.rollback()
            raise

    def get_by_id(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca um vídeo pelo ID.
        
        Args:
            video_id: ID do vídeo.
            
        Returns:
            Dicionário com os dados do vídeo ou None se não encontrado.
        """
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(SQL_SELECT_VIDEO_BY_ID, (video_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            log.error(f"Erro ao buscar vídeo {video_id}: {e}")
            return None


class PlaylistDAO:
    """DAO para operações relacionadas a playlists."""

    def __init__(self, db: DBConnection) -> None:
        """
        Inicializa o DAO de playlists.
        
        Args:
            db: Instância da conexão com o banco de dados.
        """
        self.db = db

    def upsert(self, data: Dict[str, Any]) -> None:
        """
        Insere ou atualiza uma playlist no banco de dados.
        
        Args:
            data: Dicionário com os dados da playlist. Deve conter:
                - id: ID único da playlist (obrigatório)
                - title: Título da playlist (obrigatório)
                - description: Descrição da playlist (opcional)
                - url: URL da playlist (opcional)
        """
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(SQL_INSERT_PLAYLIST, (
                data.get("id"),
                data.get("title"),
                data.get("description"),
                data.get("url"),
            ))
            self.db.connection.commit()
            log.debug(f"Playlist {data.get('id')} inserida/atualizada com sucesso")
        except Exception as e:
            log.error(f"Erro ao inserir/atualizar playlist: {e}")
            self.db.connection.rollback()
            raise

    def link_video(self, playlist_id: str, video_id: str, position: int = 0) -> None:
        """
        Vincula um vídeo a uma playlist.
        
        Args:
            playlist_id: ID da playlist.
            video_id: ID do vídeo.
            position: Posição do vídeo na playlist (padrão: 0).
        """
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(SQL_INSERT_PLAYLIST_VIDEO, (playlist_id, video_id, position))
            self.db.connection.commit()
            log.debug(f"Vídeo {video_id} vinculado à playlist {playlist_id}")
        except Exception as e:
            log.error(f"Erro ao vincular vídeo à playlist: {e}")
            self.db.connection.rollback()
            raise

    def get_playlist_items(self, playlist_id: str) -> List[Dict[str, Any]]:
        """
        Retorna todos os vídeos de uma playlist ordenados por posição.
        
        Args:
            playlist_id: ID da playlist.
            
        Returns:
            Lista de dicionários com os dados dos vídeos da playlist.
        """
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(SQL_SELECT_PLAYLIST_ITEMS, (playlist_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            log.error(f"Erro ao buscar itens da playlist {playlist_id}: {e}")
            return []


class HistoryDAO:
    """DAO para operações relacionadas ao histórico de downloads."""

    def __init__(self, db: DBConnection) -> None:
        """
        Inicializa o DAO de histórico.
        
        Args:
            db: Instância da conexão com o banco de dados.
        """
        self.db = db

    def add_history(self, data: Dict[str, Any]) -> int:
        """
        Adiciona um registro ao histórico de downloads.
        
        Args:
            data: Dicionário com os dados do histórico. Deve conter:
                - video_id: ID do vídeo (opcional)
                - playlist_id: ID da playlist (opcional)
                - status: Status do download ('pending', 'downloading', 'completed', 'failed')
                - file_path: Caminho do arquivo baixado (opcional)
                - file_size: Tamanho do arquivo em bytes (opcional)
                - download_started_at: Timestamp de início (opcional)
                - download_completed_at: Timestamp de conclusão (opcional)
                - error_message: Mensagem de erro (opcional)
                
        Returns:
            ID do registro inserido.
        """
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(SQL_INSERT_HISTORY, (
                data.get("video_id"),
                data.get("playlist_id"),
                data.get("status"),
                data.get("file_path"),
                data.get("file_size"),
                data.get("download_started_at"),
                data.get("download_completed_at"),
                data.get("error_message"),
            ))
            self.db.connection.commit()
            history_id = cursor.lastrowid
            log.debug(f"Registro de histórico {history_id} adicionado")
            return history_id
        except Exception as e:
            log.error(f"Erro ao adicionar histórico: {e}")
            self.db.connection.rollback()
            raise

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retorna o histórico de downloads ordenado por data de criação (mais recente primeiro).
        
        Args:
            limit: Número máximo de registros a retornar (padrão: 50).
            
        Returns:
            Lista de dicionários com os dados do histórico.
        """
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(SQL_SELECT_HISTORY, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            log.error(f"Erro ao buscar histórico: {e}")
            return []

