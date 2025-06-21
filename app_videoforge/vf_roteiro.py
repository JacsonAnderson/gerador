# vf_roteiro.py
import re
import os
import json, re
import sqlite3
from pathlib import Path

# Importante para o baixar_legenda_yt
import yt_dlp


# Importante para usar o chat gpt
from dotenv import load_dotenv
from openai import OpenAI




# ------------------------------------------------------------------
# 1) Carregamento de configs direto do SQLite
# ------------------------------------------------------------------
VIDEOS_DB_PATH = Path("data/videos.db")

def _carregar_configs(canal: str, video_id: str) -> dict:
    """Busca configs JSON diretamente na tabela videos."""
    with sqlite3.connect(VIDEOS_DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT configs FROM videos WHERE canal = ? AND video_id = ?",
            (canal, video_id)
        )
        row = cur.fetchone()
    if not row:
        return {}
    try:
        return json.loads(row[0])
    except:
        return {}


# ------------------------------------------------------------------
# 2) Inicialização do cliente OpenAI
# ------------------------------------------------------------------
load_dotenv()
_api_key = os.getenv("OPENAI_API_KEY")
if not _api_key:
    raise RuntimeError("❌ OPENAI_API_KEY não encontrada no .env")
_client = OpenAI(api_key=_api_key)

log_callback = print  # Você pode sobrescrever via set_logger, se quiser

def set_logger(callback):
    global log_callback
    log_callback = callback


# ------------------------------------------------------------------
# 3) Baixar e extrair transcrição do YouTube
# ------------------------------------------------------------------

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

    log_callback(f"[vf_roteiro] Baixando legendas de: {url}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            yt_id = info['id']
            log_callback(f"[vf_roteiro] YouTube ID detectado: {yt_id}")
        except Exception as e:
            log_callback(f"[vf_roteiro] Erro no extract_info: {e}")
            return None, None

    # coleta todos os VTTs
    vtt_files = list(Path(pasta_destino).glob(f"{yt_id}.*.vtt"))
    log_callback(f"[vf_roteiro] VTTs baixados: {[f.name for f in vtt_files]}")

    # escolhe por prioridade
    escolhida = None
    idioma = None
    for lang in prioridade_idiomas:
        for f in vtt_files:
            if f.stem.endswith(lang):
                escolhida = f
                idioma = lang
                break
        if escolhida:
            break

    # se não achou prioritário, pega o primeiro
    if not escolhida and vtt_files:
        escolhida = vtt_files[0]
        idioma = escolhida.stem.split('.')[-1]
        log_callback(f"[vf_roteiro] Sem prioridade, usando: {escolhida.name}")

    if not escolhida:
        log_callback("[vf_roteiro] Nenhum VTT encontrado.")
        return None, None

    # extrai o texto
    linhas = escolhida.read_text(encoding="utf-8").splitlines()
    legendas = []
    for l in linhas:
        l = l.strip()
        if (not l
            or l.startswith(("WEBVTT", "Kind:", "Language:"))
            or "-->" in l
            or "align:" in l
            or "position:" in l):
            continue
        texto = re.sub(r"<.*?>", "", l)
        if re.search(r'\[(music|música|musique|musik|musica)\]', texto, re.IGNORECASE):
            continue
        legendas.append(texto)

    transcricao = " ".join(legendas).strip()
    log_callback(f"[vf_roteiro] Texto extraído: {len(transcricao)} chars")

    # limpa todos os .vtt
    for f in vtt_files:
        try:
            f.unlink()
        except:
            pass

    return transcricao, idioma


# ------------------------------------------------------------------
# 4) Gerar resumo e injetar em metadados.json
# ------------------------------------------------------------------

def gerar_resumo(canal: str, video_id: str) -> bool:
    """
    Gera um resumo a partir de data/{canal}/{video_id}/control/transcript_original.json
    e injeta esse resumo dentro de data/{canal}/{video_id}/control/metadados.json
    na chave "resumo". Retorna True se sucesso.
    """
    cp = Path("data") / canal / video_id / "control"
    transcript = cp / "transcript_original.json"
    meta_path  = cp / "metadados.json"

    if not transcript.exists():
        log_callback(f"[vf_roteiro] Transcrição não encontrada em {transcript}")
        return False
    if not meta_path.exists():
        log_callback(f"[vf_roteiro] metadados.json não encontrado em {meta_path}")
        return False

    # carrega transcrição limpa
    dados_trans = json.loads(transcript.read_text(encoding="utf-8"))
    txt = dados_trans.get("transcricao_limpa") if isinstance(dados_trans, dict) else ""
    if not txt or not txt.strip():
        log_callback("[vf_roteiro] Transcrição vazia.")
        return False

    prompt = (
        "Você é um assistente especialista em análise de conteúdo de vídeos do YouTube, com foco em compreensão profunda, segmentação de tópicos e extração de ideias centrais. "
        "Abaixo está a transcrição completa de um vídeo. Sua tarefa é gerar um resumo avançado e estruturado, como se fosse uma apresentação escrita para um briefing editorial.\n\n"
        
        "⚙️ **Instruções específicas:**\n"
        "1. Leia todo o conteúdo cuidadosamente.\n"
        "2. Identifique e liste os principais tópicos abordados, com subtítulos claros se necessário.\n"
        "3. Para cada tópico, explique o que foi dito com detalhes, destacando as ideias principais, exemplos utilizados, dados mencionados ou histórias relatadas.\n"
        "4. Se houver momentos de opinião, crítica, humor, instrução ou ensinamento, destaque-os separadamente.\n"
        "5. Use linguagem clara, profissional e fluída, como se estivesse explicando o conteúdo a um leitor que precisa entender tudo sem ver o vídeo.\n"
        "6. Mantenha a organização lógica e sequencial do vídeo, respeitando a ordem dos acontecimentos.\n\n"
        
        f"🎙️ **Transcrição original do vídeo:**\n{txt}\n\n"
        "✍️ **Gere agora o resumo completo e detalhado conforme solicitado acima:**"
    )

    try:
        resp = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}],
            temperature=0.7
        )
        resumo_text = resp.choices[0].message.content.strip()

        # agora abrimos o metadados.json, injetamos o resumo e salvamos
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["resumo"] = resumo_text
        meta_path.write_text(
            json.dumps(meta, ensure_ascii=False, indent=4),
            encoding="utf-8"
        )

        log_callback(f"✅ Resumo salvo em {meta_path}")
        return True

    except Exception as e:
        log_callback(f"⚠️ Erro ao gerar resumo: {e}")
        return False


# ------------------------------------------------------------------
# 5) Gerar tópicos 
# ------------------------------------------------------------------
def gerar_topicos(canal: str, video_id: str) -> bool:
    control_dir    = Path("data") / canal / video_id / "control"
    metadados_path = control_dir / "metadados.json"
    transcript_p    = control_dir / "transcript_original.json"

    # 1) já gerado?
    meta = json.loads(metadados_path.read_text(encoding="utf-8"))
    if meta.get("topicos"):
        log_callback("✅ Tópicos já existem em metadados.json. Pulando.")
        return True

    # 2) transcript ok?
    if not transcript_p.exists():
        log_callback("⚠️ Transcrição não encontrada. Não foi possível gerar tópicos.")
        return False
    dados = json.loads(transcript_p.read_text(encoding="utf-8"))
    txt   = dados.get("transcricao_limpa", "") if isinstance(dados, dict) else ""
    if not txt.strip():
        log_callback("⚠️ Transcrição vazia. Não foi possível gerar tópicos.")
        return False

    # 3) carrega prompt_topicos (DB ou prompts.json)
    cfg        = _carregar_configs(canal, video_id)
    prompt_top = cfg.get("prompt_topicos", "").strip()
    if not prompt_top:
        prompts_file = Path("data") / canal / "prompts.json"
        if prompts_file.exists():
            j = json.loads(prompts_file.read_text(encoding="utf-8"))
            prompt_top = j.get("prompt_topicos", "").strip()
    if not prompt_top:
        log_callback("⚠️ prompt_topicos não definido. Não foi possível gerar tópicos.")
        return False

    # 4) monta prompt final
    idioma  = (cfg.get("idioma", "") or "").lower()
    inst_id = obter_instrucao_idioma(idioma)

    prompt_final = f"""{prompt_top}

Transcrição para referência:
{txt}

⚠️ IMPORTANTE: Gere exatamente no formato abaixo, sem comentários extras e mantendo o número exato de tópicos (nem mais, nem menos):

⚠️ Estes tópicos devem ser direto ao ponto. Exemplo: se o vídeo é sobre "4 remédios para curar o coração",
  - Tópico 01 fala sobre o problema  
  - Tópico 02 fala sobre o Remédio 01  
  - Tópico 03 fala sobre o Remédio 02  
  …e assim por diante.

⚠️ Vamos evitar tópicos genéricos! Foque no que foi dito na transcrição e agregue valor real ao conteúdo.  
⚠️ Cada tópico deve ser útil para a criação de conteúdos altamente relevantes e impactantes.  

{inst_id}

Topico 01: "TÍTULO IMPACTANTE E PERSUASIVO DO TÓPICO 01"  
RESUMO: "Descrição clara e detalhada do que esse tópico aborda."

Topico 02: "TÍTULO IMPACTANTE E PERSUASIVO DO TÓPICO 02"  
RESUMO: "Descrição clara e detalhada do que esse tópico aborda."

Topico 03: "TÍTULO IMPACTANTE E PERSUASIVO DO TÓPICO 03"  
RESUMO: "Descrição clara e detalhada do que esse tópico aborda."

… (Continue exatamente nesse formato até completar o número exato de tópicos solicitados)
"""

    # 5) chama OpenAI e extrai via regex
    resp = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt_final}],
        temperature=0.4
    )
    out = resp.choices[0].message.content.strip()

    pad   = r'[Tt][oó]pico\s*(\d+):\s*"([^"]+)"\s*RESUMO:\s*"([^"]+)"'
    found = re.findall(pad, out, re.IGNORECASE)
    if not found:
        log_callback("⚠️ Nenhum tópico detectado pela regex.")
        return False

    lista = [
        {"numero": int(n), "titulo": t.strip(), "resumo": r.strip()}
        for n, t, r in found
    ]

    # 6) injeta em metadados.json
    meta["topicos"] = lista
    metadados_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=4),
        encoding="utf-8"
    )
    return True


# ------------------------------------------------------------
# Dicionário de idiomas (deixa tudo isso aqui embaixo, sem misturar)
# ------------------------------------------------------------

IDIOMAS_SUPORTADOS = {
    "pt": {
        "nome": "Português Brasileiro",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Português Brasileiro correto, com clareza e sem regionalismos excessivos."
    },
    "es": {
        "nome": "Espanhol Neutro",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Espanhol neutro latino, com clareza e sem misturar português ou outros idiomas."
    },
    "en": {
        "nome": "Inglês",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Inglês fluente, natural e de fácil entendimento para o público global."
    },
    "fr": {
        "nome": "Francês",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Francês europeu padrão, com clareza e elegância."
    },
    "de": {
        "nome": "Alemão",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Alemão padrão (Hochdeutsch), formal e claro."
    },
    "it": {
        "nome": "Italiano",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Italiano formal, elegante e de fácil compreensão."
    },
    "ja": {
        "nome": "Japonês",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Japonês formal (日本語), com clareza e respeito pela cultura local."
    },
    "zh": {
        "nome": "Chinês (Mandarim Simplificado)",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Chinês Mandarim Simplificado (中文简体), de forma clara e profissional."
    },
    "ru": {
        "nome": "Russo",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Russo padrão, com linguagem formal e respeitosa."
    },
    "ar": {
        "nome": "Árabe",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Árabe moderno padrão (الفصحى), claro e respeitando normas culturais."
    },
    "hi": {
        "nome": "Hindi",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Hindi formal (हिन्दी), de forma clara e culturalmente respeitosa."
    },
    "tr": {
        "nome": "Turco",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Turco padrão, com linguagem clara e respeitosa."
    },
    "nl": {
        "nome": "Holandês",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Holandês padrão (Nederlands), claro e natural."
    },
    "pl": {
        "nome": "Polonês",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Polonês padrão, claro e fluente."
    },
    "ko": {
        "nome": "Coreano",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Coreano padrão (한국어), claro e natural."
    },
    "sv": {
        "nome": "Sueco",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Sueco padrão, claro e profissional."
    },
    "no": {
        "nome": "Norueguês",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Norueguês padrão (Bokmål), claro e respeitoso."
    },
    "da": {
        "nome": "Dinamarquês",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Dinamarquês padrão, claro e natural."
    },
    "fi": {
        "nome": "Finlandês",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Finlandês padrão, claro e fluido."
    },
    "id": {
        "nome": "Indonésio",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Indonésio (Bahasa Indonesia), claro e natural."
    },
    "vi": {
        "nome": "Vietnamita",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Vietnamita padrão, claro e respeitoso."
    },
    "ms": {
        "nome": "Malaio",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Malaio padrão, claro e natural."
    },
}

def obter_instrucao_idioma(codigo_idioma):
    """Retorna a instrução correta para o idioma especificado."""
    return IDIOMAS_SUPORTADOS.get(codigo_idioma.lower(), {}).get("instrucao", "")

