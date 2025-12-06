"""Aba de gerenciamento de fila de downloads."""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from services.queue_manager import DownloadStatus, QueueManager
from ui.components.video_list import VideoList
from ui.constants import (
    COLUMNS_QUEUE,
    COLUMN_WIDTHS_QUEUE,
    FONT_TITLE,
    PADDING_DEFAULT,
    QUEUE_BUTTON_CLEAR,
    QUEUE_BUTTON_PAUSE,
    QUEUE_BUTTON_RESUME,
    QUEUE_TITLE,
)
from utils.logger import get_logger

log = get_logger(__name__)


class QueueTab:
    """
    Aba de gerenciamento de fila de downloads.
    
    Exibe e controla a fila de downloads com opções para
    pausar, retomar, retentar e limpar itens concluídos.
    """

    def __init__(
        self,
        parent: ttk.Notebook,
        queue_manager: QueueManager,
    ) -> None:
        """
        Inicializa a aba de fila.
        
        Args:
            parent: Widget pai (Notebook) onde a aba será adicionada.
            queue_manager: Instância do gerenciador de fila.
        """
        self.frame = ttk.Frame(parent)
        self.queue_manager = queue_manager
        self._setup_ui()
        self._start_refresh_timer()

    def _setup_ui(self) -> None:
        """Configura a interface gráfica da aba."""
        # Container principal
        main_container = ttk.Frame(self.frame, padding=PADDING_DEFAULT)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Título e botões de controle
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        title_label = ttk.Label(
            header_frame,
            text=QUEUE_TITLE,
            font=FONT_TITLE
        )
        title_label.pack(side=tk.LEFT)

        # Botões de controle
        button_frame = ttk.Frame(header_frame)
        button_frame.pack(side=tk.RIGHT)

        self.pause_button = ttk.Button(
            button_frame,
            text=QUEUE_BUTTON_PAUSE,
            command=self._pause_queue
        )
        self.pause_button.pack(side=tk.LEFT, padx=(0, 5))

        self.resume_button = ttk.Button(
            button_frame,
            text=QUEUE_BUTTON_RESUME,
            command=self._resume_queue,
            state=tk.DISABLED
        )
        self.resume_button.pack(side=tk.LEFT, padx=(0, 5))

        self.clear_button = ttk.Button(
            button_frame,
            text=QUEUE_BUTTON_CLEAR,
            command=self._clear_completed
        )
        self.clear_button.pack(side=tk.LEFT)

        # Lista de downloads
        self.video_list = VideoList(
            main_container,
            columns=COLUMNS_QUEUE,
            column_widths=COLUMN_WIDTHS_QUEUE,
            on_select=self._on_item_select
        )
        
        # Bind de duplo clique para retentar
        self.video_list.tree.bind("<Double-1>", self._on_double_click)

    def _format_status(self, status: DownloadStatus) -> str:
        """
        Formata o status para exibição.
        
        Args:
            status: Status do download.
            
        Returns:
            String formatada do status.
        """
        return status.value

    def _format_progress(self, progress: float) -> str:
        """
        Formata o progresso para exibição.
        
        Args:
            progress: Porcentagem de progresso (0-100).
            
        Returns:
            String formatada do progresso.
        """
        return f"{progress:.1f}%"

    def _on_item_select(self, item: dict) -> None:
        """
        Handler chamado quando um item é selecionado.
        
        Args:
            item: Dicionário com os dados do item selecionado.
        """
        log.debug(f"Item selecionado: {item.get('Vídeo')}")

    def _on_double_click(self, event: tk.Event) -> None:
        """Handler para duplo clique - retenta item com erro."""
        item = self.video_list.get_selected_item()
        if item:
            original = item.get("_original")
            if original and original.status == DownloadStatus.ERROR:
                self._retry_item(original.id)

    def _pause_queue(self) -> None:
        """Pausa o processamento da fila."""
        self.queue_manager.pause()
        self.pause_button.config(state=tk.DISABLED)
        self.resume_button.config(state=tk.NORMAL)
        messagebox.showinfo("Fila Pausada", "A fila de downloads foi pausada.")

    def _resume_queue(self) -> None:
        """Retoma o processamento da fila."""
        self.queue_manager.resume()
        self.pause_button.config(state=tk.NORMAL)
        self.resume_button.config(state=tk.DISABLED)
        messagebox.showinfo("Fila Retomada", "A fila de downloads foi retomada.")

    def _retry_item(self, item_id: str) -> None:
        """
        Tenta novamente um item que falhou.
        
        Args:
            item_id: ID do item a ser retentado.
        """
        self.queue_manager.retry_item(item_id)
        self.refresh()
        messagebox.showinfo("Item Reenfileirado", "O item foi adicionado novamente à fila.")

    def _clear_completed(self) -> None:
        """Remove todos os itens concluídos da fila."""
        removed = self.queue_manager.clear_completed()
        self.refresh()
        messagebox.showinfo(
            "Itens Removidos",
            f"{removed} item(ns) concluído(s) removido(s) da fila."
        )

    def refresh(self) -> None:
        """Atualiza a lista de downloads da fila."""
        try:
            items = self.queue_manager.get_all_items()
            
            # Formata dados para exibição
            formatted_data = []
            for item in items:
                # Determina ação disponível
                action = ""
                if item.status == DownloadStatus.ERROR:
                    action = "Retentar"
                elif item.status == DownloadStatus.PAUSED:
                    action = "Retomar"
                
                formatted_item = {
                    "Vídeo": item.title,
                    "Status": self._format_status(item.status),
                    "Progresso": self._format_progress(item.progress),
                    "Ação": action,
                    # Mantém dados originais para referência
                    "_original": item,
                }
                formatted_data.append(formatted_item)
            
            self.video_list.load_data(formatted_data)
            
            # Atualiza estado dos botões
            has_items = len(items) > 0
            has_completed = any(
                item.status == DownloadStatus.COMPLETED for item in items
            )
            self.clear_button.config(state=tk.NORMAL if has_completed else tk.DISABLED)
            
            log.debug(f"Fila atualizada: {len(formatted_data)} itens")
        except Exception as e:
            log.error(f"Erro ao atualizar fila: {e}")

    def _start_refresh_timer(self) -> None:
        """Inicia timer para atualizar a lista periodicamente."""
        self.refresh()
        # Agenda próxima atualização
        self.frame.after(1000, self._start_refresh_timer)

