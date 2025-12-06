"""Script de validação da Etapa 2: Motor de Download (Service/Controller)."""

import time
from services.download_manager import DownloadManager


def progress_handler(percent: float, msg: str) -> None:
    """Handler de progresso do download."""
    print(f"PROGRESSO: {percent:.1f}% - {msg}")


def complete_handler(success: bool, msg: str) -> None:
    """Handler de conclusão do download."""
    status = "SUCESSO" if success else "FALHA"
    print(f"FINALIZADO: {status} - {msg}")


if __name__ == "__main__":
    print("=" * 60)
    print("Teste do DownloadManager")
    print("=" * 60)
    print()
    
    manager = DownloadManager()
    
    # Nota: O YouTube pode bloquear downloads, mas o importante é que
    # os callbacks de progresso e conclusão estão funcionando.
    # Você pode testar com qualquer URL válida do YouTube.
    test_url = input("Digite a URL do vídeo do YouTube (ou Enter para usar URL padrão): ").strip()
    if not test_url:
        # URL de exemplo - pode não funcionar devido a restrições do YouTube
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        print(f"Usando URL padrão: {test_url}")
    
    print()
    print("Iniciando download em thread separada...")
    print("(A thread principal continua responsiva)")
    print()
    
    manager.start_download_thread(
        url=test_url,
        path="./downloads",
        mode="mp4",
        on_progress=progress_handler,
        on_complete=complete_handler
    )
    
    # Manter main thread viva e demonstrar que não está bloqueada
    print("Thread principal aguardando (não bloqueada)...")
    for i in range(15):
        time.sleep(1)
        if i % 3 == 0:
            print(f"  [Thread principal ativa - {i}s]")
    
    print()
    print("=" * 60)
    print("Teste concluído! Verifique se os callbacks foram chamados acima.")
    print("=" * 60)

