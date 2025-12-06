"""Ponto de entrada da aplicação YT-Downloader Pro."""

from config import Config
from database.connection import DBConnection
from ui.root import MainWindow
from ui.tabs.download_tab import DownloadTab
from ui.tabs.history_tab import HistoryTab
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

    # Adiciona aba de download primeiro (será a primeira aba à esquerda)
    # Passa referência para atualizar histórico após downloads
    history_tab = None
    refresh_history = None
    
    if db:
        history_tab = HistoryTab(app.notebook, db)
        refresh_history = history_tab.refresh
    
    download_tab = DownloadTab(app.notebook, db=db, history_tab_ref=refresh_history)
    app.add_tab("Download", download_tab.frame)

    # Adiciona aba de histórico depois (será a segunda aba)
    if db:
        app.add_tab("Histórico", history_tab.frame)

    # Seleciona a aba "Download" como inicial
    app.select_tab("Download")

    # Inicia aplicação
    log.info("Interface gráfica pronta")
    app.run()


if __name__ == "__main__":
    main()

