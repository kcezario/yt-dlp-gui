"""Aba de histórico de downloads."""

import os
import subprocess
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Callable, Optional

from database.connection import DBConnection
from database.dao import HistoryDAO
from config import Config
from ui.components.video_list import VideoList
from utils.logger import get_logger

log = get_logger(__name__)


class HistoryTab:
    """
    Aba de histórico que exibe os downloads realizados.
    
    Mostra uma tabela com informações dos downloads, incluindo
    título do vídeo, status, data, etc.
    """

    def __init__(self, parent: ttk.Notebook, db: DBConnection) -> None:
        """
        Inicializa a aba de histórico.
        
        Args:
            parent: Widget pai (Notebook) onde a aba será adicionada.
            db: Instância da conexão com o banco de dados.
        """
        self.frame = ttk.Frame(parent)
        self.db = db
        self.history_dao = HistoryDAO(db)
        
        self._setup_ui()
        self.load_history()

    def _setup_ui(self) -> None:
        """Configura a interface gráfica da aba."""
        # Container principal
        main_container = ttk.Frame(self.frame, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)

        # Título e botão de atualizar
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        title_label = ttk.Label(
            header_frame,
            text="Histórico de Downloads",
            font=("", 14, "bold")
        )
        title_label.pack(side=tk.LEFT)

        refresh_button = ttk.Button(
            header_frame,
            text="Atualizar",
            command=self.load_history
        )
        refresh_button.pack(side=tk.RIGHT)

        # Lista de vídeos
        columns = ["Título", "Status", "Data", "Caminho"]
        column_widths = {
            "Título": 300,
            "Status": 100,
            "Data": 150,
            "Caminho": 200,
        }

        self.video_list = VideoList(
            main_container,
            columns=columns,
            column_widths=column_widths,
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

    def load_history(self, limit: int = 50) -> None:
        """
        Carrega o histórico de downloads do banco de dados.
        
        Args:
            limit: Número máximo de registros a carregar.
        """
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
        self.context_menu.add_command(label="Abrir Pasta", command=self._open_folder)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Deletar", command=self._delete_item)
        
        # Bind do botão direito
        self.video_list.tree.bind("<Button-3>", self._show_context_menu)  # Windows/Linux
        self.video_list.tree.bind("<Button-2>", self._show_context_menu)  # macOS

    def _show_context_menu(self, event: tk.Event) -> None:
        """Exibe o menu de contexto na posição do clique."""
        # Seleciona o item clicado
        item = self.video_list.tree.identify_row(event.y)
        if item:
            self.video_list.tree.selection_set(item)
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
            cursor.execute("DELETE FROM history WHERE id = ?", (history_id,))
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

