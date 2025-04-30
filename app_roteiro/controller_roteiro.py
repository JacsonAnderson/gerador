import os
import json

from app_roteiro.transcritor import gerar_transcricao
from app_roteiro.gerador_resumo import gerar_resumo
from app_roteiro.gerador_topicos import gerar_topicos
from app_roteiro.gerador_introducao import gerar_introducao
from app_roteiro.gerador_conteudos import gerar_conteudos_topicos  # ✅ NOVO

DATA_DIR = "data"
log_callback = print

def set_logger(callback):
    global log_callback
    log_callback = callback

def listar_videos_para_transcricao():
    tarefas = {}
    for canal in os.listdir(DATA_DIR):
        canal_path = os.path.join(DATA_DIR, canal)
        if not os.path.isdir(canal_path):
            continue
        videos = []
        for item in os.listdir(canal_path):
            video_path = os.path.join(canal_path, item)
            if os.path.isdir(video_path) and item.isdigit():
                transcript_json = os.path.join(video_path, "control", "transcript_original.json")
                if not os.path.exists(transcript_json):
                    videos.append(item)
        if videos:
            tarefas[canal] = sorted(videos)
    return tarefas

def listar_videos_para_resumo():
    tarefas = {}
    for canal in os.listdir(DATA_DIR):
        canal_path = os.path.join(DATA_DIR, canal)
        if not os.path.isdir(canal_path):
            continue
        videos = []
        for item in os.listdir(canal_path):
            video_path = os.path.join(canal_path, item)
            if os.path.isdir(video_path) and item.isdigit():
                transcript_json = os.path.join(video_path, "control", "transcript_original.json")
                resumo_json = os.path.join(video_path, "control", "resumo.json")
                if os.path.exists(transcript_json) and not os.path.exists(resumo_json):
                    videos.append(item)
        if videos:
            tarefas[canal] = sorted(videos)
    return tarefas

def listar_videos_para_topicos():
    tarefas = {}
    for canal in os.listdir(DATA_DIR):
        canal_path = os.path.join(DATA_DIR, canal)
        if not os.path.isdir(canal_path):
            continue
        videos = []
        for item in os.listdir(canal_path):
            video_path = os.path.join(canal_path, item)
            if os.path.isdir(video_path) and item.isdigit():
                control_path = os.path.join(video_path, "control")
                transcript_json = os.path.join(control_path, "transcript_original.json")
                resumo_json = os.path.join(control_path, "resumo.json")
                topicos_json = os.path.join(control_path, "topicos.json")
                if os.path.exists(transcript_json) and os.path.exists(resumo_json) and not os.path.exists(topicos_json):
                    videos.append(item)
        if videos:
            tarefas[canal] = sorted(videos)
    return tarefas

def listar_videos_para_introducao():
    tarefas = {}
    for canal in os.listdir(DATA_DIR):
        canal_path = os.path.join(DATA_DIR, canal)
        if not os.path.isdir(canal_path):
            continue
        videos = []
        for item in os.listdir(canal_path):
            video_path = os.path.join(canal_path, item)
            if os.path.isdir(video_path) and item.isdigit():
                control_path = os.path.join(video_path, "control")
                topicos_json = os.path.join(control_path, "topicos.json")
                introducao_txt = os.path.join(control_path, "introducao.txt")
                if os.path.exists(topicos_json) and not os.path.exists(introducao_txt):
                    videos.append(item)
        if videos:
            tarefas[canal] = sorted(videos)
    return tarefas

def listar_videos_para_conteudos():
    tarefas = {}
    for canal in os.listdir(DATA_DIR):
        canal_path = os.path.join(DATA_DIR, canal)
        if not os.path.isdir(canal_path):
            continue
        videos = []
        for item in os.listdir(canal_path):
            video_path = os.path.join(canal_path, item)
            if os.path.isdir(video_path) and item.isdigit():
                control_path = os.path.join(video_path, "control")
                introducao_txt = os.path.join(control_path, "introducao.txt")
                topicos_json = os.path.join(control_path, "topicos.json")
                roteiros_json = os.path.join(control_path, "roteiros.json")
                if os.path.exists(introducao_txt) and os.path.exists(topicos_json) and not os.path.exists(roteiros_json):
                    videos.append(item)
        if videos:
            tarefas[canal] = sorted(videos)
    return tarefas

def processar_roteiros():
    # Fase 1 - Transcrição
    transcrever = listar_videos_para_transcricao()
    if transcrever:
        log_callback("📄 Etapa 1: Transcrições pendentes encontradas.")
        exibir_tarefas(transcrever)
        for canal, videos in transcrever.items():
            for video_id in videos:
                log_callback(f"\n🎙️ Transcrevendo {canal}/{video_id}...")
                sucesso = gerar_transcricao(canal, video_id, log_callback)
                if not sucesso:
                    log_callback(f"⛔ Erro ao transcrever {canal}/{video_id}")
    else:
        log_callback("✅ Nenhuma transcrição pendente.")

    # Fase 2 - Resumo
    resumir = listar_videos_para_resumo()
    if resumir:
        log_callback("🧠 Etapa 2: Resumos pendentes encontrados.")
        exibir_tarefas(resumir)
        for canal, videos in resumir.items():
            for video_id in videos:
                log_callback(f"\n📚 Gerando resumo para {canal}/{video_id}...")
                sucesso = gerar_resumo(canal, video_id, log_callback)
                if not sucesso:
                    log_callback(f"⚠️ Erro ao gerar resumo para {canal}/{video_id}")
    else:
        log_callback("✅ Nenhum resumo pendente.")

    # Fase 3 - Tópicos
    gerar_topicos_tarefas = listar_videos_para_topicos()
    if gerar_topicos_tarefas:
        log_callback("🗂️ Etapa 3: Tópicos pendentes encontrados.")
        exibir_tarefas(gerar_topicos_tarefas)
        for canal, videos in gerar_topicos_tarefas.items():
            for video_id in videos:
                log_callback(f"\n📝 Gerando tópicos para {canal}/{video_id}...")
                sucesso = gerar_topicos(canal, video_id, log_callback)
                if not sucesso:
                    log_callback(f"⚠️ Erro ao gerar tópicos para {canal}/{video_id}")
    else:
        log_callback("✅ Nenhum tópico pendente.")

    # Fase 4 - Introdução
    introducao_tarefas = listar_videos_para_introducao()
    if introducao_tarefas:
        log_callback("🎥 Etapa 4: Introduções pendentes encontradas.")
        exibir_tarefas(introducao_tarefas)
        for canal, videos in introducao_tarefas.items():
            for video_id in videos:
                log_callback(f"\n🎬 Gerando introdução para {canal}/{video_id}...")
                sucesso = gerar_introducao(canal, video_id, log_callback)
                if not sucesso:
                    log_callback(f"⚠️ Erro ao gerar introdução para {canal}/{video_id}")
    else:
        log_callback("✅ Nenhuma introdução pendente.")

    # Fase 5 - Conteúdos dos Tópicos
    conteudos_tarefas = listar_videos_para_conteudos()
    if conteudos_tarefas:
        log_callback("✍️ Etapa 5: Conteúdos dos tópicos pendentes encontrados.")
        exibir_tarefas(conteudos_tarefas)
        for canal, videos in conteudos_tarefas.items():
            for video_id in videos:
                log_callback(f"\n🧾 Gerando conteúdos para {canal}/{video_id}...")
                sucesso = gerar_conteudos_topicos(canal, video_id, log_callback)
                if not sucesso:
                    log_callback(f"⚠️ Erro ao gerar conteúdos para {canal}/{video_id}")
    else:
        log_callback("✅ Nenhum conteúdo pendente.")

        

    # Fase 6 - Preparar roteiro para áudio (temporário)
    try:
        from geracao_audio_eleven.controller_audio_eleven import preparar_audios_para_tts
        log_callback("🎧 Etapa 6 (TEMPORÁRIA): Preparando roteiros para áudio ElevenLabs...")
        preparar_audios_para_tts()
    except Exception as e:
        log_callback(f"⚠️ Erro ao preparar áudios para ElevenLabs: {e}")




def exibir_tarefas(tarefas):
    for canal, lista in tarefas.items():
        log_callback(f"\n🎬 Canal '{canal}': {len(lista)} vídeo(s) pendente(s).")
        for v in lista:
            log_callback(f"  → Vídeo {v}")

def iniciar_controller():
    log_callback("📡 Iniciando processamento de vídeos...")
    processar_roteiros()

if __name__ == "__main__":
    iniciar_controller()
