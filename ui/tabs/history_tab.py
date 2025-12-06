"""Aba de histórico de downloads."""

import os
import subprocess
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING, Optional

from database.connection import DBConnection
from database.constants import SQL_DELETE_HISTORY
from database.dao import HistoryDAO, VideoDAO
from config import Config
from ui.components.video_list import VideoList

if TYPE_CHECKING:
    from services.queue_manager import QueueManager
from ui.constants import (
    COLUMNS_HISTORY,
    COLUMN_WIDTHS_HISTORY,
    FONT_TITLE,
    HISTORY_BUTTON_REFRESH,
    HISTORY_MENU_DELETE,
    HISTORY_MENU_OPEN_FOLDER,
    HISTORY_MENU_RETRY,
    HISTORY_TITLE,
    PADDING_DEFAULT,
)
from utils.logger import get_logger

log = get_logger(__name__)


class HistoryTab:
    """
    Aba de histórico que exibe os downloads realizados.
    
    Mostra uma tabela com informações dos downloads, incluindo
    título do vídeo, status, data, etc.
    """

    def __init__(
        self, 
        parent: ttk.Notebook, 
        db: DBConnection,
        queue_manager: Optional["QueueManager"] = None
    ) -> None:
        """
        Inicializa a aba de histórico.
        
        Args:
            parent: Widget pai (Notebook) onde a aba será adicionada.
            db: Instância da conexão com o banco de dados.
            queue_manager: Gerenciador de fila de downloads (opcional).
        """
        self.frame = ttk.Frame(parent)
        self.db = db
        self.history_dao = HistoryDAO(db)
        self.video_dao = VideoDAO(db) if db else None
        self.queue_manager = queue_manager
        
        self._setup_ui()
        self.load_history()

    def _setup_ui(self) -> None:
        """Configura a interface gráfica da aba."""
        # Container principal
        main_container = ttk.Frame(self.frame, padding=PADDING_DEFAULT)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Título e botão de atualizar
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        title_label = ttk.Label(
            header_frame,
            text=HISTORY_TITLE,
            font=FONT_TITLE
        )
        title_label.pack(side=tk.LEFT)

        refresh_button = ttk.Button(
            header_frame,
            text=HISTORY_BUTTON_REFRESH,
            command=self.load_history
        )
        refresh_button.pack(side=tk.RIGHT)

        # Lista de vídeos
        self.video_list = VideoList(
            main_container,
            columns=COLUMNS_HISTORY,
            column_widths=COLUMN_WIDTHS_HISTORY,
            on_select=self._on_item_select
        )
        
        # Adiciona menu de contexto
        self._setup_context_menu()

    def _format_status(self, status: str) -> str:
        """
        Formata o status para exibição.
        
        Args:
            status: Status do download.
            
        Returns:
            String formatada do status.
        """
        status_map = {
            "pending": "Pendente",
            "downloading": "Baixando",
            "completed": "Concluído",
            "failed": "Falhou",
        }
        return status_map.get(status, status.title())

    def _format_date(self, date_str: Optional[str]) -> str:
        """
        Formata a data para exibição.
        
        Args:
            date_str: String de data ou None.
            
        Returns:
            String formatada da data.
        """
        if not date_str:
            return ""
        try:
            # Tenta parsear diferentes formatos
            if isinstance(date_str, str):
                # SQLite retorna formato ISO
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                return dt.strftime("%d/%m/%Y %H:%M")
            return str(date_str)
        except Exception:
            return str(date_str)

    def _format_path(self, path: Optional[str]) -> str:
        """
        Formata o caminho do arquivo para exibição (trunca se muito longo).
        
        Args:
            path: Caminho do arquivo.
            
        Returns:
            String formatada do caminho.
        """
        if not path:
            return ""
        if len(path) > 50:
            return "..." + path[-47:]
        return path

    def load_history(self, limit: Optional[int] = None) -> None:
        """
        Carrega o histórico de downloads do banco de dados.
        
        Args:
            limit: Número máximo de registros a carregar (padrão: Config.HISTORY_LIMIT_DEFAULT).
        """
        if limit is None:
            limit = Config.HISTORY_LIMIT_DEFAULT
        try:
            history_data = self.history_dao.get_history(limit=limit)
            
            # Formata dados para exibição
            formatted_data = []
            for item in history_data:
                formatted_item = {
                    "Título": item.get("video_title") or item.get("playlist_title") or "Desconhecido",
                    "Status": self._format_status(item.get("status", "unknown")),
                    "Data": self._format_date(item.get("created_at")),
                    "Caminho": self._format_path(item.get("file_path")),
                    # Mantém dados originais para referência
                    "_original": item,
                }
                formatted_data.append(formatted_item)
            
            self.video_list.load_data(formatted_data)
            log.info(f"Histórico carregado: {len(formatted_data)} registros")
        except Exception as e:
            log.error(f"Erro ao carregar histórico: {e}")

    def _setup_context_menu(self) -> None:
        """Configura o menu de contexto (botão direito) na Treeview."""
        self.context_menu = tk.Menu(self.frame, tearoff=0)
        
        # Bind do botão direito
        self.video_list.tree.bind("<Button-3>", self._show_context_menu)  # Windows/Linux
        self.video_list.tree.bind("<Button-2>", self._show_context_menu)  # macOS

    def _show_context_menu(self, event: tk.Event) -> None:
        """Exibe o menu de contexto na posição do clique."""
        # Seleciona o item clicado
        item = self.video_list.tree.identify_row(event.y)
        if not item:
            return
        
        self.video_list.tree.selection_set(item)
        
        # Limpa o menu anterior
        self.context_menu.delete(0, tk.END)
        
        # Obtém o item selecionado para verificar status
        selected_item = self.video_list.get_selected_item()
        if selected_item:
            original_data = selected_item.get("_original", {})
            status = original_data.get("status", "")
            video_url = original_data.get("video_url")
            
            # Adiciona opções base
            self.context_menu.add_command(label=HISTORY_MENU_OPEN_FOLDER, command=self._open_folder)
            
            # Adiciona "Tentar Novamente" apenas para itens que falharam e têm URL
            if status == "failed" and video_url and self.queue_manager:
                self.context_menu.add_separator()
                self.context_menu.add_command(label=HISTORY_MENU_RETRY, command=self._retry_download)
            
            self.context_menu.add_separator()
            self.context_menu.add_command(label=HISTORY_MENU_DELETE, command=self._delete_item)
        
        # Exibe o menu
        self.context_menu.post(event.x_root, event.y_root)

    def _open_folder(self) -> None:
        """Abre a pasta do arquivo selecionado."""
        item = self.video_list.get_selected_item()
        if not item:
            messagebox.showwarning("Aviso", "Nenhum item selecionado.")
            return
        
        original_data = item.get("_original", {})
        file_path = original_data.get("file_path")
        
        if not file_path:
            messagebox.showinfo("Informação", "Este item não possui arquivo associado.")
            return
        
        try:
            # Converte para Path e obtém o diretório
            path = Path(file_path)
            if path.exists():
                folder_path = path.parent
            else:
                # Se o arquivo não existe, tenta usar o caminho do diretório
                folder_path = Path(file_path).parent
                if not folder_path.exists():
                    messagebox.showerror("Erro", f"Pasta não encontrada:\n{folder_path}")
                    return
            
            # Abre a pasta no explorador de arquivos do sistema
            if os.name == "nt":  # Windows
                os.startfile(str(folder_path))
            elif os.name == "posix":  # macOS e Linux
                subprocess.run(["open" if os.uname().sysname == "Darwin" else "xdg-open", str(folder_path)])
            else:
                messagebox.showinfo("Informação", f"Pasta: {folder_path}")
        except Exception as e:
            log.error(f"Erro ao abrir pasta: {e}")
            messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{e}")

    def _retry_download(self) -> None:
        """Tenta novamente o download de um item que falhou."""
        if not self.queue_manager:
            messagebox.showerror("Erro", "Gerenciador de fila não disponível.")
            return
        
        item = self.video_list.get_selected_item()
        if not item:
            messagebox.showwarning("Aviso", "Nenhum item selecionado.")
            return
        
        original_data = item.get("_original", {})
        video_url = original_data.get("video_url")
        video_id = original_data.get("video_id")
        title = item.get("Título", "Desconhecido")
        status = original_data.get("status")
        
        if status != "failed":
            messagebox.showinfo("Informação", "Este item não falhou. Apenas itens com falha podem ser tentados novamente.")
            return
        
        if not video_url:
            messagebox.showerror("Erro", "Não foi possível obter a URL do vídeo para tentar novamente.")
            return
        
        # Tenta obter informações do vídeo do banco de dados
        video_info = None
        if video_id and self.video_dao:
            try:
                video_info = self.video_dao.get_by_id(video_id)
            except Exception as e:
                log.warning(f"Erro ao buscar informações do vídeo: {e}")
        
        # Determina o caminho de destino
        file_path = original_data.get("file_path")
        if file_path:
            download_path = str(Path(file_path).parent)
        else:
            download_path = Config.DEFAULT_DOWNLOAD_PATH
        
        # Tenta determinar o formato baseado na extensão do arquivo ou usa MP4 como padrão
        mode = "mp4"  # Padrão
        if file_path:
            ext = Path(file_path).suffix.lower()
            if ext == ".mp3":
                mode = "mp3"
            elif ext in [".mp4", ".m4a", ".webm"]:
                mode = "mp4"
        
        # Adiciona à fila
        try:
            item_id = self.queue_manager.add_item(
                url=video_url,
                title=title,
                path=download_path,
                mode=mode,
                video_id=video_id,
            )
            
            log.info(f"Download reenfileirado: {title} ({item_id[:8]})")
            messagebox.showinfo(
                "Download Reenfileirado",
                f"O download foi adicionado à fila novamente.\n\n"
                f"Título: {title}\n"
                f"Formato: {mode.upper()}\n"
                f"Destino: {download_path}"
            )
            
            # Atualiza a lista de histórico
            self.refresh()
        except Exception as e:
            log.error(f"Erro ao reenfileirar download: {e}")
            messagebox.showerror("Erro", f"Não foi possível reenfileirar o download:\n{e}")

    def _delete_item(self) -> None:
        """Deleta o item selecionado do histórico."""
        item = self.video_list.get_selected_item()
        if not item:
            messagebox.showwarning("Aviso", "Nenhum item selecionado.")
            return
        
        original_data = item.get("_original", {})
        history_id = original_data.get("id")
        title = item.get("Título", "item desconhecido")
        
        if not history_id:
            messagebox.showerror("Erro", "Não foi possível identificar o item para deletar.")
            return
        
        # Confirmação
        response = messagebox.askyesno(
            "Confirmar Exclusão",
            f"Deseja realmente deletar este item do histórico?\n\n"
            f"Título: {title}\n\n"
            f"Nota: O arquivo físico não será deletado, apenas o registro do histórico."
        )
        
        if not response:
            return
        
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(SQL_DELETE_HISTORY, (history_id,))
            self.db.connection.commit()
            
            log.info(f"Item {history_id} deletado do histórico")
            messagebox.showinfo("Sucesso", "Item deletado do histórico com sucesso.")
            
            # Atualiza a lista
            self.refresh()
        except Exception as e:
            log.error(f"Erro ao deletar item do histórico: {e}")
            messagebox.showerror("Erro", f"Não foi possível deletar o item:\n{e}")

    def _on_item_select(self, item: dict) -> None:
        """
        Handler chamado quando um item é selecionado.
        
        Args:
            item: Dicionário com os dados do item selecionado.
        """
        # Pode ser expandido para mostrar detalhes ou ações
        log.debug(f"Item selecionado: {item.get('Título')}")

    def refresh(self) -> None:
        """Atualiza a lista de histórico."""
        self.load_history()

