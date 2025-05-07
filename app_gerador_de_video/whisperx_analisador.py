import os
import json
import subprocess
from pathlib import Path
import math

DATA_DIR = "data"
AUDIO_FILE_NAME = "narracao.wav"
SEGMENTOS_FILE_NAME = "segmentos.json"
MAX_SEGMENTO = 6.0  # segundos
MIN_SEGMENTO = 2.0  # segundos

def print_etapa(msg):
    print("\n" + "=" * 50)
    print(f"🟡 {msg}")
    print("=" * 50)

def dividir_segmento(inicio, fim, texto):
    partes = []
    duracao = fim - inicio

    if duracao <= MAX_SEGMENTO:
        partes.append({
            "text": texto.strip(),
            "start": round(inicio, 3),
            "end": round(fim, 3),
            "total_time_segment": round(duracao, 3),
            "descricao_chave": "",
            "nome_midia": ""
        })
        return partes

    partes_count = math.ceil(duracao / MAX_SEGMENTO)
    duracao_dividida = duracao / partes_count

    for i in range(partes_count):
        sub_inicio = inicio + i * duracao_dividida
        sub_fim = min(sub_inicio + duracao_dividida, fim)
        partes.append({
            "text": texto.strip(),
            "start": round(sub_inicio, 3),
            "end": round(sub_fim, 3),
            "total_time_segment": round(sub_fim - sub_inicio, 3),
            "descricao_chave": "",
            "nome_midia": ""
        })

    return partes

def transcrever_com_whisperx(caminho_audio, caminho_segmentos):
    print_etapa(f"Transcrevendo com WhisperX: {caminho_audio}")

    try:
        result = subprocess.run(
            [
                str(Path(".venv/Scripts/whisperx.exe").resolve()),
                str(caminho_audio),
                "--output_format", "json",
                "--output_dir", str(caminho_segmentos.parent),
                "--device", "cuda"
            ],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print("❌ Erro ao executar WhisperX:")
            print(result.stderr)
            return False

        json_gerado = caminho_segmentos.parent / (Path(caminho_audio).stem + ".json")
        if not json_gerado.exists():
            print("❌ Arquivo JSON não encontrado após transcrição.")
            return False

        with open(json_gerado, "r", encoding="utf-8") as f:
            dados = json.load(f)

        print("🧩 Processando e ajustando segmentos...")
        raw_segs = dados.get("segments", [])
        segmentos_processados = []
        total_time_segments = 0.0

        buffer_text = ""
        buffer_start = None
        buffer_end = None

        for seg in raw_segs:
            start = seg["start"]
            end = seg["end"]
            text = seg["text"].strip()
            duracao = end - start

            if buffer_start is None:
                buffer_start = start
                buffer_end = end
                buffer_text = text
                continue

            # Acumula
            buffer_end = end
            buffer_text += " " + text

            # Se buffer atingiu o mínimo exigido, salva
            buffer_duracao = buffer_end - buffer_start
            if buffer_duracao >= MIN_SEGMENTO:
                partes = dividir_segmento(buffer_start, buffer_end, buffer_text)
                segmentos_processados.extend(partes)
                for p in partes:
                    total_time_segments += p["total_time_segment"]
                buffer_start = None
                buffer_end = None
                buffer_text = ""

        # Último buffer (caso tenha sobrado algo pequeno)
        if buffer_start is not None:
            partes = dividir_segmento(buffer_start, buffer_end, buffer_text)
            segmentos_processados.extend(partes)
            for p in partes:
                total_time_segments += p["total_time_segment"]

        resultado_final = {
            "total_time": round(dados.get("duration", total_time_segments), 3),
            "total_time_segments": round(total_time_segments, 3),
            "segments": segmentos_processados
        }

        with open(caminho_segmentos, "w", encoding="utf-8") as f:
            json.dump(resultado_final, f, indent=4, ensure_ascii=False)

        print(f"✅ Segmentos salvos com sucesso em: {caminho_segmentos}")
        return True

    except Exception as e:
        print(f"❌ Erro inesperado durante a transcrição: {e}")
        return False


def processar_videos_para_segmentos():
    print_etapa("🎧 Buscando vídeos com narracao.wav sem segmentos...")

    for canal in os.listdir(DATA_DIR):
        caminho_canal = Path(DATA_DIR) / canal
        if not caminho_canal.is_dir():
            continue

        for video in os.listdir(caminho_canal):
            if not video.isdigit():
                continue

            pasta_video = caminho_canal / video
            pasta_control = pasta_video / "control"
            pasta_audio = pasta_video / "audios"

            if not pasta_control.exists() or not pasta_audio.exists():
                continue

            caminho_segmentos = pasta_control / SEGMENTOS_FILE_NAME
            caminho_audio = pasta_audio / AUDIO_FILE_NAME

            print(f"\n📂 Analisando {canal}/{video}...")

            if caminho_segmentos.exists():
                print(f"⏩ Segmentos já existem. Ignorando.")
                continue

            if not caminho_audio.exists():
                print(f"⚠️ Arquivo {AUDIO_FILE_NAME} não encontrado em {pasta_audio}")
                continue

            sucesso = transcrever_com_whisperx(caminho_audio, caminho_segmentos)
            if not sucesso:
                print(f"❌ Falha ao processar {canal}/{video}")


if __name__ == "__main__":
    processar_videos_para_segmentos()
