import json
import numpy as np
from pathlib import Path
from annoy import AnnoyIndex
from sentence_transformers import SentenceTransformer

VECTOR_SIZE = 384
INDEX_DIR = Path("data_midia/index_annoy")
INDEX_FILE = INDEX_DIR / "index.ann"
MAP_FILE = INDEX_DIR / "index_map.json"
LIMITE_REPETICAO = 3

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def carregar_index():
    index = AnnoyIndex(VECTOR_SIZE, "angular")
    index.load(str(INDEX_FILE))
    with open(MAP_FILE, "r", encoding="utf-8") as f:
        index_map = json.load(f)
    return index, index_map

def buscar_midia_obrigatoria(descricao, index, index_map, usados, max_tentativas=50):
    emb = embedding_model.encode(descricao).astype("float32")
    ids_proximos = index.get_nns_by_vector(emb, max_tentativas, include_distances=True)

    base_videos = Path("data_midia/videos").resolve()

    for i in ids_proximos[0]:
        caminho = Path(index_map[str(i)]["caminho"])
        caminho_relativo = caminho.resolve().relative_to(base_videos)
        chave = str(caminho_relativo)

        if usados.get(chave, 0) < LIMITE_REPETICAO:
            usados[chave] = usados.get(chave, 0) + 1
            return chave
    return None

def preencher_segmentos_obrigatorio(json_path):
    index, index_map = carregar_index()

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    usados = {}
    for seg in data.get("segments", []):
        nome = seg.get("nome_midia", "").strip()
        if nome:
            usados[nome] = usados.get(nome, 0) + 1

    alterado = False
    erros = []

    for seg in data.get("segments", []):
        if not seg.get("nome_midia"):
            descricao = seg.get("descricao_chave", "").strip('" ')
            if descricao:
                nome_midia = buscar_midia_obrigatoria(descricao, index, index_map, usados)
                if nome_midia:
                    seg["nome_midia"] = nome_midia
                    print(f'✅ Segmento: "{descricao}" → {nome_midia}')
                    alterado = True
                else:
                    erros.append(descricao)
                    print(f'❌ ERRO: Todas as mídias próximas atingiram o limite para "{descricao}"')

    if alterado:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"\n💾 Segmentos atualizados: {json_path}")
    else:
        print("⚠️ Nenhuma alteração feita.")

    if erros:
        error_path = Path(json_path).parent / "erros_midias.json"
        with open(error_path, "w", encoding="utf-8") as f:
            json.dump({"falhas": erros}, f, indent=4, ensure_ascii=False)
        print(f"❌ Falhas salvas em: {error_path}")

if __name__ == "__main__":
    caminho_json = input("Caminho para o arquivo de segmentos.json: ").strip('"')
    preencher_segmentos_obrigatorio(Path(caminho_json))
