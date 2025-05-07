import os
import json
import numpy as np
from pathlib import Path
from annoy import AnnoyIndex
from sentence_transformers import SentenceTransformer

# Caminhos e configurações
BASE_DIR = Path("data_midia")
INDEX_DIR = BASE_DIR / "index_annoy"
INDEX_DIR.mkdir(parents=True, exist_ok=True)

MAP_FILE = INDEX_DIR / "index_map.json"
ANNOY_FILE = INDEX_DIR / "index.ann"

EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".webp"}
EXTENSOES_VIDEO = {".mp4", ".webm", ".mov", ".mkv"}

modelo = SentenceTransformer("all-MiniLM-L6-v2")
VECTOR_SIZE = 384  # Dimensão do embedding

def carregar_index():
    if MAP_FILE.exists():
        with open(MAP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_index(index_map):
    with open(MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(index_map, f, indent=4, ensure_ascii=False)
    print(f"🗂️ Index atualizado: {MAP_FILE}")

def processar_midia(diretorio_tipo, tipo, index_map, annoy_index, proximo_id):
    for subpasta in Path(diretorio_tipo).rglob("*"):
        if not subpasta.is_dir():
            continue

        for arquivo in subpasta.iterdir():
            if not arquivo.is_file():
                continue

            if arquivo.suffix.lower() not in EXTENSOES_IMAGEM.union(EXTENSOES_VIDEO):
                continue

            # Checar se já existe no index
            if any(str(arquivo.resolve()) == v["caminho"] for v in index_map.values()):
                continue

            json_path = arquivo.with_suffix(".json")
            npy_path = arquivo.with_suffix(".npy")

            if not json_path.exists() or not npy_path.exists():
                print(f"⚠️ Pulando {arquivo.name}, falta .json ou .npy")
                continue

            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                descricao = dados.get("descricao", "").strip()
                if not descricao:
                    print(f"⚠️ Pulando {arquivo.name}, descrição vazia.")
                    continue

                vetor = np.load(npy_path).astype("float32")
                if vetor.ndim == 2:
                    vetor = vetor[0]

                annoy_index.add_item(proximo_id, vetor)

                index_map[str(proximo_id)] = {
                    "tipo": tipo,
                    "caminho": str(arquivo.resolve()),
                    "descricao": descricao
                }
                proximo_id += 1

            except Exception as e:
                print(f"❌ Erro com {arquivo.name}: {e}")

    return proximo_id

def iniciar_indexador():
    print("🔍 Iniciando indexação vetorial com Annoy...")

    index_map = carregar_index()
    proximo_id = max([int(k) for k in index_map.keys()], default=-1) + 1
    annoy_index = AnnoyIndex(VECTOR_SIZE, "angular")

    proximo_id = processar_midia(BASE_DIR / "imagens", "imagem", index_map, annoy_index, proximo_id)
    proximo_id = processar_midia(BASE_DIR / "videos", "video", index_map, annoy_index, proximo_id)

    if annoy_index.get_n_items() > 0:
        annoy_index.build(10)
        annoy_index.save(str(ANNOY_FILE))
        print(f"✅ Índice vetorial salvo: {ANNOY_FILE}")
    else:
        print("⚠️ Nenhum vetor foi adicionado ao índice.")

    salvar_index(index_map)

if __name__ == "__main__":
    iniciar_indexador()
