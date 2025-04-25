import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("❌ OPENAI_API_KEY não encontrada no .env")

client = OpenAI(api_key=api_key)

def gerar_topicos(canal, video_id, log=print):
    log(f"🗂️ Gerando tópicos para {canal}/{video_id}...")

    video_path = Path("data") / canal / video_id
    control_path = video_path / "control"

    transcript_path = control_path / "transcript_original.json"
    topicos_path = control_path / "topicos.txt"  # Mude para .txt

    if topicos_path.exists():
        log(f"⚠️ Tópicos já existentes para {canal}/{video_id}.")
        return True

    if not transcript_path.exists():
        log(f"❌ Transcrição original não encontrada em {transcript_path}")
        return False

    with open(transcript_path, "r", encoding="utf-8") as f:
        transcricao_original = json.load(f)

    canal_config_path = Path("db") / "canais" / f"{canal}.json"
    if not canal_config_path.exists():
        log(f"❌ Configuração do canal não encontrada em {canal_config_path}")
        return False

    with open(canal_config_path, "r", encoding="utf-8") as f:
        canal_config = json.load(f)
        prompt_topicos = canal_config.get("prompt_topicos", "").strip()

    if not prompt_topicos:
        log(f"❌ Prompt de tópicos não definido para o canal {canal}.")
        return False

    prompt_final = f"""
{prompt_topicos}

Transcrição completa do vídeo para referência:
{transcricao_original}

⚠️ IMPORTANTE: Gere exatamente no formato abaixo, sem comentários extras, seguindo obrigatoriamente a quantidade de tópicos solicitada (nem mais, nem menos):

Topico 01: "TÍTULO IMPACTANTE E PERSUASIVO DO TÓPICO 01"
RESUMO: "Uma descrição detalhada e clara sobre o conteúdo específico do Tópico 01."

Topico 02: "TÍTULO IMPACTANTE E PERSUASIVO DO TÓPICO 02"
RESUMO: "Uma descrição detalhada e clara sobre o conteúdo específico do Tópico 02."

Topico 03: "TÍTULO IMPACTANTE E PERSUASIVO DO TÓPICO 03"
RESUMO: "Uma descrição detalhada e clara sobre o conteúdo específico do Tópico 03."

... (Continue exatamente nesse formato até completar o número exato de tópicos solicitados)
"""

    try:
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt_final}],
            temperature=0.7,
        )

        topicos_gerados = resposta.choices[0].message.content.strip()

        # Salvar tópicos gerados diretamente como texto puro (.txt)
        with open(topicos_path, "w", encoding="utf-8") as f:
            f.write(topicos_gerados)

        log(f"✅ Tópicos salvos em {topicos_path}")
        return True

    except Exception as e:
        log(f"❌ Erro ao gerar tópicos: {e}")
        return False
