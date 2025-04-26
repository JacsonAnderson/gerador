import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from app_roteiro.modulo_idioma import obter_instrucao_idioma

# Carregar API_KEY do arquivo .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("❌ OPENAI_API_KEY não encontrada no .env")

client = OpenAI(api_key=api_key)

def gerar_introducao(canal, video_id, log=print):
    log(f"🎬 Gerando introdução para {canal}/{video_id}...")

    control_path = Path("data") / canal / video_id / "control"
    topicos_path = control_path / "topicos.json"
    introducao_path = control_path / "introducao.txt"
    canal_config_path = Path("db") / "canais" / f"{canal}.json"

    if introducao_path.exists():
        log(f"⚠️ Introdução já existente para {canal}/{video_id}.")
        return True

    if not topicos_path.exists():
        log(f"❌ Arquivo de tópicos não encontrado em {topicos_path}.")
        return False

    if not canal_config_path.exists():
        log(f"❌ Arquivo de configuração do canal não encontrado em {canal_config_path}.")
        return False

    # Corrigido para carregar o JSON
    with open(topicos_path, "r", encoding="utf-8") as f:
        topicos_json = json.load(f)

    # Monta o texto dos tópicos para usar no prompt
    topicos = ""
    for topico in topicos_json.get("topicos", []):
        topicos += f'- {topico["titulo"]}: {topico["resumo"]}\n'

    with open(canal_config_path, "r", encoding="utf-8") as f:
        canal_config = json.load(f)
        idioma_configurado = canal_config.get("idioma", "").lower()

    # Pega a instrução correta do idioma
    instrucoes_idioma = obter_instrucao_idioma(idioma_configurado)

    prompt = f"""
Você é um especialista em criação de introduções para vídeos de YouTube, focadas em **captar imediatamente a atenção emocional e racional do público**, sem utilizar frases genéricas, místicas ou vagas.

Sua missão é criar uma introdução curta (máximo 200 palavras) para o canal "{canal}", considerando os tópicos apresentados abaixo, de forma a:

- Entrar diretamente na dor, no desejo ou na necessidade real que o público enfrenta.
- Despertar uma sensação urgente e genuína de identificação e esperança.
- Deixar claro, de forma sutil e emocional, que o conteúdo do vídeo trará respostas práticas, reveladoras ou transformadoras, alinhadas com as expectativas da audiência.
- Utilizar uma linguagem emocionalmente intensa, **sem abstrações vagas, sem metáforas genéricas, sem textos poéticos irreais**.
- Utilizar frases fortes, específicas, diretas e com peso emocional — como se estivesse falando com uma pessoa que realmente precisa daquele conteúdo.
- Manter o fluxo natural e fluido, **sem soar como abertura formal de vídeo** e **sem finalização explícita**.

⚠️ **Proibições obrigatórias**:
- NÃO usar frases como "Em um rincón do universo...", "Hoje vamos falar sobre...", "Neste vídeo você verá...", "Prepare-se para...", "Acompanhe até o final", etc.
- NÃO mencionar métodos, técnicas, marketing, ou conceitos metalinguísticos.
- NÃO escrever de forma genérica, mística vaga, ou fantasiosa.
- NÃO utilizar comandos ou chamadas diretas à ação.

Use os tópicos abaixo como referência direta para construir uma abertura emocionalmente forte, **sem citá-los literalmente**:

Tópicos do Vídeo:
{topicos}

{instrucoes_idioma}

📝 Crie agora a introdução: curta, impactante, emocionalmente envolvente e naturalmente fluida.
"""


    try:
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
        )

        introducao_gerada = resposta.choices[0].message.content.strip()

        with open(introducao_path, "w", encoding="utf-8") as f:
            f.write(introducao_gerada)

        log(f"✅ Introdução salva em {introducao_path}")
        return True

    except Exception as e:
        log(f"❌ Erro ao gerar introdução: {e}")
        return False
