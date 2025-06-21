import re
import sqlite3
import json
from pathlib import Path

from app_videoforge.vf_roteiro import gerar_resumo, gerar_topicos, gerar_introducao, gerar_conteudos_topicos, baixar_legenda_yt, set_logger as set_roteiro_logger
from app_videoforge.vf_tts import gerar_audio_piper, gerar_audio_elevenlabs



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

def marcar_roteiro_concluido(canal: str, video_id: str):
    """Seta roteiro_ok=1 e estado=1 na tabela videos para este vídeo."""
    with sqlite3.connect(VIDEOS_DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE videos SET roteiro_ok = 1, estado = 1 WHERE canal = ? AND video_id = ?",
            (canal, video_id)
        )
        conn.commit()

def obter_status_roteiro(canal: str, video_id: str) -> int:
    """Retorna o valor da coluna roteiro_ok para este vídeo."""
    with sqlite3.connect(VIDEOS_DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT roteiro_ok FROM videos WHERE canal = ? AND video_id = ?",
            (canal, video_id)
        )
        row = cur.fetchone()
    return row[0] if row else 0

def obter_status_audio(canal: str, video_id: str) -> int:
    """Retorna o valor de audio_ok no banco (0=pendente,1=OK,2=ignorado)."""
    with sqlite3.connect(VIDEOS_DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT audio_ok FROM videos WHERE canal = ? AND video_id = ?",
            (canal, video_id)
        )
        row = cur.fetchone()
    return row[0] if row else 0

def marcar_audio_concluido(canal: str, video_id: str):
    """Seta audio_ok=1 e estado=2 na tabela videos."""
    with sqlite3.connect(VIDEOS_DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE videos SET audio_ok = 1, estado = 2 WHERE canal = ? AND video_id = ?",
            (canal, video_id)
        )
        conn.commit()

def processar_video(canal, video_id):
    log_callback(f"\n📌 Processando Vídeo {video_id} do Canal {canal}...")
    configs = carregar_configs_video(canal, video_id)


    # ─── ROTEIRO ───────────────────────────────────────────
    if not configs.get("gerar_roteiro", False):
        log_callback("  ⏭ Roteiro ignorado. ")
        return
    
    if obter_status_roteiro(canal, video_id) == 1:
        log_callback("  ⏭ Roteiro já finalizado.")
        
    else:
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

        # ─── Etapa 5: Conteúdos ────────────────────────────────────────────
        if not gerar_conteudos_topicos(canal, video_id):
            log_callback("  ⚠️ Falha ao gerar conteúdos dos tópicos.")
            return

        # ─── Marcando roteiro como concluído ────────────────────────────────
        marcar_roteiro_concluido(canal, video_id)
        log_callback(f"  ✅ Vídeo {video_id} marcado como roteiro OK e estado atualizado para Concluido.")


        # ─── ÁUDIO ────────────────────────────────────────────
    log_callback("  🎤 Iniciando geração de áudio...")
    gerar_audio  = configs.get("gerar_audio", False)    # Piper (local)
    audio_manual = configs.get("audio_manual", False)   # ElevenLabs (remoto)

    # nenhum dos dois? ignora mas NÃO retorna
    if not gerar_audio and not audio_manual:
        log_callback("  ⏭ Áudio desativado. Marcando como ignorado e seguindo para vídeo.")
        with sqlite3.connect(VIDEOS_DB_PATH) as conn:
            conn.execute(
                "UPDATE videos SET audio_ok = 2 WHERE canal = ? AND video_id = ?",
                (canal, video_id)
            )
            conn.commit()
    else:
        # não podem ser ambos True
        if gerar_audio and audio_manual:
            log_callback("  ⚠️ Configuração inválida: gerar_audio e audio_manual ambos True. Abortando.")
            return

        status_audio = obter_status_audio(canal, video_id)
        if status_audio == 1:
            log_callback("  ⏭ Áudio já OK. Pulando geração.")
        else:
            # fluxo de Piper vs ElevenLabs
            if gerar_audio:
                log_callback("  🎙️ Gerando áudio local com Piper...")
                sucesso_audio = gerar_audio_piper(canal, video_id)
                check_tts = False  # como Piper ainda não implementado, não marca
            else:
                log_callback("  🎙️ Gerando áudio remoto com ElevenLabs...")
                sucesso_audio = gerar_audio_elevenlabs(canal, video_id)
                # só consideramos “feito” se houver .mp3 na pasta tts/
                tts_dir = Path("data")/canal/video_id/"control"/"tts"
                mp3s = list(tts_dir.glob("*.mp3")) if tts_dir.exists() else []
                check_tts = bool(mp3s)

            if not sucesso_audio:
                log_callback("  ⚠️ Falha ao gerar áudio. Abortando.")
                return

            if check_tts:
                marcar_audio_concluido(canal, video_id)
                log_callback("  ✅ Áudio OK (audio_ok=1, estado=2).")
            else:
                log_callback("  ⏭ Áudio não concluído — aguardando arquivos .mp3 em tts/.")







    # ─── VÍDEO ─────────────────────────────────────────────
    # Só entra aqui se áudio estiver OK (1) ou IGNORADO (2)
    log_callback("  (Placeholder) ✅ Editando vídeo...")
    # ─── Demais etapas (Áudio, Vídeo, etc) ──────────────────────────

    log_callback("  (Placeholder) 🏁 Pronto! Vídeo concluído.")
    # atualizar_estado_video(canal, video_id, 1)
