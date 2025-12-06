"""Gerenciador de fila de downloads."""

import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

from utils.logger import get_logger

log = get_logger(__name__)


class DownloadStatus(Enum):
    """Status de um item na fila de downloads."""
    QUEUED = "Na Fila"
    DOWNLOADING = "Baixando"
    PAUSED = "Pausado"
    COMPLETED = "Concluído"
    ERROR = "Erro"
    CANCELLED = "Cancelado"


@dataclass
class QueueItem:
    """Item na fila de downloads."""
    id: str
    url: str
    title: str
    path: str
    mode: str
    status: DownloadStatus = DownloadStatus.QUEUED
    progress: float = 0.0
    error_message: Optional[str] = None
    file_path: Optional[str] = None
    video_id: Optional[str] = None
    # Callbacks
    on_progress: Optional[Callable[[str, float, str], None]] = None
    on_complete: Optional[Callable[[str, bool, str, Optional[str]], None]] = None


class QueueManager:
    """
    Gerenciador de fila de downloads.
    
    Gerencia uma fila de downloads, processando sequencialmente
    e permitindo controle (pausar, retomar, cancelar).
    """

    def __init__(self) -> None:
        """Inicializa o gerenciador de fila."""
        self.queue: List[QueueItem] = []
        self.current_item: Optional[QueueItem] = None
        self._lock = threading.Lock()
        self._paused = False
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._download_manager = None  # Será injetado

    def set_download_manager(self, download_manager) -> None:
        """Define o gerenciador de downloads a ser usado."""
        self._download_manager = download_manager

    def add_item(
        self,
        url: str,
        title: str,
        path: str,
        mode: str,
        video_id: Optional[str] = None,
        on_progress: Optional[Callable[[str, float, str], None]] = None,
        on_complete: Optional[Callable[[str, bool, str, Optional[str]], None]] = None,
    ) -> str:
        """
        Adiciona um item à fila.
        
        Args:
            url: URL do vídeo.
            title: Título do vídeo.
            path: Caminho de destino.
            mode: Modo de download ('mp3' ou 'mp4').
            video_id: ID do vídeo (opcional).
            on_progress: Callback de progresso (item_id, percent, message).
            on_complete: Callback de conclusão (item_id, success, message, file_path).
            
        Returns:
            ID único do item na fila.
        """
        import uuid
        item_id = str(uuid.uuid4())
        
        item = QueueItem(
            id=item_id,
            url=url,
            title=title,
            path=path,
            mode=mode,
            video_id=video_id,
            on_progress=on_progress,
            on_complete=on_complete,
        )
        
        with self._lock:
            self.queue.append(item)
        
        log.info(f"Item adicionado à fila: {title} ({item_id[:8]})")
        
        # Inicia worker se não estiver rodando
        if not self._worker_thread or not self._worker_thread.is_alive():
            self._start_worker()
        
        return item_id

    def get_item(self, item_id: str) -> Optional[QueueItem]:
        """
        Retorna um item da fila pelo ID.
        
        Args:
            item_id: ID do item.
            
        Returns:
            Item da fila ou None se não encontrado.
        """
        with self._lock:
            for item in self.queue:
                if item.id == item_id:
                    return item
            if self.current_item and self.current_item.id == item_id:
                return self.current_item
        return None

    def get_all_items(self) -> List[QueueItem]:
        """
        Retorna todos os itens da fila.
        
        Returns:
            Lista de todos os itens (incluindo o atual).
        """
        with self._lock:
            items = self.queue.copy()
            if self.current_item:
                items.insert(0, self.current_item)
            return items

    def pause(self) -> None:
        """Pausa o processamento da fila."""
        with self._lock:
            self._paused = True
            if self.current_item:
                self.current_item.status = DownloadStatus.PAUSED
        log.info("Fila pausada")

    def resume(self) -> None:
        """Retoma o processamento da fila."""
        with self._lock:
            self._paused = False
        self._stop_event.clear()
        log.info("Fila retomada")
        
        # Reinicia worker se necessário
        if not self._worker_thread or not self._worker_thread.is_alive():
            self._start_worker()

    def retry_item(self, item_id: str) -> None:
        """
        Tenta novamente um item que falhou.
        
        Args:
            item_id: ID do item a ser retentado.
        """
        with self._lock:
            item = self.get_item(item_id)
            if item:
                item.status = DownloadStatus.QUEUED
                item.progress = 0.0
                item.error_message = None
                
                # Move para o final da fila se não estiver lá
                if item in self.queue:
                    self.queue.remove(item)
                self.queue.append(item)
                
                log.info(f"Item {item_id[:8]} marcado para retentar")

    def remove_item(self, item_id: str) -> bool:
        """
        Remove um item da fila.
        
        Args:
            item_id: ID do item a ser removido.
            
        Returns:
            True se o item foi removido, False caso contrário.
        """
        with self._lock:
            # Remove da fila
            for item in self.queue:
                if item.id == item_id:
                    self.queue.remove(item)
                    log.info(f"Item {item_id[:8]} removido da fila")
                    return True
            
            # Se for o item atual, cancela
            if self.current_item and self.current_item.id == item_id:
                self.current_item.status = DownloadStatus.CANCELLED
                self._stop_event.set()
                log.info(f"Item atual {item_id[:8]} cancelado")
                return True
        
        return False

    def clear_completed(self) -> int:
        """
        Remove todos os itens concluídos da fila.
        
        Returns:
            Número de itens removidos.
        """
        with self._lock:
            removed = 0
            self.queue = [
                item for item in self.queue
                if item.status != DownloadStatus.COMPLETED
            ]
            removed = len([item for item in self.queue if item.status == DownloadStatus.COMPLETED])
        log.info(f"{removed} itens concluídos removidos da fila")
        return removed

    def _start_worker(self) -> None:
        """Inicia a thread worker que processa a fila."""
        if self._worker_thread and self._worker_thread.is_alive():
            return
        
        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        log.debug("Worker thread da fila iniciada")

    def _worker_loop(self) -> None:
        """Loop principal do worker que processa a fila."""
        while True:
            if self._stop_event.is_set():
                break
            
            # Verifica se está pausado
            if self._paused:
                threading.Event().wait(1)
                continue
            
            # Pega próximo item da fila
            with self._lock:
                if not self.queue:
                    break
                self.current_item = self.queue.pop(0)
                item = self.current_item
            
            if item.status == DownloadStatus.CANCELLED:
                continue
            
            # Processa o item
            self._process_item(item)
            
            # Limpa item atual
            with self._lock:
                self.current_item = None
        
        log.debug("Worker thread da fila finalizada")

    def _process_item(self, item: QueueItem) -> None:
        """
        Processa um item da fila.
        
        Args:
            item: Item a ser processado.
        """
        if not self._download_manager:
            log.error("DownloadManager não configurado")
            return
        
        item.status = DownloadStatus.DOWNLOADING
        
        # Evento para sincronizar conclusão
        download_complete = threading.Event()
        download_result = {"success": False, "msg": "", "file_path": None}
        
        def progress_callback(percent: float, msg: str) -> None:
            """Callback de progresso."""
            item.progress = percent
            if item.on_progress:
                item.on_progress(item.id, percent, msg)
        
        def complete_callback(success: bool, msg: str, file_path: Optional[str] = None) -> None:
            """Callback de conclusão."""
            download_result["success"] = success
            download_result["msg"] = msg
            download_result["file_path"] = file_path
            
            if success:
                item.status = DownloadStatus.COMPLETED
                item.progress = 100.0
                item.file_path = file_path
            else:
                item.status = DownloadStatus.ERROR
                item.error_message = msg
                item.progress = 0.0
            
            if item.on_complete:
                item.on_complete(item.id, success, msg, file_path)
            
            download_complete.set()
        
        # Inicia download
        try:
            self._download_manager.start_download_thread(
                url=item.url,
                path=item.path,
                mode=item.mode,
                on_progress=progress_callback,
                on_complete=complete_callback,
            )
            
            # Aguarda conclusão ou pausa
            while not download_complete.is_set():
                if self._stop_event.is_set():
                    item.status = DownloadStatus.CANCELLED
                    break
                if self._paused:
                    item.status = DownloadStatus.PAUSED
                    break
                download_complete.wait(timeout=0.5)
                
        except Exception as e:
            log.error(f"Erro ao processar item {item.id[:8]}: {e}")
            item.status = DownloadStatus.ERROR
            item.error_message = str(e)
            if item.on_complete:
                item.on_complete(item.id, False, str(e), None)

