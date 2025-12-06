"""Ponto de entrada da aplicação YT-Downloader Pro."""

from config import Config
from database.connection import DBConnection
from services.queue_manager import QueueManager
from ui.constants import (
    TAB_DOWNLOAD,
    TAB_HISTORY,
    TAB_QUEUE,
    TAB_SETTINGS,
)
from ui.root import MainWindow
from ui.tabs.download_tab import DownloadTab
from ui.tabs.history_tab import HistoryTab
from ui.tabs.queue_tab import QueueTab
from ui.tabs.settings_tab import SettingsTab
from utils.logger import get_logger

log = get_logger(__name__)


def main() -> None:
    """Função principal que inicializa a aplicação."""
    log.info("Iniciando YT-Downloader Pro")

    # Garante que os diretórios necessários existam
    Config.ensure_directories()

    # Inicializa banco de dados
    db = None
    try:
        db = DBConnection(Config.DB_PATH)
        db.init_db()
        log.info("Banco de dados inicializado")
    except Exception as e:
        log.error(f"Erro ao inicializar banco de dados: {e}")
        # Continua mesmo se o banco falhar (para permitir testes)

    # Cria janela principal
    app = MainWindow()

    # Cria gerenciador de fila
    queue_manager = QueueManager()

    # Adiciona aba de download primeiro (será a primeira aba à esquerda)
    # Passa referência para atualizar histórico após downloads
    history_tab = None
    refresh_history = None
    queue_tab = None
    refresh_queue = None
    
    if db:
        history_tab = HistoryTab(app.notebook, db, queue_manager=queue_manager)
        refresh_history = history_tab.refresh
    
    # Cria aba de fila
    queue_tab = QueueTab(app.notebook, queue_manager)
    refresh_queue = queue_tab.refresh
    
    download_tab = DownloadTab(
        app.notebook,
        db=db,
        history_tab_ref=refresh_history,
        queue_manager=queue_manager,
        queue_tab_ref=refresh_queue
    )
    app.add_tab(TAB_DOWNLOAD, download_tab.frame)

    # Adiciona aba de fila
    app.add_tab(TAB_QUEUE, queue_tab.frame)

    # Adiciona aba de histórico depois
    if db:
        app.add_tab(TAB_HISTORY, history_tab.frame)

    # Adiciona aba de configurações
    settings_tab = SettingsTab(app.notebook)
    app.add_tab(TAB_SETTINGS, settings_tab.frame)

    # Seleciona a aba "Download" como inicial
    app.select_tab(TAB_DOWNLOAD)

    # Inicia aplicação
    log.info("Interface gráfica pronta")
    app.run()


if __name__ == "__main__":
    main()

