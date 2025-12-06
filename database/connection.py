"""Gerenciamento de conexão com o banco de dados SQLite (Singleton)."""

import sqlite3
from pathlib import Path
from typing import Optional

from utils.logger import get_logger

log = get_logger(__name__)


class DBConnection:
    """
    Singleton para gerenciar conexão com o banco de dados SQLite.
    
    Garante que apenas uma conexão seja mantida durante a execução
    da aplicação e fornece métodos para inicializar o schema.
    """

    _instance: Optional["DBConnection"] = None
    _connection: Optional[sqlite3.Connection] = None
    _db_path: Optional[str] = None

    def __new__(cls, db_path: str) -> "DBConnection":
        """
        Implementa o padrão Singleton.
        
        Args:
            db_path: Caminho para o arquivo do banco de dados.
            
        Returns:
            Instância única da classe DBConnection.
        """
        if cls._instance is None or cls._db_path != db_path:
            cls._instance = super().__new__(cls)
            cls._db_path = db_path
            cls._connection = None
        return cls._instance

    def __init__(self, db_path: str) -> None:
        """
        Inicializa a conexão com o banco de dados.
        
        Args:
            db_path: Caminho para o arquivo do banco de dados.
        """
        if self._connection is None:
            self._connect(db_path)

    def _connect(self, db_path: str) -> None:
        """
        Estabelece conexão com o banco de dados.
        
        Args:
            db_path: Caminho para o arquivo do banco de dados.
        """
        try:
            # Garante que o diretório existe
            db_file = Path(db_path)
            db_file.parent.mkdir(parents=True, exist_ok=True)
            
            self._connection = sqlite3.connect(
                db_path,
                check_same_thread=False,
                timeout=30.0
            )
            self._connection.row_factory = sqlite3.Row
            self._db_path = db_path
            log.info(f"Conexão estabelecida com banco de dados: {db_path}")
        except sqlite3.Error as e:
            log.error(f"Erro ao conectar ao banco de dados: {e}")
            raise

    @property
    def connection(self) -> sqlite3.Connection:
        """
        Retorna a conexão com o banco de dados.
        
        Returns:
            Objeto de conexão SQLite.
            
        Raises:
            RuntimeError: Se a conexão não foi estabelecida.
        """
        if self._connection is None:
            raise RuntimeError("Conexão com banco de dados não estabelecida")
        return self._connection

    def init_db(self) -> None:
        """
        Inicializa o banco de dados executando o schema SQL.
        
        Lê o arquivo schema.sql e executa todas as instruções DDL.
        """
        try:
            schema_path = Path(__file__).parent / "schema.sql"
            
            if not schema_path.exists():
                raise FileNotFoundError(f"Arquivo schema.sql não encontrado em {schema_path}")
            
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            
            cursor = self.connection.cursor()
            cursor.executescript(schema_sql)
            self.connection.commit()
            log.info("Schema do banco de dados inicializado com sucesso")
        except (sqlite3.Error, FileNotFoundError) as e:
            log.error(f"Erro ao inicializar schema: {e}")
            self.connection.rollback()
            raise

    def close(self) -> None:
        """Fecha a conexão com o banco de dados."""
        if self._connection:
            self._connection.close()
            self._connection = None
            log.info("Conexão com banco de dados fechada")

    def __enter__(self) -> "DBConnection":
        """Suporte para context manager (with statement)."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Fecha a conexão ao sair do context manager."""
        # Não fechamos automaticamente para manter o singleton ativo
        pass

