"""Classe base para testes com setup/teardown de banco de dados temporário."""

import os
import tempfile
import unittest
from pathlib import Path
from typing import Optional

from database.connection import DBConnection


class TestBase(unittest.TestCase):
    """
    Classe base para testes com configuração de banco de dados temporário.
    
    Cria um banco de dados SQLite temporário para cada teste e inicializa
    o schema automaticamente.
    """

    def setUp(self) -> None:
        """
        Configura o ambiente de teste.
        Cria um banco de dados temporário para cada teste.
        """
        # Cria um arquivo temporário para o banco de dados
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Inicializa a conexão com o banco temporário
        self.db = DBConnection(self.db_path)
        self.db.init_db()
    
    def tearDown(self) -> None:
        """
        Limpa o ambiente de teste.
        Remove o banco de dados temporário.
        """
        if hasattr(self, "db") and self.db:
            self.db.close()
        
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

