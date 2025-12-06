"""Componente de lista de vídeos com Treeview e scrollbar."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, List, Optional

from utils.logger import get_logger

log = get_logger(__name__)


class VideoList:
    """
    Componente reutilizável de lista de vídeos usando Treeview.
    
    Fornece uma tabela com scrollbar para exibir dados de vídeos
    ou histórico de downloads.
    """

    def __init__(
        self,
        parent: ttk.Widget,
        columns: List[str],
        column_widths: Optional[Dict[str, int]] = None,
        on_select: Optional[Callable[[Dict], None]] = None,
    ) -> None:
        """
        Inicializa o componente de lista de vídeos.
        
        Args:
            parent: Widget pai onde o componente será criado.
            columns: Lista de nomes das colunas.
            column_widths: Dicionário opcional com larguras das colunas.
            on_select: Callback chamado quando um item é selecionado.
        """
        self.parent = parent
        self.columns = columns
        self.column_widths = column_widths or {}
        self.on_select = on_select
        self.data: List[Dict] = []

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Configura a interface do componente."""
        # Frame principal
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview
        self.tree = ttk.Treeview(main_frame, columns=self.columns, show="headings", selectmode="browse")
        
        # Configura colunas
        for col in self.columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            width = self.column_widths.get(col, 150)
            self.tree.column(col, width=width, anchor=tk.W)

        # Scrollbar vertical
        v_scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scrollbar.set)

        # Scrollbar horizontal
        h_scrollbar = ttk.Scrollbar(main_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(xscrollcommand=h_scrollbar.set)

        # Layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Bind de seleção
        if self.on_select:
            self.tree.bind("<<TreeviewSelect>>", self._on_item_select)

    def _on_item_select(self, event: tk.Event) -> None:
        """Handler para seleção de item."""
        selection = self.tree.selection()
        if selection and self.on_select:
            item_id = selection[0]
            item_data = self.tree.item(item_id)
            # Busca dados originais pelo índice
            values = item_data["values"]
            if values:
                # Tenta encontrar o item correspondente nos dados
                for data_item in self.data:
                    # Compara pelo primeiro valor (geralmente ID ou título)
                    if str(data_item.get(self.columns[0], "")) == str(values[0]):
                        self.on_select(data_item)
                        break

    def add_item(self, data: Dict) -> str:
        """
        Adiciona um item à lista.
        
        Args:
            data: Dicionário com os dados do item. As chaves devem corresponder
                  aos nomes das colunas.
                  
        Returns:
            ID do item inserido no Treeview.
        """
        values = [str(data.get(col, "")) for col in self.columns]
        item_id = self.tree.insert("", tk.END, values=values)
        self.data.append(data)
        return item_id

    def clear(self) -> None:
        """Remove todos os itens da lista."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.data.clear()

    def load_data(self, data_list: List[Dict]) -> None:
        """
        Carrega uma lista de dados na tabela.
        
        Args:
            data_list: Lista de dicionários com os dados a serem exibidos.
        """
        self.clear()
        for data in data_list:
            self.add_item(data)
        log.debug(f"Carregados {len(data_list)} itens na lista")

    def refresh(self) -> None:
        """Recarrega os dados atuais (útil para atualizações)."""
        current_data = self.data.copy()
        self.load_data(current_data)

    def get_selected_item(self) -> Optional[Dict]:
        """
        Retorna o item atualmente selecionado.
        
        Returns:
            Dicionário com os dados do item selecionado ou None.
        """
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            item_data = self.tree.item(item_id)
            values = item_data["values"]
            if values:
                for data_item in self.data:
                    if str(data_item.get(self.columns[0], "")) == str(values[0]):
                        return data_item
        return None

