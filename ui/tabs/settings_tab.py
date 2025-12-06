"""Aba de configurações da aplicação."""

import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from config import Config
from utils.logger import get_logger

log = get_logger(__name__)


class SettingsTab:
    """
    Aba de configurações da aplicação.
    
    Permite configurar caminhos e preferências da aplicação.
    """

    def __init__(self, parent: ttk.Notebook) -> None:
        """
        Inicializa a aba de configurações.
        
        Args:
            parent: Widget pai (Notebook) onde a aba será adicionada.
        """
        self.frame = ttk.Frame(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Configura a interface gráfica da aba."""
        # Container principal
        main_container = ttk.Frame(self.frame, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)

        # Título
        title_label = ttk.Label(
            main_container,
            text="Configurações",
            font=("", 14, "bold")
        )
        title_label.pack(pady=(0, 20))

        # Frame para caminho padrão de downloads
        download_path_frame = ttk.LabelFrame(
            main_container,
            text="Pasta Padrão de Downloads",
            padding="10"
        )
        download_path_frame.pack(fill=tk.X, pady=(0, 10))

        self.download_path_var = tk.StringVar(value=Config.DEFAULT_DOWNLOAD_PATH)
        download_path_entry = ttk.Entry(
            download_path_frame,
            textvariable=self.download_path_var,
            width=50
        )
        download_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        browse_download_button = ttk.Button(
            download_path_frame,
            text="Procurar...",
            command=self._browse_download_folder
        )
        browse_download_button.pack(side=tk.LEFT)

        # Frame para caminho do FFmpeg
        ffmpeg_frame = ttk.LabelFrame(
            main_container,
            text="Caminho do FFmpeg (Opcional)",
            padding="10"
        )
        ffmpeg_frame.pack(fill=tk.X, pady=(0, 10))

        help_label = ttk.Label(
            ffmpeg_frame,
            text="FFmpeg é necessário apenas para downloads de áudio (MP3).\n"
                 "Se não especificado, o sistema tentará encontrá-lo automaticamente.",
            foreground="gray",
            font=("", 9)
        )
        help_label.pack(anchor=tk.W, pady=(0, 5))

        self.ffmpeg_path_var = tk.StringVar(value=Config.FFMPEG_PATH or "")
        ffmpeg_path_entry = ttk.Entry(
            ffmpeg_frame,
            textvariable=self.ffmpeg_path_var,
            width=50
        )
        ffmpeg_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        browse_ffmpeg_button = ttk.Button(
            ffmpeg_frame,
            text="Procurar...",
            command=self._browse_ffmpeg
        )
        browse_ffmpeg_button.pack(side=tk.LEFT)

        clear_ffmpeg_button = ttk.Button(
            ffmpeg_frame,
            text="Limpar",
            command=lambda: self.ffmpeg_path_var.set("")
        )
        clear_ffmpeg_button.pack(side=tk.LEFT, padx=(5, 0))

        # Frame para informações
        info_frame = ttk.LabelFrame(
            main_container,
            text="Informações",
            padding="10"
        )
        info_frame.pack(fill=tk.X, pady=(0, 10))

        info_text = (
            "Nota: As configurações são temporárias nesta versão.\n"
            "Para salvar permanentemente, edite o arquivo .env ou config.py"
        )
        info_label = ttk.Label(
            info_frame,
            text=info_text,
            foreground="gray",
            font=("", 9)
        )
        info_label.pack(anchor=tk.W)

        # Botões de ação
        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        save_button = ttk.Button(
            button_frame,
            text="Aplicar Configurações",
            command=self._apply_settings
        )
        save_button.pack(side=tk.LEFT, padx=(0, 5))

        reset_button = ttk.Button(
            button_frame,
            text="Restaurar Padrões",
            command=self._reset_settings
        )
        reset_button.pack(side=tk.LEFT)

    def _browse_download_folder(self) -> None:
        """Abre diálogo para selecionar pasta de downloads padrão."""
        folder = filedialog.askdirectory(
            initialdir=self.download_path_var.get(),
            title="Selecione a pasta padrão de downloads"
        )
        if folder:
            self.download_path_var.set(folder)

    def _browse_ffmpeg(self) -> None:
        """Abre diálogo para selecionar executável do FFmpeg."""
        if os.name == "nt":  # Windows
            filetypes = [("Executável", "*.exe"), ("Todos os arquivos", "*.*")]
        else:
            filetypes = [("Executável", "*"), ("Todos os arquivos", "*.*")]
        
        file_path = filedialog.askopenfilename(
            title="Selecione o executável do FFmpeg",
            filetypes=filetypes
        )
        if file_path:
            self.ffmpeg_path_var.set(file_path)

    def _apply_settings(self) -> None:
        """Aplica as configurações."""
        download_path = self.download_path_var.get().strip()
        ffmpeg_path = self.ffmpeg_path_var.get().strip()

        # Validações
        if download_path:
            try:
                Path(download_path).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                messagebox.showerror(
                    "Erro",
                    f"Não foi possível criar/acessar a pasta de downloads:\n{e}"
                )
                return

        if ffmpeg_path:
            if not os.path.exists(ffmpeg_path):
                messagebox.showerror(
                    "Erro",
                    f"O arquivo do FFmpeg não foi encontrado:\n{ffmpeg_path}"
                )
                return

        # Aplica configurações (temporariamente, apenas na sessão atual)
        if download_path:
            Config.DEFAULT_DOWNLOAD_PATH = download_path
            Config.ensure_directories()

        if ffmpeg_path:
            Config.FFMPEG_PATH = ffmpeg_path
        else:
            Config.FFMPEG_PATH = None

        messagebox.showinfo(
            "Sucesso",
            "Configurações aplicadas com sucesso!\n\n"
            "Nota: Estas configurações são válidas apenas para esta sessão."
        )
        log.info("Configurações aplicadas")

    def _reset_settings(self) -> None:
        """Restaura as configurações padrão."""
        self.download_path_var.set(str(Path.home() / "Downloads" / "yt-downloads"))
        self.ffmpeg_path_var.set("")
        messagebox.showinfo("Informação", "Configurações restauradas para os valores padrão.")

