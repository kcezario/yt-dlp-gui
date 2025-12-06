# YT-Downloader Pro

Aplicação desktop para download de vídeos e áudios do YouTube com interface gráfica moderna, desenvolvida em Python usando Tkinter.

## 📋 Sobre o Projeto

O **YT-Downloader Pro** é uma aplicação desktop completa que permite baixar vídeos e áudios do YouTube de forma simples e intuitiva. A aplicação oferece suporte para downloads individuais, playlists e canais inteiros, com gerenciamento de fila, histórico de downloads e configurações personalizáveis.

### Principais Funcionalidades

- ✅ Download de vídeos únicos, playlists e canais
- ✅ Suporte para formatos MP4 (vídeo) e MP3 (áudio)
- ✅ Gerenciamento de fila de downloads com controle de pausa/retomada
- ✅ Histórico completo de downloads com informações detalhadas
- ✅ Interface gráfica moderna e responsiva
- ✅ Validação de URLs do YouTube
- ✅ Configurações personalizáveis (caminhos de download, FFmpeg)
- ✅ Banco de dados SQLite para persistência de dados
- ✅ Sistema de logs completo

## 🏗️ Arquitetura

O projeto segue rigorosamente o padrão **MVC (Model-View-Controller)**:

```
/
├── main.py                   # Ponto de entrada (Bootstrap da GUI e DB)
├── config.py                 # Configurações globais e constantes
├── requirements.txt          # Lista de dependências
├── database/                 # MODELO DE DADOS
│   ├── __init__.py
│   ├── connection.py         # Singleton de conexão SQLite
│   ├── schema.sql            # Script DDL (Tabelas: videos, playlists, history)
│   ├── constants.py          # Constantes SQL
│   └── dao.py                # Data Access Objects (CRUD)
├── services/                 # LÓGICA DE NEGÓCIO (CONTROLLER BACKEND)
│   ├── __init__.py
│   ├── download_manager.py   # Wrapper do yt_dlp + Gerenciamento de Threads
│   ├── queue_manager.py      # Gerenciamento de fila de downloads
│   ├── validation.py         # Validadores de URL
│   └── constants.py          # Constantes de serviços
└── ui/                       # INTERFACE GRÁFICA (VIEW)
    ├── __init__.py
    ├── root.py               # Janela Principal (MainWindow)
    ├── constants.py          # Constantes de UI
    ├── components/           # Widgets reutilizáveis
    │   └── video_list.py     # Treeview com scrollbars
    └── tabs/                 # Abas do Notebook
        ├── download_tab.py   # Input e ações de download
        ├── history_tab.py    # Visualização do Banco
        ├── queue_tab.py      # Gerenciamento de fila
        └── settings_tab.py   # Configurações
```

### Camadas da Arquitetura

- **Model (database/)**: Responsável pela persistência de dados usando SQLite. Contém DAOs para operações CRUD e um singleton de conexão.
- **View (ui/)**: Interface gráfica construída com Tkinter/TTK, seguindo o tema nativo do sistema operacional.
- **Controller (services/)**: Lógica de negócio isolada da interface, incluindo gerenciamento de downloads, validações e processamento de filas.

### Padrões de Design Utilizados

- **Singleton**: `DBConnection` para garantir uma única instância de conexão com o banco.
- **DAO (Data Access Object)**: Abstração de acesso a dados (`VideoDAO`, `PlaylistDAO`, `HistoryDAO`).
- **Observer Pattern**: Sistema de callbacks para atualização da UI durante downloads.
- **Threading**: Downloads executados em threads separadas para não bloquear a GUI.

## 📦 Pré-requisitos

### Python

- **Python 3.12 ou superior** é obrigatório.

Para verificar sua versão:
```bash
python --version
```

### FFmpeg

O FFmpeg é necessário apenas para downloads de áudio (MP3). Para downloads de vídeo (MP4), não é obrigatório.

#### Windows

1. Baixe o FFmpeg de [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Extraia o arquivo ZIP
3. Adicione o caminho do executável `ffmpeg.exe` nas configurações da aplicação, ou adicione o diretório ao PATH do sistema

#### Linux

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# Fedora
sudo dnf install ffmpeg

# Arch Linux
sudo pacman -S ffmpeg
```

#### macOS

```bash
# Usando Homebrew
brew install ffmpeg
```

## 🚀 Instalação

### 1. Clone o Repositório

```bash
git clone <url-do-repositorio>
cd yt-dlp-gui
```

### 2. Crie um Ambiente Virtual

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instale as Dependências

```bash
pip install -r requirements.txt
```

### 4. Configure Variáveis de Ambiente (Opcional)

Copie o arquivo `env.example` para `.env` e ajuste as configurações:

```bash
# Windows
copy env.example .env

# Linux/macOS
cp env.example .env
```

Edite o arquivo `.env` com suas preferências:
```env
DB_PATH=data/yt_downloader.db
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
LOG_CONSOLE=true
FFMPEG_PATH=C:\caminho\para\ffmpeg.exe
```

## 💻 Uso

### Executar a Aplicação

```bash
python main.py
```

### Como Usar

1. **Aba Download:**
   - Selecione o tipo de download (Vídeo Único, Playlist ou Canal)
   - Cole a URL do YouTube
   - Escolha o formato (MP4 ou MP3)
   - Selecione a pasta de destino (ou use a padrão)
   - Clique em "Baixar"

2. **Aba Fila de Downloads:**
   - Visualize todos os downloads em fila
   - Use "Pausar" para pausar a fila
   - Use "Retomar" para continuar
   - Use "Limpar Concluídos" para remover itens finalizados
   - Clique duas vezes em um item com falha para tentar novamente

3. **Aba Histórico:**
   - Visualize todos os downloads realizados
   - Clique com o botão direito em um item para:
     - Abrir a pasta do arquivo
     - Deletar o registro do histórico
   - Use "Atualizar" para recarregar a lista

4. **Aba Configurações:**
   - Configure a pasta padrão de downloads
   - Configure o caminho do FFmpeg (opcional)
   - Use "Aplicar Configurações" para salvar
   - Use "Restaurar Padrões" para reverter

### Estrutura de Diretórios Criados

A aplicação cria automaticamente os seguintes diretórios:

- `data/` - Banco de dados SQLite
- `logs/` - Arquivos de log da aplicação
- `downloads/` - Pasta padrão de downloads (ou a configurada)

## 🧪 Testes

O projeto inclui uma estrutura básica de testes em `tests/`. Para executar testes futuros:

```bash
# Com pytest (quando implementado)
pytest tests/
```

## 📝 Logs

Os logs são salvos em `logs/app.log` e também exibidos no console (se `LOG_CONSOLE=true`). Os níveis de log são:

- **DEBUG**: Mensagens detalhadas para desenvolvimento
- **INFO**: Eventos importantes do fluxo normal
- **WARNING**: Situações inesperadas não fatais
- **ERROR**: Falhas em operações tratadas
- **CRITICAL**: Falhas irreversíveis

## 🔧 Configuração Avançada

### Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `DB_PATH` | Caminho do banco de dados SQLite | `data/yt_downloader.db` |
| `LOG_LEVEL` | Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL) | `INFO` |
| `LOG_FILE` | Caminho do arquivo de log | `logs/app.log` |
| `LOG_CONSOLE` | Exibir logs no console (true/false) | `true` |
| `FFMPEG_PATH` | Caminho do executável FFmpeg | `None` (auto-detect) |

### Banco de Dados

O banco de dados SQLite é criado automaticamente na primeira execução. O schema está definido em `database/schema.sql` e inclui as seguintes tabelas:

- `videos` - Informações dos vídeos baixados
- `playlists` - Informações das playlists
- `playlist_videos` - Relacionamento entre playlists e vídeos
- `history` - Histórico de downloads
- `settings` - Configurações da aplicação (futuro)

## 🐛 Solução de Problemas

### Erro: "FFmpeg não encontrado"

- **Solução**: Configure o caminho do FFmpeg na aba Configurações, ou instale o FFmpeg e adicione ao PATH do sistema.

### Erro: "Video unavailable" ou "HTTP Error 403"

- **Causa**: Restrições do YouTube ou vídeo indisponível.
- **Solução**: A aplicação tenta contornar bloqueios automaticamente. Se persistir, o vídeo pode estar restrito ou indisponível.

### Erro: "Database locked"

- **Causa**: Múltiplas instâncias da aplicação tentando acessar o banco simultaneamente.
- **Solução**: Feche outras instâncias da aplicação.

## 📄 Licença

Este projeto é fornecido "como está", sem garantias. Use por sua conta e risco.

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.

## 📚 Tecnologias Utilizadas

- **Python 3.12+** - Linguagem de programação
- **Tkinter/TTK** - Interface gráfica (biblioteca padrão)
- **yt-dlp** - Engine de download do YouTube
- **SQLite3** - Banco de dados (biblioteca padrão)
- **Threading** - Concorrência (biblioteca padrão)

## 👨‍💻 Desenvolvimento

### Padrões de Código

- **Tipagem Estrita**: Type Hints em todas as assinaturas
- **Docstrings**: Google Style em português
- **Idioma**: Código em inglês, documentação em português
- **Arquitetura**: MVC rigoroso
- **Constantes**: Sem "magic strings", tudo centralizado em arquivos `constants.py`

### Estrutura de Commits

Siga o padrão "Conventional Commits" em português:

```
feat(db): cria tabelas de playlist e video
fix(gui): corrige travamento da barra de progresso
refactor(core): otimiza classe download_manager
docs(readme): adiciona instruções de instalação
```

## 📸 Screenshots

Screenshots da aplicação podem ser encontrados em `assets/screenshots/` (quando disponíveis).

---

**Desenvolvido com ❤️ usando Python e Tkinter**

