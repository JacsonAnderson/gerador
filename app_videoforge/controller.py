import sqlite3
import json
import time
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound



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

def carregar_configs_video(canal, video_id):
    with sqlite3.connect(VIDEOS_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT configs FROM videos WHERE canal = ? AND video_id = ?", (canal, video_id))
        resultado = cursor.fetchone()
        if resultado:
            try:
                return json.loads(resultado[0])
            except json.JSONDecodeError:
                log_callback("⚠ Erro ao ler as configurações JSON do vídeo.")
                return {}
        return {}
    
def verificar_ou_baixar_transcricao(canal, video_id):
    metadados_path = Path(f"data/{canal}/{video_id}/control/metadados.json")

    if not metadados_path.exists():
        log_callback("  ⚠ Arquivo metadados.json não encontrado.")
        return

    try:
        with open(metadados_path, "r", encoding="utf-8") as f:
            metadados = json.load(f)
    except json.JSONDecodeError:
        log_callback("  ⚠ Erro ao ler metadados.json.")
        return

    if "transcricao_original" in metadados:
        log_callback("  ⏩ Transcrição já existente. Pulando etapa.")
        return

    link = metadados.get("link")
    if not link:
        log_callback("  ❌ Link do vídeo não encontrado em metadados.json.")
        return

    video_id_youtube = extrair_video_id(link)
    if not video_id_youtube:
        log_callback("  ❌ Não foi possível extrair o ID do vídeo.")
        return

    log_callback("  📥 Baixando transcrição do YouTube...")
    try:
        transcript_raw = YouTubeTranscriptApi.get_transcript(
            video_id_youtube,
            languages=[
                "pt", "pt-BR", "en", "es", "es-419",  # português, inglês, espanhol latino
                "fr", "it", "de", "hi", "id",         # francês, italiano, alemão, hindi, indonésio
            ]
        )
        transcript_text = " ".join(segment["text"] for segment in transcript_raw)
        metadados["transcricao_original"] = transcript_text

        with open(metadados_path, "w", encoding="utf-8") as f:
            json.dump(metadados, f, ensure_ascii=False, indent=2)
        log_callback("  ✅ Transcrição salva com sucesso.")
    except (TranscriptsDisabled, NoTranscriptFound):
        log_callback("  ⚠ Transcrição não disponível para este vídeo.")

def extrair_video_id(link):
    import re
    # Suporta links como: https://www.youtube.com/watch?v=ABC123XYZ
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", link)
    return match.group(1) if match else None

def processar_video(canal, video_id):
    log_callback(f"\n📌 Processando Vídeo {video_id} do Canal {canal}...")

    configs = carregar_configs_video(canal, video_id)

    if not configs.get("gerar_roteiro", False):
        log_callback("  ⏭ Ignorado: gerar_roteiro está desativado para este vídeo.")
        return

    if configs.get("roteiro_ok", 0) == 1:
        log_callback("  ⏭ Ignorado: roteiro já finalizado (roteiro_ok = 1).")
        return
    time.sleep(3)
    log_callback("  ✅ Verificando roteiro...")

    verificar_ou_baixar_transcricao(canal, video_id)


    # Aqui entraria o módulo real de geração de roteiro

    log_callback("  ✅ Gerando áudio...")
    log_callback("  ✅ Editando vídeo...")
    log_callback("  ✅ Criando legenda...")
    log_callback("  ✅ Gerando thumb...")
    log_callback("  ✅ Finalizando metadados...")
    log_callback("  🏁 Pronto! Vídeo concluído.")
