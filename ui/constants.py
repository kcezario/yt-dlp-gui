"""Constantes para interface gráfica."""

# Geometria da janela principal
WINDOW_TITLE = "YT-Downloader Pro"
WINDOW_SIZE = "800x600"
WINDOW_MIN_SIZE = (600, 400)
WINDOW_PADDING = 5

# Tema
THEME_DEFAULT = "default"

# Títulos das abas
TAB_DOWNLOAD = "Download"
TAB_QUEUE = "Fila de Downloads"
TAB_HISTORY = "Histórico"
TAB_SETTINGS = "Configurações"

# Textos da aba de Download
DOWNLOAD_TITLE = "Download de Vídeos"
DOWNLOAD_TYPE_LABEL = "Tipo de Download"
DOWNLOAD_TYPE_VIDEO = "Vídeo Único"
DOWNLOAD_TYPE_PLAYLIST = "Playlist"
DOWNLOAD_TYPE_CHANNEL = "Canal"
DOWNLOAD_URL_LABEL = "URL"
DOWNLOAD_PATH_LABEL = "Pasta de Destino"
DOWNLOAD_FORMAT_LABEL = "Formato"
DOWNLOAD_FORMAT_MP4 = "Vídeo (MP4)"
DOWNLOAD_FORMAT_MP3 = "Áudio (MP3)"
DOWNLOAD_BUTTON = "Baixar"
DOWNLOAD_PROGRESS_LABEL = "Progresso"
DOWNLOAD_STATUS_READY = "Pronto para baixar"
DOWNLOAD_STATUS_EXTRACTING = "Extraindo informações do vídeo..."
DOWNLOAD_STATUS_STARTING = "Iniciando download..."
DOWNLOAD_STATUS_EXTRACTING_PLAYLIST = "Extraindo lista de vídeos..."

# Textos da aba de Fila
QUEUE_TITLE = "Fila de Downloads"
QUEUE_BUTTON_PAUSE = "Pausar"
QUEUE_BUTTON_RESUME = "Retomar"
QUEUE_BUTTON_CLEAR = "Limpar Concluídos"

# Textos da aba de Histórico
HISTORY_TITLE = "Histórico de Downloads"
HISTORY_BUTTON_REFRESH = "Atualizar"

# Textos da aba de Configurações
SETTINGS_TITLE = "Configurações"
SETTINGS_DOWNLOAD_PATH_LABEL = "Pasta Padrão de Downloads"
SETTINGS_FFMPEG_LABEL = "Caminho do FFmpeg (Opcional)"
SETTINGS_FFMPEG_HELP = (
    "FFmpeg é necessário apenas para downloads de áudio (MP3).\n"
    "Se não especificado, o sistema tentará encontrá-lo automaticamente."
)
SETTINGS_INFO_LABEL = "Informações"
SETTINGS_INFO_TEXT = (
    "Nota: As configurações são temporárias nesta versão.\n"
    "Para salvar permanentemente, edite o arquivo .env ou config.py"
)
SETTINGS_BUTTON_APPLY = "Aplicar Configurações"
SETTINGS_BUTTON_RESET = "Restaurar Padrões"

# Diálogos
DIALOG_BROWSE_FOLDER = "Selecione a pasta de destino"
DIALOG_BROWSE_DOWNLOAD_FOLDER = "Selecione a pasta padrão de downloads"
DIALOG_BROWSE_FFMPEG = "Selecione o executável do FFmpeg"

# Mensagens de status
STATUS_COLOR_BLUE = "blue"
STATUS_COLOR_GREEN = "green"
STATUS_COLOR_RED = "red"
STATUS_COLOR_GRAY = "gray"

# Fontes
FONT_TITLE = ("", 14, "bold")
FONT_HELP = ("", 9)

# Padding padrão
PADDING_DEFAULT = "10"
PADDING_SMALL = "5"

# Colunas das tabelas
COLUMNS_HISTORY = ["Título", "Status", "Data", "Caminho"]
COLUMNS_QUEUE = ["Vídeo", "Status", "Progresso", "Ação"]

# Larguras de colunas
COLUMN_WIDTHS_HISTORY = {
    "Título": 300,
    "Status": 100,
    "Data": 150,
    "Caminho": 200,
}

COLUMN_WIDTHS_QUEUE = {
    "Vídeo": 350,
    "Status": 120,
    "Progresso": 150,
    "Ação": 100,
}

