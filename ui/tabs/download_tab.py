"""Aba de download da interface gráfica."""

import queue
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional

from config import Config
from services.download_manager import DownloadManager
from utils.logger import get_logger

log = get_logger(__name__)


class DownloadTab:
    """
    Aba de download com interface para inserir URL, selecionar pasta,
    escolher formato e iniciar downloads.
    """

    def __init__(self, parent: ttk.Notebook) -> None:
        """
        Inicializa a aba de download.
        
        Args:
            parent: Widget pai (Notebook) onde a aba será adicionada.
        """
        self.frame = ttk.Frame(parent)
        self.download_manager = DownloadManager()
        
        # Fila para comunicação thread-safe entre download thread e GUI
        self.message_queue: queue.Queue = queue.Queue()
        
        # Variáveis de controle
        self.is_downloading = False
        
        self._setup_ui()
        self._start_queue_processor()

    def _setup_ui(self) -> None:
        """Configura a interface gráfica da aba."""
        # Container principal com padding
        main_container = ttk.Frame(self.frame, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)

        # Título
        title_label = ttk.Label(
            main_container,
            text="Download de Vídeos",
            font=("", 14, "bold")
        )
        title_label.pack(pady=(0, 20))

        # Frame para URL
        url_frame = ttk.LabelFrame(main_container, text="URL do Vídeo", padding="10")
        url_frame.pack(fill=tk.X, pady=(0, 10))

        self.url_entry = ttk.Entry(url_frame, width=60)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.url_entry.bind("<Return>", lambda e: self._start_download())

        # Frame para seleção de pasta
        path_frame = ttk.LabelFrame(main_container, text="Pasta de Destino", padding="10")
        path_frame.pack(fill=tk.X, pady=(0, 10))

        self.path_var = tk.StringVar(value=Config.DEFAULT_DOWNLOAD_PATH)
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=50)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        browse_button = ttk.Button(
            path_frame,
            text="Procurar...",
            command=self._browse_folder
        )
        browse_button.pack(side=tk.LEFT)

        # Frame para formato
        format_frame = ttk.LabelFrame(main_container, text="Formato", padding="10")
        format_frame.pack(fill=tk.X, pady=(0, 10))

        self.format_var = tk.StringVar(value="mp4")
        
        mp4_radio = ttk.Radiobutton(
            format_frame,
            text="Vídeo (MP4)",
            variable=self.format_var,
            value="mp4"
        )
        mp4_radio.pack(side=tk.LEFT, padx=(0, 20))

        mp3_radio = ttk.Radiobutton(
            format_frame,
            text="Áudio (MP3)",
            variable=self.format_var,
            value="mp3"
        )
        mp3_radio.pack(side=tk.LEFT)

        # Botão de download
        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        self.download_button = ttk.Button(
            button_frame,
            text="Baixar",
            command=self._start_download,
            state=tk.NORMAL
        )
        self.download_button.pack(side=tk.LEFT, padx=(0, 5))

        # Barra de progresso
        progress_frame = ttk.LabelFrame(main_container, text="Progresso", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=400,
            mode="determinate"
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        self.status_label = ttk.Label(
            progress_frame,
            text="Pronto para baixar",
            foreground="gray"
        )
        self.status_label.pack(fill=tk.X)

    def _browse_folder(self) -> None:
        """Abre diálogo para selecionar pasta de destino."""
        folder = filedialog.askdirectory(
            initialdir=self.path_var.get(),
            title="Selecione a pasta de destino"
        )
        if folder:
            self.path_var.set(folder)

    def _start_download(self) -> None:
        """Inicia o download do vídeo."""
        url = self.url_entry.get().strip()
        path = self.path_var.get().strip()
        mode = self.format_var.get()

        # Validações
        if not url:
            messagebox.showerror("Erro", "Por favor, insira uma URL válida.")
            return

        if not path:
            messagebox.showerror("Erro", "Por favor, selecione uma pasta de destino.")
            return

        # Verifica se já está baixando
        if self.is_downloading:
            messagebox.showwarning("Aviso", "Já existe um download em andamento.")
            return

        # Valida se a pasta existe ou pode ser criada
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível criar/acessar a pasta:\n{e}")
            return

        # Atualiza UI
        self.is_downloading = True
        self.download_button.config(state=tk.DISABLED)
        self.url_entry.config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.status_label.config(text="Iniciando download...", foreground="blue")

        log.info(f"Iniciando download: {url} (modo: {mode})")

        # Inicia download em thread separada
        self.download_manager.start_download_thread(
            url=url,
            path=path,
            mode=mode,
            on_progress=self._on_progress_callback,
            on_complete=self._on_complete_callback
        )

    def _on_progress_callback(self, percent: float, msg: str) -> None:
        """
        Callback de progresso chamado pela thread de download.
        Envia mensagem para a fila para processamento na thread principal.
        
        Args:
            percent: Porcentagem do download (0-100).
            msg: Mensagem de status.
        """
        self.message_queue.put(("progress", percent, msg))

    def _on_complete_callback(self, success: bool, msg: str) -> None:
        """
        Callback de conclusão chamado pela thread de download.
        Envia mensagem para a fila para processamento na thread principal.
        
        Args:
            success: True se o download foi bem-sucedido.
            msg: Mensagem de status.
        """
        self.message_queue.put(("complete", success, msg))

    def _start_queue_processor(self) -> None:
        """
        Inicia o processador de mensagens da fila.
        Usa root.after para processar mensagens na thread principal.
        """
        self._process_queue()

    def _process_queue(self) -> None:
        """
        Processa mensagens da fila na thread principal.
        Deve ser chamado periodicamente usando root.after.
        """
        try:
            while True:
                try:
                    message = self.message_queue.get_nowait()
                    self._handle_message(message)
                except queue.Empty:
                    break
        except Exception as e:
            log.error(f"Erro ao processar fila: {e}")

        # Agenda próxima verificação
        self.frame.after(100, self._process_queue)

    def _handle_message(self, message: tuple) -> None:
        """
        Processa uma mensagem da fila.
        
        Args:
            message: Tupla com tipo de mensagem e dados.
        """
        msg_type = message[0]

        if msg_type == "progress":
            _, percent, msg = message
            self.progress_var.set(percent)
            self.status_label.config(text=msg, foreground="blue")

        elif msg_type == "complete":
            _, success, msg = message
            self.is_downloading = False
            self.download_button.config(state=tk.NORMAL)
            self.url_entry.config(state=tk.NORMAL)

            if success:
                self.progress_var.set(100)
                self.status_label.config(text=msg, foreground="green")
                messagebox.showinfo("Sucesso", msg)
            else:
                self.progress_var.set(0)
                self.status_label.config(text=msg, foreground="red")
                messagebox.showerror("Erro", msg)

            log.info(f"Download finalizado: {msg}")

