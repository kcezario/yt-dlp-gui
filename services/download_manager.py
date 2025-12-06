"""Gerenciador de downloads usando yt-dlp com suporte a threading e callbacks."""

import os
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Optional

import yt_dlp
from yt_dlp import YoutubeDL

from config import Config
from utils.logger import get_logger

log = get_logger(__name__)


class DownloadManager:
    """
    Gerenciador de downloads de vídeos usando yt-dlp.
    
    Suporta download em thread separada com callbacks de progresso
    e conclusão. Pode baixar vídeo (MP4) ou apenas áudio (MP3).
    """

    def __init__(self) -> None:
        """Inicializa o gerenciador de downloads."""
        self._active_downloads: Dict[str, threading.Thread] = {}
        self._ffmpeg_path = self._find_ffmpeg()

    def _find_ffmpeg(self) -> Optional[str]:
        """
        Tenta localizar o executável FFmpeg.
        
        Returns:
            Caminho para o FFmpeg ou None se não encontrado.
        """
        # Primeiro, verifica se está configurado no Config
        if Config.FFMPEG_PATH and os.path.exists(Config.FFMPEG_PATH):
            return Config.FFMPEG_PATH

        # Tenta encontrar no PATH
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            return ffmpeg_path

        log.warning("FFmpeg não encontrado. Downloads de áudio podem falhar.")
        return None

    def _get_ydl_opts(
        self,
        output_path: str,
        mode: str,
        on_progress: Optional[Callable[[float, str], None]] = None,
    ) -> Dict:
        """
        Gera as opções do yt-dlp baseado no modo de download.
        
        Args:
            output_path: Caminho onde o arquivo será salvo.
            mode: Modo de download ('mp3' ou 'mp4').
            on_progress: Callback de progresso (opcional).
            
        Returns:
            Dicionário com opções do yt-dlp.
        """
        # Garante que o diretório existe
        os.makedirs(output_path, exist_ok=True)

        # Template de nome do arquivo
        filename_template = os.path.join(output_path, "%(title)s.%(ext)s")

        # Opções base
        opts: Dict = {
            "outtmpl": filename_template,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [self._create_progress_hook(on_progress)] if on_progress else [],
            # Opções para contornar bloqueios do YouTube
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web"],  # Tenta diferentes clientes
                }
            },
            # Headers para parecer um navegador real
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            },
        }

        # Configurações específicas por modo
        if mode.lower() == "mp3":
            # Download apenas de áudio (MP3)
            opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            })
            if self._ffmpeg_path:
                opts["ffmpeg_location"] = self._ffmpeg_path
        else:
            # Download de vídeo (MP4)
            opts.update({
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "merge_output_format": "mp4",
            })
            if self._ffmpeg_path:
                opts["ffmpeg_location"] = self._ffmpeg_path

        return opts

    def _create_progress_hook(
        self, callback: Optional[Callable[[float, str], None]]
    ) -> Callable:
        """
        Cria um hook de progresso para o yt-dlp.
        
        Args:
            callback: Função callback que recebe (percent, message).
            
        Returns:
            Função hook compatível com yt-dlp.
        """
        def progress_hook(d: Dict) -> None:
            """Hook interno que processa informações de progresso do yt-dlp."""
            if callback is None:
                return

            status = d.get("status")
            if status == "downloading":
                # Calcula porcentagem
                total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                downloaded_bytes = d.get("downloaded_bytes", 0)
                
                if total_bytes > 0:
                    percent = (downloaded_bytes / total_bytes) * 100
                else:
                    percent = 0.0

                # Mensagem de status
                speed = d.get("speed", 0)
                if speed:
                    speed_str = f"{speed / 1024 / 1024:.2f} MB/s"
                else:
                    speed_str = "calculando..."

                msg = f"Baixando... {speed_str}"
                callback(percent, msg)
            elif status == "finished":
                callback(100.0, "Download concluído!")
            elif status == "error":
                callback(0.0, f"Erro: {d.get('error', 'Erro desconhecido')}")

        return progress_hook

    def start_download_thread(
        self,
        url: str,
        path: str,
        mode: str = "mp4",
        on_progress: Optional[Callable[[float, str], None]] = None,
        on_complete: Optional[Callable[[bool, str], None]] = None,
    ) -> None:
        """
        Inicia um download em uma thread separada.
        
        Args:
            url: URL do vídeo/playlist a ser baixado.
            path: Caminho onde o arquivo será salvo.
            mode: Modo de download ('mp3' ou 'mp4', padrão: 'mp4').
            on_progress: Callback chamado durante o progresso (percent, message).
            on_complete: Callback chamado ao finalizar (success, message).
        """
        if url in self._active_downloads:
            log.warning(f"Download para {url} já está em andamento")
            if on_complete:
                on_complete(False, "Download já está em andamento")
            return

        def download_worker() -> None:
            """Worker thread que executa o download."""
            success = False
            message = ""
            file_path = ""

            try:
                log.info(f"Iniciando download: {url} (modo: {mode})")
                
                opts = self._get_ydl_opts(path, mode, on_progress)
                
                with YoutubeDL(opts) as ydl:
                    # Extrai informações do vídeo
                    info = ydl.extract_info(url, download=False)
                    video_id = info.get("id", "")
                    title = info.get("title", "Desconhecido")
                    
                    # Inicia o download
                    ydl.download([url])
                    
                    # Tenta encontrar o arquivo baixado
                    # yt-dlp pode ter modificado o nome do arquivo
                    downloaded_files = list(Path(path).glob(f"*{title}*"))
                    if downloaded_files:
                        file_path = str(downloaded_files[0])
                    else:
                        # Fallback: busca por extensão
                        if mode.lower() == "mp3":
                            files = list(Path(path).glob("*.mp3"))
                        else:
                            files = list(Path(path).glob("*.mp4"))
                        if files:
                            # Pega o mais recente
                            file_path = str(max(files, key=os.path.getctime))

                success = True
                message = f"Download concluído: {title}"
                log.info(f"Download concluído com sucesso: {url}")

            except Exception as e:
                success = False
                error_str = str(e)
                
                # Mensagens mais amigáveis para erros comuns
                if "403" in error_str or "Forbidden" in error_str:
                    message = (
                        "Erro: YouTube bloqueou o download (403 Forbidden).\n\n"
                        "Possíveis soluções:\n"
                        "• Atualize o yt-dlp: pip install --upgrade yt-dlp\n"
                        "• Tente novamente em alguns minutos\n"
                        "• Alguns vídeos podem ter restrições de download"
                    )
                elif "Video unavailable" in error_str or "unavailable" in error_str:
                    message = "Erro: Vídeo não disponível ou foi removido."
                elif "Private video" in error_str:
                    message = "Erro: Este vídeo é privado e não pode ser baixado."
                elif "Sign in to confirm your age" in error_str:
                    message = "Erro: Vídeo com restrição de idade. Não é possível baixar."
                elif "FFmpeg" in error_str or "ffmpeg" in error_str:
                    message = (
                        "Erro: FFmpeg não encontrado ou não configurado corretamente.\n\n"
                        "Para downloads de áudio (MP3), o FFmpeg é necessário.\n"
                        "Baixe em: https://ffmpeg.org/download.html"
                    )
                else:
                    message = f"Erro no download: {error_str}"
                
                log.error(f"Erro ao baixar {url}: {e}", exc_info=True)
            finally:
                # Remove da lista de downloads ativos
                if url in self._active_downloads:
                    del self._active_downloads[url]
                
                # Chama callback de conclusão
                if on_complete:
                    on_complete(success, message)

        # Cria e inicia a thread
        thread = threading.Thread(target=download_worker, daemon=True)
        thread.start()
        self._active_downloads[url] = thread
        log.debug(f"Thread de download iniciada para {url}")

    def is_downloading(self, url: str) -> bool:
        """
        Verifica se há um download ativo para a URL especificada.
        
        Args:
            url: URL a verificar.
            
        Returns:
            True se há download ativo, False caso contrário.
        """
        return url in self._active_downloads

