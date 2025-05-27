import os
import json
import shutil
import time
import msvcrt
import subprocess
import psutil
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
from sentence_transformers import util

# Configurações
EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".webp"}
EXTENSOES_VIDEO = {".mp4", ".webm", ".mov", ".mkv"}
DESTINO_BASE = Path("data_midia")
MAX_MIDIAS_POR_PASTA = 100
RESOLUCAO_PADRAO = (1920, 1080)
VECTOR_SIZE = 384

# Modelos
device = "cuda" if torch.cuda.is_available() else "cpu"
blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large").to(device)
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def escolher_pasta():
    return str(Path(__file__).resolve().parent.parent / "midias_temporais")


def descansar(cpu_limite=85, pausa_segundos=3):
    uso = psutil.cpu_percent(interval=1)
    if uso >= cpu_limite:
        print(f"⏳ CPU em {uso:.1f}%, aguardando {pausa_segundos}s para aliviar...")
        time.sleep(pausa_segundos)


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

def is_similar(new_text, textos_existentes, threshold=0.85):
    if not textos_existentes:
        return False
    emb_novo = embedding_model.encode(new_text, convert_to_tensor=True).to(device)
    emb_existentes = embedding_model.encode(textos_existentes, convert_to_tensor=True).to(device)
    scores = util.cos_sim(emb_novo, emb_existentes)
    return any(score.item() >= threshold for score in scores[0])



def gerar_descricao_blip_pil(imagem_pil):
    prompt = (
        "Describe this scene briefly. Focus on the main subject, visible objects, actions, and the setting. "
        "Avoid unnecessary details. Respond in one short sentence."
    )
    inputs = blip_processor(images=imagem_pil, return_tensors="pt").to(device)
    with torch.no_grad():
        saida = blip_model.generate(
            **inputs,
            num_beams=5,
            length_penalty=0.8,
            max_new_tokens=30,
            do_sample=False
        )
    descricao = blip_processor.decode(saida[0], skip_special_tokens=True).strip()
    return descricao




def gerar_descricao_blip_path(imagem_path):
    imagem = Image.open(imagem_path).convert("RGB")
    return gerar_descricao_blip_pil(imagem)

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
        duracao = float(container.duration * stream.time_base)
        intervalo = 2  # segundos
        proximo_tempo = 0
        frames_descricao = []

        destino_temp = str(destino.with_suffix(".temp.mp4"))
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(destino_temp, fourcc, fps, RESOLUCAO_PADRAO)

        for frame in container.decode(video=0):
            tempo_atual = frame.pts * stream.time_base
            img = frame.to_ndarray(format="bgr24")
            img = cv2.resize(img, RESOLUCAO_PADRAO, interpolation=cv2.INTER_AREA)
            out.write(img)

            if tempo_atual >= proximo_tempo:
                img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                descricao = gerar_descricao_blip_pil(img_pil)
                frames_descricao.append(descricao)
                proximo_tempo += intervalo

        out.release()
        shutil.move(destino_temp, destino)

        if frames_descricao:
            descricao_final = []
            for desc in frames_descricao:
                if not is_similar(desc, descricao_final):
                    descricao_final.append(desc)
            descricao_texto = " ".join(descricao_final)
            salvar_json_e_npy(destino, descricao_texto)
            print(f"🎥 {destino.name} | {descricao_texto}")

        else:
            print(f"⚠️ Nenhum frame útil encontrado para: {origem.name}")

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

        descansar()  # pausa curta após cada arquivo

        if total % 10 == 0:
            print("😮‍💨 Descanso maior de 10 segundos para resfriar CPU...")
            time.sleep(10)

        total += 1
    print(f"\n📦 Total de mídias processadas e salvas: {total}")

def rodar_indexador_annoy():
    BASE_DIR = Path("data_midia")
    INDEX_DIR = BASE_DIR / "index_annoy"
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    MAP_FILE = INDEX_DIR / "index_map.json"
    ANNOY_FILE = INDEX_DIR / "index.ann"

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

    print("\n🔍 Reconstruindo o índice do zero...")
    index_map = {}  # <-- zera tudo
    proximo_id = 0
    annoy_index = AnnoyIndex(VECTOR_SIZE, "angular")
    proximo_id = processar_midia(BASE_DIR / "imagens", "imagem", index_map, annoy_index, proximo_id)
    proximo_id = processar_midia(BASE_DIR / "videos", "video", index_map, annoy_index, proximo_id)
    if annoy_index.get_n_items() > 0:
        annoy_index.build(10)
        annoy_index.save(str(ANNOY_FILE))
        print(f"✅ Index reconstruído com sucesso. Total: {annoy_index.get_n_items()} itens.")
    else:
        print("⚠️ Nenhum vetor foi adicionado.")
    salvar_index(index_map)

def aguardar_liberacao(arquivo_path, tentativas=5, delay=2):
    """Tenta abrir o arquivo com exclusividade até conseguir ou atingir o limite."""
    for _ in range(tentativas):
        try:
            with open(arquivo_path, "r+b") as f:
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            return True
        except (PermissionError, OSError):
            time.sleep(delay)
    return False

def remover_forcado_cmd(caminho: Path):
    try:
        subprocess.run(
            ["cmd", "/c", "del", "/f", "/q", str(caminho)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=True
        )
        if not caminho.exists():
            print(f"💣 Forçado e deletado: {caminho.name}")
        else:
            print(f"⛔ Ainda não foi possível deletar: {caminho.name}")
    except Exception as e:
        print(f"❌ Erro na exclusão forçada de {caminho.name}: {e}")


def limpar_midias_temporais():
    pasta = Path(__file__).resolve().parent.parent / "midias_temporais"
    if not pasta.exists():
        return

    arquivos_falhados = []

    for arquivo in pasta.iterdir():
        try:
            if arquivo.is_file():
                arquivo.unlink()
        except Exception as e:
            print(f"❌ Erro ao apagar {arquivo.name}: {e}")
            arquivos_falhados.append(arquivo)

    if arquivos_falhados:
        print("⏳ Verificando arquivos em uso antes de tentar apagar novamente...")
        for arquivo in arquivos_falhados:
            if aguardar_liberacao(arquivo):
                try:
                    arquivo.unlink()
                    print(f"✅ Apagado após liberação: {arquivo.name}")
                except Exception:
                    remover_forcado_cmd(arquivo)
            else:
                remover_forcado_cmd(arquivo)





def iniciar_importador():
    pasta = escolher_pasta()
    if pasta:
        copiar_arquivos(pasta)
        rodar_indexador_annoy()
        limpar_midias_temporais()
        
if __name__ == "__main__":
    iniciar_importador()
