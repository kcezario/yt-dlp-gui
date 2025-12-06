"""Script de validação da Etapa 1: Camada de Persistência (Model)."""

from database.dao import VideoDAO, PlaylistDAO
from database.connection import DBConnection

# Inicializar banco de dados
db = DBConnection("test.db")
db.init_db()  # Executa schema

# Teste Inserção
v_dao = VideoDAO(db)
v_dao.upsert({
    "id": "vid123",
    "title": "Teste Video",
    "duration": 100,
    "channel": "Dev",
    "upload_date": "2023-01-01",
    "url": "https://www.youtube.com/watch?v=test123"
})

p_dao = PlaylistDAO(db)
p_dao.upsert({
    "id": "pl999",
    "title": "Minha Lista"
})
p_dao.link_video("pl999", "vid123", position=1)

# Teste Recuperação
history = p_dao.get_playlist_items("pl999")
print(f"Itens na playlist: {len(history)}")  # Deve ser 1
print("Database OK!")

# Limpeza
db.close()
import os
if os.path.exists("test.db"):
    os.remove("test.db")

