import os
import json
import time
import re
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Carrega a chave da API do arquivo .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

DATA_DIR = "data"
SEGMENTOS_FILE_NAME = "segmentos.json"

def gerar_descricao(texto):
    prompt = (
        "You are an expert in video production.\n"
        "Given a short spoken sentence from a video narration, generate a unique and visual search tag (max 8 words) "
        "to help find matching stock video footage.\n"
        "Each tag must describe a distinct, realistic visual scene or action, avoiding repetition and vagueness.\n"
        "If the sentence is too abstract, imagine what visuals best represent it.\n"
        "Reply only with the visual tag in English.\n"
        f"\nTranscript:\n\"{texto}\"\n\n"
        "Search Tag:"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=60
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Erro na API: {e}")
        return None

def dividir_texto_proporcional(texto, total, index):
    palavras = texto.strip().split()
    qtd = len(palavras)
    por_bloco = max(1, qtd // total)
    inicio = por_bloco * index
    fim = por_bloco * (index + 1) if index < total - 1 else qtd
    return " ".join(palavras[inicio:fim])

def salvar_temporario(segmentos_path, data):
    with open(segmentos_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"💾 Progresso salvo: {segmentos_path}")

def processar_segmentos(segmentos_path):
    print(f"\n📄 Lendo: {segmentos_path}")
    with open(segmentos_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    alterado = False
    segmentos = data.get("segments", [])
    texto_map = {}
    for s in segmentos:
        t = s["text"]
        texto_map.setdefault(t, []).append(s)

    contador = 0

    for idx, segmento in enumerate(segmentos):
        if segmento.get("descricao_chave"):
            continue

        texto = segmento["text"]
        lista_repetidos = texto_map[texto]
        index_no_grupo = lista_repetidos.index(segmento)
        total_repetidos = len(lista_repetidos)
        subtexto = dividir_texto_proporcional(texto, total_repetidos, index_no_grupo)

        descricao = gerar_descricao(subtexto)
        if descricao:
            segmento["descricao_chave"] = descricao
            alterado = True
            contador += 1
            print(f"🧠 {idx + 1}: {descricao}")
            time.sleep(1.2)

            if contador % 10 == 0:
                salvar_temporario(segmentos_path, data)

        else:
            print(f"⚠️ Segmento {idx + 1} falhou.")

    if alterado:
        salvar_temporario(segmentos_path, data)
        print(f"✅ Segmentos atualizados em: {segmentos_path}")
    else:
        print("⏩ Nenhuma alteração feita.")

def buscar_segmentos():
    print("\n🔍 Buscando arquivos de segmentos para gerar descrições...")
    for canal in os.listdir(DATA_DIR):
        caminho_canal = Path(DATA_DIR) / canal
        if not caminho_canal.is_dir():
            continue

        for video in os.listdir(caminho_canal):
            if not video.isdigit():
                continue

            pasta_control = caminho_canal / video / "control"
            segmentos_path = pasta_control / SEGMENTOS_FILE_NAME

            if segmentos_path.exists():
                processar_segmentos(segmentos_path)
            else:
                print(f"❌ Segmentos não encontrados: {segmentos_path}")

if __name__ == "__main__":
    buscar_segmentos()
