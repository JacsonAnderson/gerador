import os
import re
import json
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from urllib.parse import urlparse, parse_qs

def extrair_id_youtube(url):
    regex = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    resultado = re.findall(regex, url)
    return resultado[0] if resultado else None

def gerar_transcricao(canal, video_id, log=print):
    video_path = Path("data") / canal / video_id
    control_path = video_path / "control"
    metadados_path = control_path / "metadados.json"
    transcript_path = control_path / "transcript_original.json"

    if transcript_path.exists():
        with open(transcript_path, "r", encoding="utf-8") as f:
            try:
                existente = json.load(f)
                if isinstance(existente, str) or existente.get("status") == "indisponivel":
                    log(f"[{canal}/{video_id}] Transcrição já existente.")
                    return True
            except Exception:
                pass

    if not metadados_path.exists():
        log(f"[{canal}/{video_id}] metadados.json não encontrado.")
        return False

    with open(metadados_path, "r", encoding="utf-8") as f:
        dados = json.load(f)

    link = dados.get("link", "")
    video_youtube_id = extrair_id_youtube(link)

    if not video_youtube_id:
        log(f"[{canal}/{video_id}] ID do vídeo não pôde ser extraído.")
        return False

    idiomas_preferidos = ['pt', 'pt-PT', 'pt-BR', 'es', 'en']

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_youtube_id, languages=idiomas_preferidos)
    except (TranscriptsDisabled, NoTranscriptFound):
        try:
            lista = YouTubeTranscriptApi.list_transcripts(video_youtube_id)
            transcript = lista.find_transcript(lista._transcripts.keys()).fetch()
        except Exception:
            with open(transcript_path, "w", encoding="utf-8") as f:
                json.dump({"status": "indisponivel"}, f, indent=4)
            log(f"[{canal}/{video_id}] Nenhuma transcrição disponível (marcado como processado).")
            return False
    except Exception as e:
        log(f"[{canal}/{video_id}] Erro inesperado ao buscar transcrição: {e}")
        return False

    transcript_filtrado = [
        item for item in transcript if not re.search(r'\[(music|música|musique|musik|musica)\]', item['text'], re.IGNORECASE)
    ]

    texto_concatenado = " ".join(item['text'].strip() for item in transcript_filtrado)
    texto_concatenado = re.sub(r'\s+([.,!?;:])', r'\1', texto_concatenado)
    texto_concatenado = re.sub(r'\s{2,}', ' ', texto_concatenado).strip()

    with open(transcript_path, "w", encoding="utf-8") as f:
        json.dump(texto_concatenado, f, indent=4, ensure_ascii=False)

    log(f"[{canal}/{video_id}] Transcrição salva com sucesso.")
    return True
