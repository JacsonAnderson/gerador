# vf_tts.py

import json
from pathlib import Path
from app_videoforge.vf_roteiro import log_callback

def gerar_audio_piper(canal: str, video_id: str) -> bool:
    log_callback(f"🎙️ [Piper] INDISPONÍVEL… VOU IMPLEMENTAR ISSO FUTURAMENTE! ")
    return True

def gerar_audio_elevenlabs(canal: str, video_id: str) -> bool:
    """
    1) Se roteiro.txt NÃO existe em data/{canal}/{video_id}/control, gera-o aqui e sai.
    2) Se roteiro.txt já existe, mas não há pasta tts/, apenas sai (aguardando você colocar os MP3s).
    3) Se roteiro.txt existe e tts/ existe, entra no fluxo de processar os MP3s (TODO).
    """
    control_dir      = Path("data") / canal / video_id / "control"
    meta_path        = control_dir / "metadados.json"
    roteiro_txt_path = control_dir / "roteiro.txt"
    tts_dir          = control_dir / "tts"

    # pré: metadados.json deve existir
    if not meta_path.exists():
        log_callback(f"⚠️ metadados.json não encontrado em {meta_path}")
        return False

    # 1) gerar roteiro.txt na primeira vez
    if not roteiro_txt_path.exists():
        meta   = json.loads(meta_path.read_text(encoding="utf-8"))
        blocos = meta.get("conteudos", [])
        if not blocos:
            log_callback("⚠️ Nenhum conteúdo para TTS encontrado em metadados.json.")
            return False

        roteiro_txt = ""
        for bloco in blocos:
            titulo   = bloco.get("titulo", "").strip()
            conteudo = bloco.get("conteudo", "").strip()
            roteiro_txt += f"{titulo}. {conteudo}\n\n"

        roteiro_txt_path.write_text(roteiro_txt, encoding="utf-8")
        log_callback(f"✅ roteiro.txt gerado em {roteiro_txt_path}")
        return True

    # 2) roteiro.txt já existe: espera a pasta tts/ aparecer
    if not tts_dir.exists():
        log_callback(f"⏭ roteiro.txt encontrado, aguardando áudios em {tts_dir}… Pulando.")
        return True

    # 3) tts/ existe: aqui você processaria os MP3s que colocou lá
    mp3s = sorted(tts_dir.glob("*.mp3"))
    if not mp3s:
        log_callback(f"⚠️ Pasta {tts_dir} está vazia. Aguarde os arquivos .mp3.")
        return True

    # TODO: implementar aqui a lógica de combinar / renomear / mover os MP3s
    log_callback(f"🎙️ Encontrados {len(mp3s)} arquivos em {tts_dir}: {[p.name for p in mp3s]}")
    # ex:
    #   - concatenar todos em um só
    #   - mover para data/{canal}/{video_id}/audio/…
    #   - atualizar metadados.json com paths dos áudios gerados

    return True
