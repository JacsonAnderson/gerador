import os
import re
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Carregar API_KEY do .env
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
    topicos_json_path = control_path / "topicos.json"

    if topicos_json_path.exists():
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

    # Monta o prompt final
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
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt_final}],
            temperature=0.4,
        )

        texto_topicos = resposta.choices[0].message.content.strip()

        # Expressão para capturar número, título e resumo
        padrao = r'Topico\s*(\d+):\s*"([^"]+)"\s*RESUMO:\s*"([^"]+)"'
        topicos_encontrados = re.findall(padrao, texto_topicos, re.IGNORECASE)

        if not topicos_encontrados:
            log(f"⚠️ Nenhum tópico detectado no texto gerado.")
            return False

        lista_topicos = []
        for numero, titulo, resumo in topicos_encontrados:
            lista_topicos.append({
                "numero": int(numero),
                "titulo": titulo.strip(),
                "resumo": resumo.strip()
            })

        # Salva no formato JSON estruturado
        with open(topicos_json_path, "w", encoding="utf-8") as f:
            json.dump({"topicos": lista_topicos}, f, indent=4, ensure_ascii=False)

        log(f"✅ Tópicos salvos em {topicos_json_path}")
        return True

    except Exception as e:
        log(f"❌ Erro ao gerar tópicos: {e}")
        return False
