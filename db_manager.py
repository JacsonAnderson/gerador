# db_manager.py

import sqlite3
from pathlib import Path

# Define os caminhos para os bancos de dados
VIDEOS_DB_PATH = Path("data/videos.db")
CHANNELS_DB_PATH = Path("data/channels.db")

def inicializar_bancos_de_dados():
    """
    Verifica e cria o diretório 'data' e os bancos de dados com suas tabelas,
    se não existirem. Esta é a única função que precisa ser chamada no início do app.
    """
    try:
        # Garante que o diretório 'data' exista
        CHANNELS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        # --- 1. Banco de Dados de Canais ---
        # Conecta e cria a tabela 'canais' se ela não existir
        with sqlite3.connect(CHANNELS_DB_PATH) as conn_channels:
            cursor = conn_channels.cursor()
            # SQL copiado exatamente do seu modal_criar_canal.py
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS canais (
                    id TEXT PRIMARY KEY,
                    nome TEXT NOT NULL UNIQUE,
                    idioma TEXT,
                    marca_dagua TEXT,
                    ativo INTEGER DEFAULT 1,
                    caminho_videos TEXT,
                    roteiros_gerados INTEGER DEFAULT 0,
                    data_criacao TEXT,
                    configs TEXT
                )
            """)
            conn_channels.commit()

        # --- 2. Banco de Dados de Vídeos ---
        # Conecta e cria a tabela 'videos' se ela não existir
        with sqlite3.connect(VIDEOS_DB_PATH) as conn_videos:
            cursor = conn_videos.cursor()
            # SQL copiado exatamente do seu modal_adicionar_videos.py
            # Adicionei a coluna 'configs' que estava faltando no seu CREATE TABLE, mas existia no INSERT
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    canal TEXT NOT NULL,
                    video_id TEXT NOT NULL,
                    link TEXT,
                    roteiro_ok INTEGER DEFAULT 0,
                    audio_ok INTEGER DEFAULT 0,
                    legenda_ok INTEGER DEFAULT 0,
                    metadado_ok INTEGER DEFAULT 0,
                    thumb_ok INTEGER DEFAULT 0,
                    estado INTEGER DEFAULT 0,
                    roteiro_data TEXT,
                    audio_data TEXT,
                    legenda_data TEXT,
                    metadado_data TEXT,
                    thumb_data TEXT,
                    criado_em TEXT,
                    configs TEXT,
                    UNIQUE(canal, video_id)
                )
            """)
            conn_videos.commit()
        
        # Se chegou até aqui, tudo ocorreu bem.
        print("[DB Manager] Bancos de dados inicializados com sucesso.")

    except sqlite3.Error as e:
        print(f"[DB Manager] ❌ Erro ao inicializar os bancos de dados: {e}")
        # Em um app real, você poderia mostrar um messagebox de erro aqui e fechar o app.
        raise e # Levanta o erro para parar a execução se o DB não puder ser criado.

