import os
import json
from datetime import datetime
from app_roteiro.transcritor import gerar_transcricao

DATA_DIR = "data"
log_callback = print

def set_logger(callback):
    global log_callback
    log_callback = callback

def listar_videos_para_roteiro():
    tarefas = {}

    for canal in os.listdir(DATA_DIR):
        canal_path = os.path.join(DATA_DIR, canal)
        if not os.path.isdir(canal_path):
            continue

        videos = []

        for item in os.listdir(canal_path):
            video_path = os.path.join(canal_path, item)

            if os.path.isdir(video_path) and item.isdigit():
                pasta_control = os.path.join(video_path, "control")
                roteiro_json = os.path.join(pasta_control, "roteiro_pronto.json")
                video_final_json = os.path.join(video_path, "video_pronto.json")
                transcript_json = os.path.join(pasta_control, "transcript_original.json")

                # Se qualquer um dos arquivos de controle final existir, ignora
                if os.path.exists(roteiro_json) or os.path.exists(video_final_json) or os.path.exists(transcript_json):
                    continue

                videos.append(item)

        if videos:
            tarefas[canal] = sorted(videos)

    return tarefas

def exibir_tarefas(tarefas):
    for canal, lista in tarefas.items():
        log_callback(f"\n🎬 Canal '{canal}': {len(lista)} vídeo(s) para gerar roteiro.")
        for v in lista:
            log_callback(f"  → Vídeo {v}")

def processar_roteiros():
    while True:
        tarefas = listar_videos_para_roteiro()
        if not tarefas:
            log_callback("\n✅ Nenhum vídeo pendente encontrado. Tudo finalizado.")
            break

        exibir_tarefas(tarefas)

        for canal, videos in tarefas.items():
            for video_id in videos:
                log_callback(f"\n⚙️ Processando {canal}/{video_id}...")

                sucesso_transcricao = gerar_transcricao(canal, video_id, log_callback)

                if not sucesso_transcricao:
                    log_callback(f"⛔ Transcrição indisponível ou erro em {canal}/{video_id}, pulando.")
                    continue

                log_callback(f"✍️ (AQUI) Gerar roteiro para {canal}/{video_id}")

        log_callback("\n🔁 Verificando se há novos vídeos adicionados durante o processo...")

def iniciar_controller():
    log_callback("📡 Iniciando processamento de roteiros...")
    processar_roteiros()

if __name__ == "__main__":
    iniciar_controller()
