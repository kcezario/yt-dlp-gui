"""Ponto de entrada da aplicação YT-Downloader Pro."""

from config import Config
from database.connection import DBConnection
from ui.root import MainWindow
from ui.tabs.download_tab import DownloadTab
from utils.logger import get_logger

log = get_logger(__name__)


def main() -> None:
    """Função principal que inicializa a aplicação."""
    log.info("Iniciando YT-Downloader Pro")

    # Garante que os diretórios necessários existam
    Config.ensure_directories()

    # Inicializa banco de dados
    try:
        db = DBConnection(Config.DB_PATH)
        db.init_db()
        log.info("Banco de dados inicializado")
    except Exception as e:
        log.error(f"Erro ao inicializar banco de dados: {e}")
        # Continua mesmo se o banco falhar (para permitir testes)

    # Cria janela principal
    app = MainWindow()

    # Adiciona aba de download
    download_tab = DownloadTab(app.notebook)
    app.add_tab("Download", download_tab.frame)

    # Inicia aplicação
    log.info("Interface gráfica pronta")
    app.run()


if __name__ == "__main__":
    main()

