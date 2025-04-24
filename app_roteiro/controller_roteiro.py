import os
import json
from datetime import datetime

DATA_DIR = "data"

log_callback = print  # padrão, se não redefinido

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

            # Checa se é pasta numérica (tipo "01", "02", ...)
            if os.path.isdir(video_path) and item.isdigit():
                pasta_control = os.path.join(video_path, "control")
                roteiro_json = os.path.join(pasta_control, "roteiro_pronto.json")
                video_final_json = os.path.join(video_path, "video_pronto.json")

                # Se o vídeo já tiver roteiro OU vídeo finalizado, ignora
                if os.path.exists(roteiro_json) or os.path.exists(video_final_json):
                    continue

                videos.append(item)

        if videos:
            tarefas[canal] = videos

    return tarefas

def exibir_tarefas(tarefas):
    for canal, lista in tarefas.items():
        log_callback(f"\n🎬 Canal '{canal}': {len(lista)} vídeo(s) para gerar roteiro.")
        for v in lista:
            log_callback(f"  → Vídeo {v}")

def iniciar_controller():
    log_callback("📡 Escaneando canais em busca de roteiros pendentes...")
    tarefas = listar_videos_para_roteiro()

    if not tarefas:
        log_callback("✅ Nenhum vídeo pendente encontrado. Tudo finalizado.")
        return

    exibir_tarefas(tarefas)

    # Aqui entraria a lógica de geração de roteiro:
    # for canal, videos in tarefas.items():
    #     for video_id in videos:
    #         gerar_roteiro_para_video(canal, video_id)

if __name__ == "__main__":
    iniciar_controller()
