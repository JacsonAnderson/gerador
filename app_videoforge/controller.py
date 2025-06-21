import re
import sqlite3
import json
from pathlib import Path

from app_videoforge.vf_roteiro import gerar_resumo, gerar_topicos, gerar_introducao, baixar_legenda_yt, set_logger as set_roteiro_logger


VIDEOS_DB_PATH = Path("data/videos.db")
CHANNELS_DB_PATH = Path("data/channels.db")

ESTADOS = {
    0: "Pendente",
    1: "Roteiro OK",
    2: "Áudio OK",
    3: "Vídeo Gerado",
    4: "Legendas OK",
    5: "Metadados OK",
    6: "Thumb OK",
    7: "Postado"
}
STATUS_OK_MAP = {0: "Não feito", 1: "OK", 2: "Ignorado"}

log_callback = print

def set_logger(callback):
    global log_callback
    log_callback = callback
    set_roteiro_logger(log_callback)  

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
                log_callback("⚠ Nenhum vídeo válido encontrado (todos já postados ou erro).")
                return
            for vid_id in videos:
                processar_video(canal, vid_id)
        else:
            log_callback("❌ Canal não especificado para modo canal.")
    elif modo == "todos":
        log_callback("\n🚀 Iniciando fluxo para TODOS OS CANAIS")
        canais = listar_canais()
        if not canais:
            log_callback("⚠ Nenhum canal encontrado no banco de dados.")
            return
        for canal_nome in canais:
            videos = listar_videos_validos(canal_nome)
            if not videos:
                continue
            for vid_id in videos:
                processar_video(canal_nome, vid_id)
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
                log_callback(f"⚠ Erro ao ler configs JSON de {canal}/{video_id}.")
    return {}

def atualizar_estado_video(canal, video_id, estado_codigo):
    if estado_codigo not in ESTADOS:
        return
    with sqlite3.connect(VIDEOS_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE videos SET estado = ? WHERE canal = ? AND video_id = ?",
                       (estado_codigo, canal, video_id))
        conn.commit()


def processar_video(canal, video_id):
    log_callback(f"\n📌 Processando Vídeo {video_id} do Canal {canal}...")
    configs = carregar_configs_video(canal, video_id)
    if not configs.get("gerar_roteiro", False):
        log_callback("  ⏭ Ignorado (gerar_roteiro=False).")
        return
    if configs.get("roteiro_ok", 0) == 1:
        log_callback("  ⏭ Já finalizado (roteiro_ok=1).")
        return

    control_dir = Path(f"data/{canal}/{video_id}/control")
    metadados_path = control_dir / "metadados.json"
    if not metadados_path.exists():
        log_callback("  ❌ metadados.json não encontrado.")
        return
    link = json.loads(metadados_path.read_text(encoding="utf-8")).get("link")
    if not link:
        log_callback("  ❌ Link ausente em metadados.json.")
        return

    # ─── Etapa 1: Transcrição ─────────────────────────────────────────
    transcript_path = control_dir / "transcript_original.json"
    if transcript_path.exists():
        try:
            dados = json.loads(transcript_path.read_text(encoding="utf-8"))
            if dados.get("transcricao_limpa", "").strip():
                log_callback(f"  ✅ Transcrição já existente em {transcript_path}. Pulando etapa.")
            else:
                raise ValueError("transcricao_limpa vazia")
        except Exception as e:
            log_callback(f"  ⚠️ Transcript inválido ({e}), refazendo...")
            trans, idi = baixar_legenda_yt(link, ['en','es','pt'], str(control_dir))
            if not trans or not trans.strip():
                transcript_path.write_text(
                    json.dumps({"erro":"Falha ao obter transcrição automática.","idioma": idi},
                               ensure_ascii=False, indent=4),
                    encoding="utf-8"
                )
                log_callback(f"  ⚠️ Erro salvo em {transcript_path}")
                return
            transcript_path.write_text(
                json.dumps({"transcricao_limpa": trans, "idioma": idi},
                           ensure_ascii=False, indent=4),
                encoding="utf-8"
            )
            log_callback(f"  ✅ Transcrição refeita e salva em {transcript_path} (idioma: {idi})")
    else:
        trans, idi = baixar_legenda_yt(link, ['en','es','pt'], str(control_dir))
        if not trans or not trans.strip():
            transcript_path.write_text(
                json.dumps({"erro":"Falha ao obter transcrição automática.","idioma": idi},
                           ensure_ascii=False, indent=4),
                encoding="utf-8"
            )
            log_callback(f"  ⚠️ Erro salvo em {transcript_path}")
            return
        transcript_path.write_text(
            json.dumps({"transcricao_limpa": trans, "idioma": idi},
                       ensure_ascii=False, indent=4),
            encoding="utf-8"
        )
        log_callback(f"  ✅ Transcrição salva em {transcript_path} (idioma: {idi})")

    # ─── Etapa 2: Resumo ──────────────────────────────────────────────
    meta = json.loads(metadados_path.read_text(encoding="utf-8"))
    if meta.get("resumo"):
        log_callback("  ✅ Resumo já existe em metadados.json. Pulando.")
    else:
        sucesso = gerar_resumo(canal, video_id)
        if not sucesso:
            log_callback(f"  ⚠️ Falha ao gerar resumo.")
            return

    # ─── Etapa 3: Tópicos ──────────────────────────────────────────────

    # carrega metadados para ver se já tem tópicos
    meta = json.loads(metadados_path.read_text(encoding="utf-8"))
    if meta.get("topicos"):
        log_callback("  ✅ Tópicos já existem em metadados.json. Pulando.")
    else:
        sucesso = gerar_topicos(canal, video_id)
        if not sucesso:
            log_callback("  ⚠️ Falha ao gerar tópicos.")
            return
        log_callback("  ✅ Tópicos salvos em metadados.json")

    # ─── Etapa 4: Introdução ────────────────────────────────────────────
    if not gerar_introducao(canal, video_id):
        log_callback("  ⚠️ Falha ao gerar introdução.")
        return




    # ─── Demais etapas (Áudio, Vídeo, etc) ──────────────────────────
    log_callback("  (Placeholder) ✅ Gerando áudio...")
    log_callback("  (Placeholder) ✅ Editando vídeo...")
    log_callback("  (Placeholder) 🏁 Pronto! Vídeo concluído.")
    # atualizar_estado_video(canal, video_id, 1)
