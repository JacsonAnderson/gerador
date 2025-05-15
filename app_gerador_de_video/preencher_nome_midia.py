import json
import numpy as np
from pathlib import Path
from annoy import AnnoyIndex
from sentence_transformers import SentenceTransformer

VECTOR_SIZE = 384
SIMILARITY_THRESHOLD = 0.75  # << Reduzido para permitir mais matches

# Caminhos
INDEX_DIR = Path("data_midia/index_annoy")
INDEX_FILE = INDEX_DIR / "index.ann"
MAP_FILE = INDEX_DIR / "index_map.json"

# Modelo
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def carregar_index():
    index = AnnoyIndex(VECTOR_SIZE, "angular")
    index.load(str(INDEX_FILE))
    with open(MAP_FILE, "r", encoding="utf-8") as f:
        index_map = json.load(f)
    return index, index_map

def buscar_midia(descricao, index, index_map):
    emb = embedding_model.encode(descricao).astype("float32")
    ids_proximos = index.get_nns_by_vector(emb, 1, include_distances=True)

    if not ids_proximos[0]:
        return ""

    i, dist = ids_proximos[0][0], ids_proximos[1][0]
    similaridade = 1 - dist / 2  # Conversão angular → cos_sim approx
    caminho = Path(index_map[str(i)]["caminho"])

    if similaridade >= SIMILARITY_THRESHOLD:
        return caminho.name
    else:
        print(f"🔍 Melhor match: {caminho.name} | Similaridade: {similaridade:.2f} (abaixo do threshold)")
    return ""

def preencher_segmentos_json(json_path):
    index, index_map = carregar_index()

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    faltando = []
    alterado = False

    for seg in data.get("segments", []):
        if not seg.get("nome_midia"):
            descricao = seg.get("descricao_chave", "").strip('" ')
            if descricao:
                nome_midia = buscar_midia(descricao, index, index_map)
                if nome_midia:
                    seg["nome_midia"] = nome_midia
                    print(f'✅ Segmento atualizado: "{descricao}" → {nome_midia}')
                    alterado = True
                else:
                    faltando.append(descricao)
                    print(f'⚠️ Nenhuma mídia encontrada para: "{descricao}"')

    if alterado:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"\n💾 Segmentos atualizados em: {json_path}")
    else:
        print("🟡 Nenhuma alteração feita.")

    if faltando:
        control_dir = Path(json_path).parent
        faltando_json = control_dir / "faltando_midias.json"
        with open(faltando_json, "w", encoding="utf-8") as f:
            json.dump({
                "descricao_faltando": faltando,
                "total_faltando": len(faltando)
            }, f, indent=4, ensure_ascii=False)
        print(f"❌ {len(faltando)} segmentos sem mídia salvos em: {faltando_json}")

if __name__ == "__main__":
    caminho_json = input("Caminho para o arquivo de segmentos.json: ").strip('"')
    preencher_segmentos_json(Path(caminho_json))
