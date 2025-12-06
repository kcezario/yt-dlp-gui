"""Janela principal da aplicação."""

import tkinter as tk
from tkinter import ttk
from typing import Optional

from config import Config
from ui.constants import (
    THEME_DEFAULT,
    WINDOW_MIN_SIZE,
    WINDOW_PADDING,
    WINDOW_SIZE,
    WINDOW_TITLE,
)
from utils.logger import get_logger

log = get_logger(__name__)


class MainWindow:
    """
    Janela principal da aplicação.
    
    Gerencia a interface gráfica principal com abas (Notebook)
    e configura o tema nativo do sistema operacional.
    """

    def __init__(self) -> None:
        """Inicializa a janela principal."""
        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.minsize(WINDOW_MIN_SIZE[0], WINDOW_MIN_SIZE[1])

        # Configura tema nativo
        style = ttk.Style()
        style.theme_use(THEME_DEFAULT)

        # Cria notebook para abas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=WINDOW_PADDING, pady=WINDOW_PADDING)

        # Dicionário para armazenar referências às abas
        self.tabs: dict[str, ttk.Frame] = {}

        log.info("Janela principal inicializada")

    def add_tab(self, name: str, frame: ttk.Frame) -> None:
        """
        Adiciona uma aba ao notebook.
        
        Args:
            name: Nome da aba.
            frame: Frame que será exibido na aba.
        """
        self.notebook.add(frame, text=name)
        self.tabs[name] = frame
        log.debug(f"Aba '{name}' adicionada")

    def select_tab(self, name: str) -> None:
        """
        Seleciona uma aba pelo nome.
        
        Args:
            name: Nome da aba a ser selecionada.
        """
        if name in self.tabs:
            frame = self.tabs[name]
            # Encontra o índice da aba
            for i in range(self.notebook.index("end")):
                if self.notebook.tab(i, "text") == name:
                    self.notebook.select(i)
                    log.debug(f"Aba '{name}' selecionada")
                    break

    def run(self) -> None:
        """Inicia o loop principal da aplicação."""
        log.info("Iniciando loop principal da aplicação")
        self.root.mainloop()

    def get_root(self) -> tk.Tk:
        """
        Retorna a instância da janela raiz.
        
        Returns:
            Instância do Tk root.
        """
        return self.root

