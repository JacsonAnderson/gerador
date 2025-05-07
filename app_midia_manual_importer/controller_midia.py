import os
import json
import shutil
import time
from pathlib import Path
from tkinter import Tk, filedialog
from PIL import Image
import av
import cv2
import numpy as np
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
from sentence_transformers import SentenceTransformer
from annoy import AnnoyIndex

# Configurações
EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".webp"}
EXTENSOES_VIDEO = {".mp4", ".webm", ".mov", ".mkv"}
DESTINO_BASE = Path("data_midia")
MAX_MIDIAS_POR_PASTA = 100
RESOLUCAO_PADRAO = (1920, 1080)
VECTOR_SIZE = 384

# Modelos
device = "cuda" if torch.cuda.is_available() else "cpu"
blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base", use_fast=False)
blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(device)
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def escolher_pasta():
    Tk().withdraw()
    return filedialog.askdirectory(title="Selecione uma pasta com mídias")

def classificar_tipo(extensao):
    ext = extensao.lower()
    if ext in EXTENSOES_IMAGEM:
        return "imagens"
    elif ext in EXTENSOES_VIDEO:
        return "videos"
    return None

def contar_midias(pasta, tipo):
    prefixo = "img_" if tipo == "imagens" else "vid_"
    extensao = ".webp" if tipo == "imagens" else ".mp4"
    return len(list(pasta.glob(f"{prefixo}*{extensao}")))

def gerar_subpasta(tipo):
    base_path = DESTINO_BASE / tipo
    base_path.mkdir(parents=True, exist_ok=True)
    subpastas = sorted([p for p in base_path.iterdir() if p.is_dir()])
    for sub in subpastas:
        if contar_midias(sub, tipo) < MAX_MIDIAS_POR_PASTA:
            return sub
    nova = base_path / f"{chr(97 + len(subpastas))}0"
    nova.mkdir(parents=True, exist_ok=True)
    return nova

def gerar_nome(subpasta, tipo, extensao):
    prefixo = "img" if tipo == "imagens" else "vid"
    existentes = list(subpasta.glob(f"{prefixo}_*.{extensao.strip('.')}"))
    numero = len(existentes) + 1
    return f"{prefixo}_{numero:04d}{extensao}"

def gerar_descricao_blip_path(imagem_path):
    imagem = Image.open(imagem_path).convert("RGB")
    return gerar_descricao_blip_pil(imagem)

def gerar_descricao_blip_pil(imagem_pil):
    inputs = blip_processor(imagem_pil, return_tensors="pt").to(device)
    with torch.no_grad():
        saida = blip_model.generate(**inputs, max_new_tokens=50)
    return blip_processor.decode(saida[0], skip_special_tokens=True).strip()

def gerar_embedding(texto):
    return embedding_model.encode(texto)

def salvar_json_e_npy(path_midia, descricao):
    json_path = path_midia.with_suffix(".json")
    npy_path = path_midia.with_suffix(".npy")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"descricao": descricao}, f, indent=4, ensure_ascii=False)
    np.save(npy_path, gerar_embedding(descricao))

def processar_imagem(origem, destino):
    try:
        img = Image.open(origem).convert("RGB")
        img = img.resize(RESOLUCAO_PADRAO, Image.LANCZOS)
        destino = destino.with_suffix(".webp")
        img.save(destino, "WEBP", quality=85)
        descricao = gerar_descricao_blip_path(destino)
        salvar_json_e_npy(destino, descricao)
        print(f"🖼️ {destino.name} | {descricao}")
    except Exception as e:
        print(f"❌ Erro imagem {origem.name}: {e}")

def processar_video(origem, destino):
    try:
        container = av.open(str(origem))
        stream = container.streams.video[0]
        fps = float(stream.average_rate)
        max_frames = int(fps * 8)
        frames = []
        frame_descricao = None
        for i, frame in enumerate(container.decode(video=0)):
            if i >= max_frames:
                break
            img = frame.to_ndarray(format="bgr24")
            img = cv2.resize(img, RESOLUCAO_PADRAO, interpolation=cv2.INTER_AREA)
            frames.append(img)
            if i == int(fps * 2):
                frame_descricao = img
        destino_temp = str(destino.with_suffix(".temp.mp4"))
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(destino_temp, fourcc, fps, RESOLUCAO_PADRAO)
        for f in frames:
            out.write(f)
        out.release()
        shutil.move(destino_temp, destino)
        if frame_descricao is not None:
            img_pil = Image.fromarray(cv2.cvtColor(frame_descricao, cv2.COLOR_BGR2RGB))
            descricao = gerar_descricao_blip_pil(img_pil)
            salvar_json_e_npy(destino, descricao)
            print(f"🎥 {destino.name} | {descricao}")
        else:
            print(f"⚠️ Nenhum frame disponível para descrição: {origem.name}")
    except Exception as e:
        print(f"❌ Erro vídeo {origem.name}: {e}")

def copiar_arquivos(pasta_origem):
    arquivos = os.listdir(pasta_origem)
    total = 0
    for nome in arquivos:
        caminho = Path(pasta_origem) / nome
        if not caminho.is_file():
            continue
        tipo = classificar_tipo(caminho.suffix)
        if not tipo:
            continue
        subpasta = gerar_subpasta(tipo)
        extensao = ".webp" if tipo == "imagens" else ".mp4"
        nome_final = gerar_nome(subpasta, tipo, extensao)
        destino = subpasta / nome_final
        if destino.exists():
            print(f"⚠️ Já existe: {destino}")
            continue
        if tipo == "imagens":
            processar_imagem(caminho, destino)
        elif tipo == "videos":
            processar_video(caminho, destino)
        total += 1
    print(f"\n📦 Total de mídias processadas e salvas: {total}")

def rodar_indexador_annoy():
    from annoy import AnnoyIndex
    BASE_DIR = Path("data_midia")
    INDEX_DIR = BASE_DIR / "index_annoy"
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    MAP_FILE = INDEX_DIR / "index_map.json"
    ANNOY_FILE = INDEX_DIR / "index.ann"
    EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".webp"}
    EXTENSOES_VIDEO = {".mp4", ".webm", ".mov", ".mkv"}

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
                if any(str(arquivo.resolve()) == v["caminho"] for v in index_map.values()):
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
                proximo_id += 1
        return proximo_id

    print("\n🔍 Iniciando geração de index ANN...")
    index_map = carregar_index()
    proximo_id = max([int(k) for k in index_map.keys()], default=-1) + 1
    annoy_index = AnnoyIndex(VECTOR_SIZE, "angular")
    proximo_id = processar_midia(BASE_DIR / "imagens", "imagem", index_map, annoy_index, proximo_id)
    proximo_id = processar_midia(BASE_DIR / "videos", "video", index_map, annoy_index, proximo_id)
    if annoy_index.get_n_items() > 0:
        annoy_index.build(10)
        annoy_index.save(str(ANNOY_FILE))
        print(f"✅ Index salvo em: {ANNOY_FILE}")
    else:
        print("⚠️ Nenhum vetor adicionado.")
    salvar_index(index_map)

def iniciar_importador():
    pasta = escolher_pasta()
    if pasta:
        copiar_arquivos(pasta)
        rodar_indexador_annoy()

if __name__ == "__main__":
    iniciar_importador()
