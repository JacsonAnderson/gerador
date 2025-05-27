import os
import sys
import subprocess
import time

from pathlib import Path

# Adiciona o diretório raiz ao sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app_gerador_de_video.whisperx_analisador import transcrever_com_whisperx
from app_gerador_de_video.gerador_descricao_chave import processar_segmentos

# Novo import para preenchimento de nome_midia
from app_gerador_de_video.preencher_nome_midia import preencher_segmentos_json

from app_midia_manual_importer.controller_midia import iniciar_importador
from app_gerador_de_video.preencher_segmentos_obrigatorio import preencher_segmentos_obrigatorio




DATA_DIR = "data"
AUDIO_FILE_NAME = "narracao.wav"
SEGMENTOS_FILE_NAME = "segmentos.json"

log_callback = print

def set_logger(callback):
    global log_callback
    log_callback = callback

def listar_videos_para_gerar_video():
    tarefas = {}
    for canal in os.listdir(DATA_DIR):
        canal_path = os.path.join(DATA_DIR, canal)
        if not os.path.isdir(canal_path):
            continue

        videos = []
        for item in os.listdir(canal_path):
            video_path = os.path.join(canal_path, item)
            control_path = os.path.join(video_path, "control")
            finalizado_path = os.path.join(control_path, "video_finalizado.txt")

            if os.path.isdir(video_path) and item.isdigit():
                if not os.path.exists(finalizado_path):
                    videos.append(item)

        if videos:
            tarefas[canal] = sorted(videos)

    return tarefas

def processar_videos():
    tarefas = listar_videos_para_gerar_video()

    if not tarefas:
        log_callback("✅ Nenhum vídeo pendente para geração.")
        return

    for canal, videos in tarefas.items():
        log_callback(f"\n🎞️ Canal '{canal}': {len(videos)} vídeo(s) pendente(s) para geração.")
        for video_id in videos:
            log_callback(f"🎬 Gerando vídeo para {canal}/{video_id}...")

            control_path = Path(DATA_DIR) / canal / video_id / "control"
            audio_path = control_path.parent / "audios" / AUDIO_FILE_NAME
            segmentos_path = control_path / SEGMENTOS_FILE_NAME

            # Transcrição
            if not segmentos_path.exists():
                log_callback("🧠 Segmentos não encontrados. Iniciando transcrição com WhisperX...")
                sucesso = transcrever_com_whisperx(audio_path, segmentos_path)
                if not sucesso:
                    log_callback(f"⛔ Falha na transcrição de {canal}/{video_id}. Pulando...")
                    continue

            # Geração de descrições visuais
            log_callback("🔎 Gerando descrições visuais dos segmentos...")
            processar_segmentos(segmentos_path)

            # Preenchimento automático de nome_midia com busca semântica
            log_callback("🔗 Buscando mídias semelhantes para os segmentos...")

            index_file = Path("data_midia/index_annoy/index.ann")
            if not index_file.exists():
                log_callback("⚙️ Índice Annoy não encontrado. Reconstruindo...")
                iniciar_importador()

            preencher_segmentos_json(segmentos_path)


            # Verifica se há faltando_midias.json e ainda não baixamos os previews
            faltando_path = control_path / "faltando_midias.json"
            flag_baixado = control_path / "midias_ja_baixadas.txt"

            if faltando_path.exists() and not flag_baixado.exists():
                log_callback("📥 Baixando mídias automaticamente via Storyblocks...")
                subprocess.run([
                    sys.executable,
                    "app_gerador_de_video/downloader_midias_storyblocks.py",
                    str(faltando_path)
                ])

                log_callback("⏳ Aguardando liberação dos arquivos...")
                time.sleep(3)

                # Após baixar, importar e indexar
                log_callback("📂 Processando e indexando mídias baixadas...")
                iniciar_importador()

                # Marca como baixado
                with open(flag_baixado, "w", encoding="utf-8", errors="ignore") as f:
                    f.write("Mídias baixadas e processadas.\n")  # Evita emoji!

            preencher_segmentos_obrigatorio(segmentos_path)


            # Aqui entrará a montagem do vídeo futuramente...

            finalizado_path = control_path / "video_finalizado.txt"
            with open(finalizado_path, "w", encoding="utf-8") as f:
                f.write("✅ Vídeo finalizado.\n")

            log_callback(f"✅ Vídeo marcado como finalizado: {canal}/{video_id}")

def iniciar_controller():
    log_callback("📽️ Iniciando gerador de vídeos...")
    processar_videos()

if __name__ == "__main__":
    iniciar_controller()
