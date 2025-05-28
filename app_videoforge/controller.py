import sqlite3
from pathlib import Path

VIDEOS_DB_PATH = Path("data/videos.db")
CHANNELS_DB_PATH = Path("data/channels.db")

log_callback = print  # Padrão


def set_logger(callback):
    global log_callback
    log_callback = callback


def iniciar_fluxo_videoforge(modo, canal=None, video_id=None):
    if modo == "video":
        if canal and video_id:
            log_callback(f"\n🚀 Iniciando fluxo para VÍDEO: Canal '{canal}', Vídeo ID '{video_id}'")
            processar_video(canal, video_id)
        else:
            log_callback("❌ Canal ou vídeo não especificado para modo vídeo.")

    elif modo == "canal":
        if canal:
            log_callback(f"\n🚀 Iniciando fluxo para CANAL: {canal}")
            videos = listar_videos_validos(canal)
            if not videos:
                log_callback("⚠ Nenhum vídeo válido encontrado (todos já postados).")
                return
            log_callback(f"🔍 Vídeos encontrados: {videos}")
            for video_id in videos:
                processar_video(canal, video_id)
        else:
            log_callback("❌ Canal não especificado para modo canal.")

    elif modo == "todos":
        log_callback("\n🚀 Iniciando fluxo para TODOS OS CANAIS")
        canais = listar_canais()
        for canal_nome in canais:
            log_callback(f"🎯 Vamos trabalhar com o canal: {canal_nome}")
            videos = listar_videos_validos(canal_nome)
            if not videos:
                log_callback("  ⚠ Nenhum vídeo válido neste canal.")
                continue
            log_callback(f"   └─ Vídeos válidos encontrados: {', '.join(videos)}\n")
            for video_id in videos:
                log_callback(f"🔽 Iniciando vídeo {video_id} do canal {canal_nome}")
                processar_video(canal_nome, video_id)

    else:
        log_callback("❌ Modo inválido. Use: 'video', 'canal' ou 'todos'.")


def listar_canais():
    with sqlite3.connect(CHANNELS_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nome FROM canais")
        return [row[0] for row in cursor.fetchall()]


def listar_videos_validos(canal):
    with sqlite3.connect(VIDEOS_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT video_id FROM videos WHERE canal = ? AND estado != 7", (canal,))
        return [row[0] for row in cursor.fetchall()]


def processar_video(canal, video_id):
    log_callback(f"\n📌 Processando Vídeo {video_id} do Canal {canal}...")

    # Aqui você pode implementar os módulos específicos
    log_callback("  ✅ Verificando roteiro...")
    log_callback("  ✅ Gerando áudio...")
    log_callback("  ✅ Editando vídeo...")
    log_callback("  ✅ Criando legenda...")
    log_callback("  ✅ Gerando thumb...")
    log_callback("  ✅ Finalizando metadados...")
    log_callback("  🏁 Pronto! Vídeo concluído.")
