import re
import sqlite3
import json
from pathlib import Path
import yt_dlp

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

def baixar_legenda_yt(url, prioridade_idiomas=None, pasta_destino="."):
    """
    Baixa UMA legenda automática do YouTube na ordem en > es > pt > qualquer outro.
    Retorna: (transcricao_texto, idioma_utilizado) ou (None, None).
    Remove todos os .vtt depois de usar.
    """
    Path(pasta_destino).mkdir(parents=True, exist_ok=True)
    if prioridade_idiomas is None:
        prioridade_idiomas = ['en', 'es', 'pt']

    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'skip_download': True,
        'outtmpl': f"{pasta_destino}/%(id)s.%(ext)s",
        'quiet': True,
    }

    log_callback(f"  [Transcritor] Baixando legendas: {url}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            yt_id = info['id']
            log_callback(f"  [Transcritor] YouTube ID: {yt_id}")
        except Exception as e:
            log_callback(f"  [Transcritor] Erro extract_info: {e}")
            return None, None

    vtt_files = list(Path(pasta_destino).glob(f"{yt_id}.*.vtt"))
    log_callback(f"  [Transcritor] VTTs encontrados: {[f.name for f in vtt_files]}")

    escolhida = None
    idioma = None
    # procura nos prioritários
    for lang in prioridade_idiomas:
        for f in vtt_files:
            if f.stem.endswith(lang):
                escolhida = f
                idioma = lang
                break
        if escolhida:
            break

    # se não achou, pega o primeiro disponível
    if not escolhida and vtt_files:
        escolhida = vtt_files[0]
        idioma = escolhida.stem.split('.')[-1]

    if not escolhida:
        log_callback("  [Transcritor] Nenhum VTT disponível.")
        return None, None

    # limpa e extrai texto
    linhas = escolhida.read_text(encoding="utf-8").splitlines()
    legendas = []
    for l in linhas:
        l = l.strip()
        if (not l
            or l.startswith("WEBVTT")
            or l.startswith("Kind:")
            or l.startswith("Language:")
            or re.match(r"\d\d:\d\d:\d\d\.\d\d\d\s+-->", l)
            or "align:" in l
            or "position:" in l):
            continue
        texto = re.sub(r"<.*?>", "", l)
        if re.search(r'\[(music|música|musique|musik|musica)\]', texto, re.IGNORECASE):
            continue
        legendas.append(texto)
    transcricao = " ".join(legendas).strip()
    log_callback(f"  [Transcritor] Transcrição: {len(transcricao)} caracteres")

    # apaga todos os VTTs
    for f in vtt_files:
        try: f.unlink()
        except: pass

    return transcricao, idioma

def processar_video(canal, video_id):
    log_callback(f"\n📌 Processando Vídeo {video_id} do Canal {canal}...")
    configs = carregar_configs_video(canal, video_id)
    if not configs.get("gerar_roteiro", False):
        log_callback("  ⏭ Ignorado.")
        return
    if configs.get("roteiro_ok", 0) == 1:
        log_callback("  ⏭ Já finalizado.")
        return

    metadados_path = Path(f"data/{canal}/{video_id}/control/metadados.json")
    if not metadados_path.exists():
        log_callback("  ❌ metadados.json não encontrado.")
        return
    link = json.loads(metadados_path.read_text(encoding="utf-8")).get("link")
    if not link:
        log_callback("  ❌ Link ausente em metadados.json.")
        return

    trans, idi = baixar_legenda_yt(
        link,
        prioridade_idiomas=['en', 'es', 'pt'],
        pasta_destino=f"data/{canal}/{video_id}/control"
    )

    transcript_path = Path(f"data/{canal}/{video_id}/control/transcript_original.json")
    if not trans or not trans.strip():
        transcript_path.write_text(
            json.dumps({"erro": "Falha ao obter transcrição automática.", "idioma": idi},
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
    log_callback("  (Placeholder) ✅ Gerando áudio...")
    log_callback("  (Placeholder) ✅ Editando vídeo...")
    log_callback("  (Placeholder) 🏁 Pronto! Vídeo concluído.")
    # atualizar_estado_video(canal, video_id, 1)
