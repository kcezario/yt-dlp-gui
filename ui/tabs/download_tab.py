"""Aba de download da interface gráfica."""

import os
import queue
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, List, Optional

import yt_dlp

from config import Config
from database.connection import DBConnection
from database.dao import HistoryDAO, VideoDAO
from services.download_manager import DownloadManager
from services.queue_manager import QueueManager
from services.validation import validate_download_url
from utils.logger import get_logger

log = get_logger(__name__)


class DownloadTab:
    """
    Aba de download com interface para inserir URL, selecionar pasta,
    escolher formato e iniciar downloads.
    """

    def __init__(
        self,
        parent: ttk.Notebook,
        db: Optional[DBConnection] = None,
        history_tab_ref: Optional[Callable[[], None]] = None,
        queue_manager: Optional[QueueManager] = None,
        queue_tab_ref: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Inicializa a aba de download.
        
        Args:
            parent: Widget pai (Notebook) onde a aba será adicionada.
            db: Instância da conexão com o banco de dados (opcional).
            history_tab_ref: Função para atualizar a aba de histórico (opcional).
            queue_manager: Gerenciador de fila de downloads (opcional).
            queue_tab_ref: Função para atualizar a aba de fila (opcional).
        """
        self.frame = ttk.Frame(parent)
        self.download_manager = DownloadManager()
        self.queue_manager = queue_manager
        if self.queue_manager:
            self.queue_manager.set_download_manager(self.download_manager)
        self.db = db
        self.history_tab_ref = history_tab_ref
        self.queue_tab_ref = queue_tab_ref
        
        # DAOs
        self.history_dao = HistoryDAO(db) if db else None
        self.video_dao = VideoDAO(db) if db else None
        
        # Fila para comunicação thread-safe entre download thread e GUI
        self.message_queue: queue.Queue = queue.Queue()
        
        # Variáveis de controle
        self.is_downloading = False
        self.current_video_info: Optional[dict] = None
        self.current_history_id: Optional[int] = None
        
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

        # Frame para tipo de download
        type_frame = ttk.LabelFrame(main_container, text="Tipo de Download", padding="10")
        type_frame.pack(fill=tk.X, pady=(0, 10))

        self.download_type_var = tk.StringVar(value="video")
        
        video_radio = ttk.Radiobutton(
            type_frame,
            text="Vídeo Único",
            variable=self.download_type_var,
            value="video"
        )
        video_radio.pack(side=tk.LEFT, padx=(0, 20))

        playlist_radio = ttk.Radiobutton(
            type_frame,
            text="Playlist",
            variable=self.download_type_var,
            value="playlist"
        )
        playlist_radio.pack(side=tk.LEFT, padx=(0, 20))

        channel_radio = ttk.Radiobutton(
            type_frame,
            text="Canal",
            variable=self.download_type_var,
            value="channel"
        )
        channel_radio.pack(side=tk.LEFT)

        # Frame para URL
        url_frame = ttk.LabelFrame(main_container, text="URL", padding="10")
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

    def _extract_video_info(self, url: str) -> Optional[dict]:
        """
        Extrai informações do vídeo antes de iniciar o download.
        
        Args:
            url: URL do vídeo.
            
        Returns:
            Dicionário com informações do vídeo ou None em caso de erro.
        """
        try:
            ydl_opts = {"quiet": True, "no_warnings": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    "id": info.get("id", ""),
                    "title": info.get("title", "Desconhecido"),
                    "duration": info.get("duration"),
                    "channel": info.get("uploader") or info.get("channel", ""),
                    "upload_date": info.get("upload_date", ""),
                    "url": url,
                    "thumbnail_url": info.get("thumbnail"),
                    "description": info.get("description", ""),
                }
        except Exception as e:
            log.error(f"Erro ao extrair informações do vídeo: {e}")
            return None

    def _extract_playlist_videos(self, url: str) -> List[dict]:
        """
        Extrai lista de vídeos de uma playlist ou canal.
        
        Args:
            url: URL da playlist ou canal.
            
        Returns:
            Lista de dicionários com informações dos vídeos.
        """
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,  # Extrai apenas metadados, não baixa
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                videos = []
                entries = info.get("entries", [])
                
                for entry in entries:
                    if entry:
                        video_url = f"https://www.youtube.com/watch?v={entry.get('id', '')}"
                        videos.append({
                            "id": entry.get("id", ""),
                            "title": entry.get("title", "Desconhecido"),
                            "url": video_url,
                            "duration": entry.get("duration"),
                            "channel": entry.get("uploader") or entry.get("channel", ""),
                        })
                
                return videos
        except Exception as e:
            log.error(f"Erro ao extrair vídeos da playlist: {e}")
            return []

    def _start_download(self) -> None:
        """Inicia o download do vídeo ou playlist."""
        url = self.url_entry.get().strip()
        path = self.path_var.get().strip()
        mode = self.format_var.get()
        download_type = self.download_type_var.get()

        # Validação de URL
        is_valid, error_msg = validate_download_url(url)
        if not is_valid:
            messagebox.showerror("URL Inválida", error_msg)
            return

        if not path:
            messagebox.showerror("Erro", "Por favor, selecione uma pasta de destino.")
            return

        # Verifica FFmpeg para downloads de áudio
        if mode.lower() == "mp3" and not self.download_manager._ffmpeg_path:
            response = messagebox.askyesno(
                "FFmpeg Não Encontrado",
                "FFmpeg não foi encontrado no sistema.\n\n"
                "FFmpeg é necessário para downloads de áudio (MP3).\n\n"
                "Deseja continuar mesmo assim? (O download pode falhar)"
            )
            if not response:
                return

        # Valida se a pasta existe ou pode ser criada
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível criar/acessar a pasta:\n{e}")
            return

        # Processa baseado no tipo
        if download_type == "video":
            self._download_single_video(url, path, mode)
        elif download_type in ("playlist", "channel"):
            self._download_playlist(url, path, mode)

    def _download_single_video(self, url: str, path: str, mode: str) -> None:
        """Inicia download de um vídeo único."""
        # Extrai informações do vídeo
        self.status_label.config(text="Extraindo informações do vídeo...", foreground="blue")
        video_info = self._extract_video_info(url)
        
        if not video_info:
            error_msg = (
                "Não foi possível extrair informações do vídeo.\n\n"
                "Possíveis causas:\n"
                "• Sem conexão com a internet\n"
                "• URL inválida ou vídeo não disponível\n"
                "• YouTube bloqueou o acesso\n\n"
                "Verifique sua conexão e tente novamente."
            )
            messagebox.showerror("Erro ao Extrair Informações", error_msg)
            self.status_label.config(text="Erro ao extrair informações", foreground="red")
            return

        self.current_video_info = video_info

        # Salva vídeo no banco de dados
        if self.video_dao:
            try:
                self.video_dao.upsert(video_info)
            except Exception as e:
                log.warning(f"Erro ao salvar vídeo no banco: {e}")

        # Cria registro de histórico
        if self.history_dao:
            try:
                history_data = {
                    "video_id": video_info.get("id"),
                    "status": "downloading",
                    "download_started_at": datetime.now().isoformat(),
                }
                self.current_history_id = self.history_dao.add_history(history_data)
            except Exception as e:
                log.warning(f"Erro ao criar registro de histórico: {e}")

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

    def _download_playlist(self, url: str, path: str, mode: str) -> None:
        """Extrai e adiciona vídeos de playlist/canal à fila."""
        if not self.queue_manager:
            messagebox.showerror(
                "Erro",
                "Gerenciador de fila não disponível.\n"
                "Downloads de playlist requerem o sistema de fila."
            )
            return

        self.status_label.config(text="Extraindo lista de vídeos...", foreground="blue")
        videos = self._extract_playlist_videos(url)
        
        if not videos:
            error_msg = (
                "Não foi possível extrair vídeos da playlist/canal.\n\n"
                "Possíveis causas:\n"
                "• Sem conexão com a internet\n"
                "• URL inválida ou playlist/canal não disponível\n"
                "• YouTube bloqueou o acesso\n\n"
                "Verifique sua conexão e tente novamente."
            )
            messagebox.showerror("Erro ao Extrair Playlist", error_msg)
            self.status_label.config(text="Erro ao extrair playlist", foreground="red")
            return

        # Adiciona vídeos à fila
        added_count = 0
        for video in videos:
            video_id = video.get("id")
            
            # Cria registro de histórico antes de adicionar à fila
            if self.history_dao and video_id:
                try:
                    # Salva vídeo no banco
                    if self.video_dao:
                        video_info = {
                            "id": video_id,
                            "title": video["title"],
                            "url": video["url"],
                            "duration": video.get("duration"),
                            "channel": video.get("channel", ""),
                        }
                        self.video_dao.upsert(video_info)
                    
                    # Cria registro de histórico
                    history_data = {
                        "video_id": video_id,
                        "status": "downloading",
                        "download_started_at": datetime.now().isoformat(),
                    }
                    self.history_dao.add_history(history_data)
                except Exception as e:
                    log.warning(f"Erro ao criar histórico para vídeo {video_id}: {e}")
            
            item_id = self.queue_manager.add_item(
                url=video["url"],
                title=video["title"],
                path=path,
                mode=mode,
                video_id=video_id,
                on_progress=self._on_queue_progress,
                on_complete=self._on_queue_complete,
            )
            added_count += 1

        messagebox.showinfo(
            "Playlist Adicionada",
            f"{added_count} vídeo(s) adicionado(s) à fila de downloads.\n\n"
            "Acompanhe o progresso na aba 'Fila de Downloads'."
        )
        
        self.status_label.config(
            text=f"{added_count} vídeo(s) na fila",
            foreground="green"
        )
        
        # Atualiza aba de fila
        if self.queue_tab_ref:
            try:
                self.queue_tab_ref()
            except Exception as e:
                log.warning(f"Erro ao atualizar aba de fila: {e}")

    def _on_queue_progress(self, item_id: str, percent: float, msg: str) -> None:
        """Callback de progresso para itens da fila."""
        if self.queue_tab_ref:
            try:
                self.queue_tab_ref()
            except Exception:
                pass

    def _on_queue_complete(self, item_id: str, success: bool, msg: str, file_path: Optional[str]) -> None:
        """
        Callback de conclusão para itens da fila.
        Salva no banco de dados e atualiza as abas.
        """
        # Obtém o item da fila
        if not self.queue_manager:
            return
        
        item = self.queue_manager.get_item(item_id)
        if not item:
            return

        # Salva vídeo no banco de dados
        if self.video_dao and item.video_id:
            try:
                # Extrai informações do vídeo se necessário
                video_info = {
                    "id": item.video_id,
                    "title": item.title,
                    "url": item.url,
                    "file_path": file_path if success else None,
                }
                
                # Tenta obter mais informações se possível
                try:
                    full_info = self._extract_video_info(item.url)
                    if full_info:
                        video_info.update(full_info)
                        if file_path and success:
                            video_info["file_path"] = file_path
                except Exception:
                    pass  # Usa informações básicas se não conseguir extrair
                
                self.video_dao.upsert(video_info)
            except Exception as e:
                log.warning(f"Erro ao salvar vídeo no banco: {e}")

        # Cria/atualiza registro de histórico
        if self.history_dao and self.db and item.video_id:
            try:
                # Busca se já existe histórico para este vídeo
                cursor = self.db.connection.cursor()
                cursor.execute(
                    "SELECT id FROM history WHERE video_id = ? ORDER BY created_at DESC LIMIT 1",
                    (item.video_id,)
                )
                existing = cursor.fetchone()
                log.debug(f"Buscando histórico para vídeo {item.video_id}: {'encontrado' if existing else 'não encontrado'}")
                
                history_data = {
                    "video_id": item.video_id,
                    "status": "completed" if success else "failed",
                    "download_completed_at": datetime.now().isoformat(),
                    "error_message": None if success else msg,
                }
                
                if file_path and success:
                    history_data["file_path"] = file_path
                    try:
                        if os.path.exists(file_path):
                            history_data["file_size"] = os.path.getsize(file_path)
                    except Exception:
                        pass

                if existing:
                    # Atualiza registro existente
                    history_id = existing["id"]
                    cursor.execute("""
                        UPDATE history 
                        SET status = ?, download_completed_at = ?, 
                            file_path = ?, file_size = ?, error_message = ?
                        WHERE id = ?
                    """, (
                        history_data["status"],
                        history_data["download_completed_at"],
                        history_data.get("file_path"),
                        history_data.get("file_size"),
                        history_data.get("error_message"),
                        history_id,
                    ))
                    log.info(f"Histórico atualizado para vídeo {item.video_id} (status: {history_data['status']})")
                else:
                    # Cria novo registro se não existir
                    history_data["download_started_at"] = datetime.now().isoformat()
                    self.history_dao.add_history(history_data)
                    log.info(f"Novo histórico criado para vídeo {item.video_id} (status: {history_data['status']})")
                
                self.db.connection.commit()
            except Exception as e:
                log.error(f"Erro ao salvar histórico para vídeo {item.video_id if item.video_id else 'desconhecido'}: {e}", exc_info=True)
        elif not item.video_id:
            log.warning(f"Item {item_id[:8]} não possui video_id, histórico não será salvo")

        # Atualiza abas
        if self.queue_tab_ref:
            try:
                self.queue_tab_ref()
            except Exception:
                pass
        
        if self.history_tab_ref:
            try:
                self.history_tab_ref()
            except Exception:
                pass

    def _on_progress_callback(self, percent: float, msg: str) -> None:
        """
        Callback de progresso chamado pela thread de download.
        Envia mensagem para a fila para processamento na thread principal.
        
        Args:
            percent: Porcentagem do download (0-100).
            msg: Mensagem de status.
        """
        self.message_queue.put(("progress", percent, msg))

    def _on_complete_callback(self, success: bool, msg: str, file_path: Optional[str] = None) -> None:
        """
        Callback de conclusão chamado pela thread de download.
        Envia mensagem para a fila para processamento na thread principal.
        
        Args:
            success: True se o download foi bem-sucedido.
            msg: Mensagem de status.
            file_path: Caminho do arquivo baixado (opcional).
        """
        self.message_queue.put(("complete", success, msg, file_path))

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
            file_path = message[3] if len(message) > 3 else None
            
            self.is_downloading = False
            self.download_button.config(state=tk.NORMAL)
            self.url_entry.config(state=tk.NORMAL)

            # Atualiza histórico no banco de dados
            if self.history_dao and self.current_history_id:
                try:
                    history_update = {
                        "status": "completed" if success else "failed",
                        "download_completed_at": datetime.now().isoformat(),
                        "error_message": None if success else msg,
                    }
                    
                    if file_path and success:
                        history_update["file_path"] = file_path
                        # Tenta obter tamanho do arquivo
                        try:
                            if os.path.exists(file_path):
                                history_update["file_size"] = os.path.getsize(file_path)
                        except Exception:
                            pass
                    
                    # Atualiza registro de histórico
                    if not self.db:
                        return
                    cursor = self.db.connection.cursor()
                    cursor.execute("""
                        UPDATE history 
                        SET status = ?, download_completed_at = ?, 
                            file_path = ?, file_size = ?, error_message = ?
                        WHERE id = ?
                    """, (
                        history_update["status"],
                        history_update["download_completed_at"],
                        history_update.get("file_path"),
                        history_update.get("file_size"),
                        history_update.get("error_message"),
                        self.current_history_id,
                    ))
                    self.db.connection.commit()
                    
                    # Atualiza caminho do arquivo no vídeo
                    if file_path and success and self.video_dao and self.current_video_info:
                        self.current_video_info["file_path"] = file_path
                        self.video_dao.upsert(self.current_video_info)
                    
                except Exception as e:
                    log.error(f"Erro ao atualizar histórico: {e}")

            # Atualiza aba de histórico se disponível
            if self.history_tab_ref:
                try:
                    log.debug("Atualizando aba de histórico automaticamente")
                    self.history_tab_ref()
                except Exception as e:
                    log.warning(f"Erro ao atualizar aba de histórico: {e}")

            if success:
                self.progress_var.set(100)
                self.status_label.config(text=msg, foreground="green")
                messagebox.showinfo("Sucesso", msg)
            else:
                self.progress_var.set(0)
                self.status_label.config(text=msg, foreground="red")
                messagebox.showerror("Erro", msg)

            # Limpa variáveis
            self.current_video_info = None
            self.current_history_id = None

            log.info(f"Download finalizado: {msg}")

