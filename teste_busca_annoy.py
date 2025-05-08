import json
import numpy as np
from pathlib import Path
from annoy import AnnoyIndex
from sentence_transformers import SentenceTransformer, util
import torch

# Configurações
INDEX_DIR = Path("data_midia/index_annoy")
MAP_FILE = INDEX_DIR / "index_map.json"
ANNOY_FILE = INDEX_DIR / "index.ann"
VECTOR_SIZE = 384

# Carrega mapeamento
with open(MAP_FILE, "r", encoding="utf-8") as f:
    index_map = json.load(f)

# Carrega índice Annoy
ann_index = AnnoyIndex(VECTOR_SIZE, "angular")
ann_index.load(str(ANNOY_FILE))

# Modelo e dispositivo
modelo = SentenceTransformer("all-MiniLM-L6-v2")
device = "cuda" if torch.cuda.is_available() else "cpu"

# Entrada do usuário
consulta = input("🔍 Digite sua busca: ").strip()
embedding = modelo.encode(consulta, convert_to_tensor=True).to(device)

# Busca preliminar com Annoy
ids, distancias = ann_index.get_nns_by_vector(embedding.cpu().numpy(), 100, include_distances=True)

# Avalia com similaridade real
resultados = []
for id_, distancia in zip(ids, distancias):
    item = index_map.get(str(id_))
    if not item:
        continue
    caminho_npy = Path(item["caminho"]).with_suffix(".npy")
    if not caminho_npy.exists():
        continue
    vetor = np.load(caminho_npy)
    if vetor.ndim == 2:
        vetor = vetor[0]
    vetor_torch = torch.tensor(vetor).to(device)
    score = util.cos_sim(embedding, vetor_torch).item()
    resultados.append((score, distancia, item))

# Filtra e ordena por maior similaridade real
resultados = [r for r in resultados if r[0] >= 0.45]
resultados.sort(reverse=True, key=lambda x: x[0])

# Exibe resultados
print("\n🎯 Resultados mais similares:")
if not resultados:
    print("Nenhum resultado relevante encontrado.")
else:
    for score, distancia, item in resultados[:10]:
        estrelas = "⭐" * int(score * 10)
        print(f"✅ ID: {list(index_map.keys())[list(index_map.values()).index(item)]}")
        print(f"📁 {item['caminho']}")
        print(f"📝 Descrição: {item.get('descricao', '[sem descrição]')[:120]}...")
        print(f"📏 Similaridade real: {score:.4f} | Distância Annoy: {distancia:.4f} {estrelas}\n")
