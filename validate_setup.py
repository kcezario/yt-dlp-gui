"""Script de validação da Etapa 0: Configuração do Ambiente e Boilerplate."""

import os
from config import Config
from utils.logger import get_logger

# 1. Verificar pastas
required_dirs = ["database", "services", "ui", "assets"]
for d in required_dirs:
    assert os.path.exists(d), f"Diretório {d} faltando"

# 2. Testar Logger
log = get_logger("TestSetup")
log.info("Ambiente configurado com sucesso.")
print("Setup OK!")

