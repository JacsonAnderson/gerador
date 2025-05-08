import json
import numpy as np
from pathlib import Path
from annoy import AnnoyIndex

# Configurações
VECTOR_SIZE = 384
BASE_DIR = Path("data_midia")
INDEX_DIR = BASE_DIR / "index_annoy"
INDEX_DIR.mkdir(parents=True, exist_ok=True)
MAP_FILE = INDEX_DIR / "index_map.json"
ANNOY_FILE = INDEX_DIR / "index.ann"
EXTENSOES_IMAGEM = {".webp"}
EXTENSOES_VIDEO = {".mp4", ".mov", ".mkv", ".webm"}

def salvar_index(index_map):
    with open(MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(index_map, f, indent=4, ensure_ascii=False)
    print(f"✅ Index salvo: {MAP_FILE}")

def processar_midia(diretorio_tipo, tipo, index_map, annoy_index, proximo_id):
    for subpasta in Path(diretorio_tipo).rglob("*"):
        if not subpasta.is_dir():
            continue
        for arquivo in subpasta.iterdir():
            if not arquivo.is_file():
                continue
            if arquivo.suffix.lower() not in EXTENSOES_IMAGEM.union(EXTENSOES_VIDEO):
                continue
            json_path = arquivo.with_suffix(".json")
            npy_path = arquivo.with_suffix(".npy")
            if not json_path.exists() or not npy_path.exists():
                continue
            with open(json_path, "r", encoding="utf-8") as f:
                dados = json.load(f)
            descricao = dados.get("descricao", "").strip()
            if not descricao:
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
            print(f"🔄 Adicionado ID {proximo_id}: {arquivo.name}")
            proximo_id += 1
    return proximo_id

def rodar_indexador_annoy():
    index_map = {}
    annoy_index = AnnoyIndex(VECTOR_SIZE, "angular")
    proximo_id = 0

    print("🔍 Processando imagens...")
    proximo_id = processar_midia(BASE_DIR / "imagens", "imagem", index_map, annoy_index, proximo_id)

    print("🎥 Processando vídeos...")
    proximo_id = processar_midia(BASE_DIR / "videos", "video", index_map, annoy_index, proximo_id)

    if annoy_index.get_n_items() > 0:
        print("🛠️ Construindo Annoy index...")
        annoy_index.build(10)
        annoy_index.save(str(ANNOY_FILE))
        salvar_index(index_map)
        print(f"✅ Index reconstruído com sucesso. Total: {annoy_index.get_n_items()} itens.")
    else:
        print("⚠️ Nenhum item foi indexado.")

if __name__ == "__main__":
    rodar_indexador_annoy()
