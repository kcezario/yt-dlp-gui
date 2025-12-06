"""Classe base para testes com setup/teardown de banco de dados temporário."""

import os
import tempfile
import unittest
from pathlib import Path
from typing import Optional


class TestBase(unittest.TestCase):
    """
    Classe base para testes com configuração de banco de dados temporário.
    
    Nota: Esta classe será expandida na Etapa 1 quando database.connection
    for implementado. Por enquanto, apenas fornece a estrutura básica.
    """

    def setUp(self) -> None:
        """
        Configura o ambiente de teste.
        Cria um banco de dados temporário para cada teste.
        
        Nota: A inicialização do DBConnection será adicionada na Etapa 1.
        """
        # Cria um arquivo temporário para o banco de dados
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # TODO: Inicializar DBConnection quando database.connection for criado
        # from database.connection import DBConnection
        # self.db = DBConnection(self.db_path)
        # self.db.init_db()
        self.db = None
    
    def tearDown(self) -> None:
        """
        Limpa o ambiente de teste.
        Remove o banco de dados temporário.
        """
        if hasattr(self, "db") and self.db:
            # TODO: Fechar conexão quando DBConnection for implementado
            # self.db.close()
            pass
        
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

