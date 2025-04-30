import os
import json
from pathlib import Path

DATA_DIR = "data"
ARQUIVO_DESTINO = "roteiro_audio.txt"

def log(msg):
    print(msg)

def preparar_audios_para_tts():
    tarefas = []

    for canal in os.listdir(DATA_DIR):
        canal_path = Path(DATA_DIR) / canal
        if not canal_path.is_dir():
            continue

        for video_id in os.listdir(canal_path):
            video_path = canal_path / video_id
            control_path = video_path / "control"
            audios_path = video_path / "audios"
            destino_path = audios_path / ARQUIVO_DESTINO

            # Verifica se já foi preparado
            if destino_path.exists():
                continue

            introducao_txt = control_path / "introducao.txt"
            roteiros_json = control_path / "roteiros.json"

            if not introducao_txt.exists() or not roteiros_json.exists():
                log(f"⚠️ Arquivos ausentes em {canal}/{video_id}. Pulando.")
                continue

            try:
                with open(introducao_txt, "r", encoding="utf-8") as f:
                    introducao = f.read().strip()

                with open(roteiros_json, "r", encoding="utf-8") as f:
                    dados_roteiros = json.load(f)

                conteudos = [
                    bloco["conteudo"].strip()
                    for bloco in dados_roteiros.get("roteiros", [])
                    if bloco.get("conteudo", "").strip()
                ]

                texto_final = introducao + "\n\n" + "\n\n".join(conteudos)

                # Cria a pasta "audios" se não existir
                audios_path.mkdir(parents=True, exist_ok=True)

                with open(destino_path, "w", encoding="utf-8") as f:
                    f.write(texto_final)

                log(f"✅ Roteiro para áudio salvo em {destino_path}")

            except Exception as e:
                log(f"❌ Erro ao preparar áudio em {canal}/{video_id}: {e}")

if __name__ == "__main__":
    log("🔊 Iniciando preparação de roteiros para áudio ElevenLabs...")
    preparar_audios_para_tts()
    log("✅ Finalizado.")
