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
# 1) Carregamento de configs direto do SQLite e Carrega idioma do canal direto do SQLite (channels.db)
# ------------------------------------------------------------------
VIDEOS_DB_PATH = Path("data/videos.db")
CHANNELS_DB_PATH = Path("data/channels.db")


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

def _carregar_idioma_canal(canal: str) -> str:
    """
    Busca a coluna 'idioma' na tabela 'canais' para o nome do canal fornecido.
    Retorna o código do idioma (ex: 'pt', 'es', 'en', ...), ou '' se não encontrar.
    """
    try:
        with sqlite3.connect(CHANNELS_DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT idioma FROM canais WHERE nome = ?", (canal,))
            row = cur.fetchone()
        return row[0] if row and row[0] else ""
    except Exception:
        return ""

def obter_instrucao_idioma(codigo_idioma):
    """Retorna a instrução correta para o idioma especificado."""
    return IDIOMAS_SUPORTADOS.get(codigo_idioma.lower(), {}).get("instrucao", "")

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

    log_callback(f"  ✅ Baixando legendas de: {url}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            yt_id = info['id']
            log_callback(f"  ✅ YouTube ID detectado: {yt_id}")
        except Exception as e:
            log_callback(f"  ⚠️ Erro no extract_info: {e}")
            return None, None

    # coleta todos os VTTs
    vtt_files = list(Path(pasta_destino).glob(f"{yt_id}.*.vtt"))
    log_callback(f"  ✅ VTTs baixados: {[f.name for f in vtt_files]}")

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
        log_callback(f"  ⚠️ Sem prioridade, usando: {escolhida.name}")

    if not escolhida:
        log_callback("  ⚠️ Nenhum VTT encontrado.")
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
    log_callback(f"  ✅ Texto extraído: {len(transcricao)} chars")

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
        log_callback(f"  ⚠️ Transcrição não encontrada em {transcript}")
        return False
    if not meta_path.exists():
        log_callback(f"  ⚠️ metadados.json não encontrado em {meta_path}")
        return False

    # carrega transcrição limpa
    dados_trans = json.loads(transcript.read_text(encoding="utf-8"))
    txt = dados_trans.get("transcricao_limpa") if isinstance(dados_trans, dict) else ""
    if not txt or not txt.strip():
        log_callback("  ⚠️ Transcrição vazia.")
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

        log_callback(f"  ✅ Resumo salvo em {meta_path}")
        return True

    except Exception as e:
        log_callback(f"  ⚠️ Erro ao gerar resumo: {e}")
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
        log_callback("  ✅ Tópicos já existem em metadados.json. Pulando.")
        return True

    # 2) transcript ok?
    if not transcript_p.exists():
        log_callback("  ⚠️ Transcrição não encontrada. Não foi possível gerar tópicos.")
        return False
    dados = json.loads(transcript_p.read_text(encoding="utf-8"))
    txt   = dados.get("transcricao_limpa", "") if isinstance(dados, dict) else ""
    if not txt.strip():
        log_callback("  ⚠️ Transcrição vazia. Não foi possível gerar tópicos.")
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
        log_callback("  ⚠️ prompt_topicos não definido. Não foi possível gerar tópicos.")
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
        model="gpt-4o",
        messages=[{"role":"user","content":prompt_final}],
        temperature=0.4
    )
    out = resp.choices[0].message.content.strip()

    pad   = r'[Tt][oó]pico\s*(\d+):\s*"([^"]+)"\s*RESUMO:\s*"([^"]+)"'
    found = re.findall(pad, out, re.IGNORECASE)
    if not found:
        log_callback("  ⚠️ Nenhum tópico detectado pela regex.")
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


# ------------------------------------------------------------------
# 6) Gerar introdução e injetar em metadados.json
# ------------------------------------------------------------------
def gerar_introducao(canal: str, video_id: str) -> bool:
    """
    Gera uma introdução curta e impactante a partir dos tópicos em metadados.json
    e injeta esse texto na chave "introducao" dentro de data/{canal}/{video_id}/control/metadados.json.
    """
    control_dir = Path("data") / canal / video_id / "control"
    meta_path   = control_dir / "metadados.json"

    # 1) pré-requisitos
    if not meta_path.exists():
        log_callback(f"  ⚠️ metadados.json não encontrado em {meta_path}")
        return False

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("introducao"):
        log_callback("  ✅ Introdução já existe em metadados.json. Pulando.")
        return True

    topicos = meta.get("topicos")
    if not topicos or not isinstance(topicos, list):
        log_callback("  ⚠️ Tópicos não encontrados em metadados.json. Não foi possível gerar introdução.")
        return False

    # 2) monta a lista de tópicos para o prompt
    lista_markdown = "".join(f"- {t['titulo']}: {t['resumo']}\n" for t in topicos)

    # 3) resolve idioma: primeiro do vídeo, senão do canal
    cfg           = _carregar_configs(canal, video_id)
    idioma_video  = (cfg.get("idioma") or "").lower()
    idioma_canal  = _carregar_idioma_canal(canal).lower()
    idioma        = idioma_video or idioma_canal or "pt"
    inst_id       = obter_instrucao_idioma(idioma)

    # 4) monta o prompt
    prompt = f"""
Você é um especialista em criação de introduções altamente persuasivas e emocionalmente impactantes para vídeos de YouTube. Seu trabalho é capturar imediatamente a atenção do público e gerar um forte desejo de continuar assistindo, usando frases que toquem nas dores reais, nos desejos ocultos e nas promessas transformadoras que o vídeo pode entregar.

Sua missão é criar uma introdução curta (máximo 150 palavras) para o canal "{canal}", baseada nos tópicos abaixo, respeitando as diretrizes obrigatórias:

⚡ Diretrizes obrigatórias:
- A primeira frase deve **impactar diretamente o emocional ou o racional do espectador em menos de 5 segundos**, com uma dor, desejo ou pergunta instigante.
- A introdução deve criar uma **conexão real com o público**, fazendo com que ele se sinta compreendido em sua dor, ansiedade, dúvida ou busca pessoal.
- Em seguida, apresente **uma promessa concreta**, uma transformação que será abordada no vídeo — **sem soar como técnica de marketing**, mas com **autoridade natural** e tom de revelação importante.
- Finalize com uma **frase fluida e emocional**, sem dar fechamento ou comandos explícitos — apenas mantendo a tensão emocional viva, como um gancho natural que conduz ao próximo conteúdo.

📌 Linguagem:
- Escreva com frases fortes, curtas, emocionalmente vívidas e específicas.
- Fale com **clareza**, **urgência emocional**, **sem abstrações**, **sem metáforas místicas** e **sem floreios poéticos genéricos**.
- Parece uma conversa sincera com alguém que realmente precisa ouvir isso — e **não** uma abertura formal de vídeo.

🚫 Proibições obrigatórias:
- **NÃO** use frases como: “Neste vídeo você verá…”, “Hoje falaremos sobre…”, “Em um rincón do universo…”, “Prepare-se para…”, “Acompanhe até o final…”.
- **NÃO** mencione técnicas, métodos, sistemas, estratégias, marketing, nem qualquer termo metalinguístico.
- **NÃO** escreva de forma genérica, mística, vaga, motivacional de autoajuda ou fantasiosa.
- **NÃO** finalize o texto com frases de encerramento. A introdução deve ser como um “gancho emocional” que leva direto para o primeiro tópico do vídeo.

Use os tópicos abaixo como referência **sem copiá-los literalmente**, para construir uma introdução intensa e altamente persuasiva:

📋 **Tópicos do Vídeo (não copie literalmente, use como base):**
{lista_markdown}

{inst_id}

📝 Crie agora a introdução: curta, impactante, emocionalmente envolvente, com promessa clara, sem encerramento explícito e com um gancho natural que leve ao primeiro conteúdo.
"""

    # 5) chama a API
    try:
        resp = _client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
        )
        introducao = resp.choices[0].message.content.strip()

        # 6) injeta e salva
        meta["introducao"] = introducao
        meta_path.write_text(
            json.dumps(meta, ensure_ascii=False, indent=4),
            encoding="utf-8"
        )

        log_callback("  ✅ Introdução salva em metadados.json. Pulando.")
        return True

    except Exception as e:
        log_callback(f"  ⚠️ Erro ao gerar introdução: {e}")
        return False



# ------------------------------------------------------------------
# 6) Gerar conteúdos dos tópicos e injetar em metadados.json
# ------------------------------------------------------------------
def gerar_conteudos_topicos(canal: str, video_id: str) -> bool:
    """
    Para cada tópico em metadados.json gera o bloco narrativo correspondente
    e injeta tudo na chave "conteudos" dentro de data/{canal}/{video_id}/control/metadados.json.
    """
    control_dir = Path("data") / canal / video_id / "control"
    meta_path   = control_dir / "metadados.json"

    # 1) pré-requisitos
    if not meta_path.exists():
        log_callback(f"  ⚠️ metadados.json não encontrado em {meta_path}")
        return False
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    # 2) pula se já gerado
    if meta.get("conteudos"):
        log_callback("  ✅ Conteúdos já existem em metadados.json. Pulando.")
        return True

    # 3) checa os dados básicos
    topicos    = meta.get("topicos")
    resumo     = meta.get("resumo", "")
    introducao = meta.get("introducao", "")
    if not topicos or not isinstance(topicos, list):
        log_callback("  ⚠️ Tópicos ausentes em metadados.json. Não foi possível gerar conteúdos.")
        return False
    if not resumo:
        log_callback("  ⚠️ Resumo ausente em metadados.json. Não foi possível gerar conteúdos.")
        return False
    if not introducao:
        log_callback("  ⚠️ Introdução ausente em metadados.json. Não foi possível gerar conteúdos.")
        return False

    # 4) carrega prompt_base de data/{canal}/prompts.json
    prompts_file = Path("data") / canal / "prompts.json"
    if not prompts_file.exists():
        log_callback("  ⚠️ prompts.json não encontrado no canal. Não foi possível gerar conteúdos.")
        return False
    j = json.loads(prompts_file.read_text(encoding="utf-8"))
    prompt_base = j.get("prompt_roteiro", "").strip()
    if not prompt_base:
        log_callback("  ⚠️ prompt_roteiro não definido em prompts.json. Não foi possível gerar conteúdos.")
        return False

    # 5) instrução de idioma: primeiro do vídeo, senão do canal
    cfg          = _carregar_configs(canal, video_id)
    idioma_video = (cfg.get("idioma") or "").lower()
    idioma_canal = _carregar_idioma_canal(canal).lower()
    idioma       = idioma_video or idioma_canal or "pt"
    inst_idioma  = obter_instrucao_idioma(idioma)
    nome_idioma  = IDIOMAS_SUPORTADOS.get(idioma, {}).get("nome", "Português Brasileiro")

    # 6) monta o prompt completo, reforçando uso do idioma do canal
    prompt = (
        f"⚠️ **ATENÇÃO**: Todo o texto abaixo deve ser redigido **exclusivamente em {nome_idioma}**.\n\n"
        f"{inst_idioma}\n\n"
        f"{prompt_base}\n\n"
        f"Contexto geral do vídeo:\n\"{resumo}\"\n\n"
        f"Introdução:\n\"{introducao}\"\n\n"
        "Agora, para cada um dos tópicos abaixo, gere o conteúdo narrativo específico, "
        "sem encerrar o raciocínio e mantendo a fluidez emocional:\n\n"
    )
    for t in topicos:
        prompt += (
            f"---\n"
            f"Tópico {t['numero']}: {t['titulo']}\n"
            f"Contexto do tópico: {t['resumo']}\n\n"
        )
    prompt += (
        "📝 Gere agora o roteiro completo, parte a parte:\n"
        "⚠️ IMPORTANTE: Cada bloco deve começar numa nova linha exatamente como “Tópico XX: Título do tópico” "
        "e, no parágrafo seguinte, vir o conteúdo. Não use bullets, numeração alternativa nem variações de hífen."
    )

    # 7) chama a API
    try:
        resp = _client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
        )
        out = resp.choices[0].message.content.strip()
    except Exception as e:
        log_callback(f"  ⚠️ Erro ao chamar OpenAI para conteúdos: {e}")
        return False

    # 8) extrai blocos via regex
    pattern = re.compile(
        r'''(?m)                       # modo multilinha
        ^\s*                           # início da linha, espaços
        (?:[Tt][óo]pico)\s*(\d+)[\s:\-–]+   # “Tópico N:” ou “Tópico N-”
        (.+?)\r?\n                     # título até quebra de linha
        ([\s\S]*?)(?=                  # bloco até
            ^\s*(?:[Tt][óo]pico)\s*\d+ # próximo tópico
            |\Z                        # ou fim do texto
        )''', re.IGNORECASE|re.VERBOSE
    )
    matches = pattern.findall(out)
    if not matches:
        log_callback("  ⚠️ Nenhum bloco de conteúdo detectado pela regex.")
        return False

    # 9) formata e salva
    conteudos = []
    for num, titulo, texto in matches:
        conteudos.append({
            "numero": int(num),
            "titulo": titulo.strip(),
            "conteudo": texto.strip()
        })

    meta["conteudos"] = conteudos
    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=4),
        encoding="utf-8"
    )

    log_callback("  ✅ Conteúdos salvos em metadados.json.")
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


