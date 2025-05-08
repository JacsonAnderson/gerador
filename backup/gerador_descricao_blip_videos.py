from pathlib import Path
import json
import time
from PIL import Image
import torch
import av
from transformers import BlipProcessor, BlipForConditionalGeneration

# ✅ Configuração do modelo
USE_MODEL_LARGE = True  # ⬅️ Troque para False se quiser usar o modelo base (mais leve)

MODEL_NAME = (
    "Salesforce/blip-image-captioning-large"
    if USE_MODEL_LARGE
    else "Salesforce/blip-image-captioning-base"
)

device = "cuda" if torch.cuda.is_available() else "cpu"
processor = BlipProcessor.from_pretrained(MODEL_NAME)
model = BlipForConditionalGeneration.from_pretrained(MODEL_NAME).to(device)

# 📁 Configurações
PASTA_BASE = Path("data_midia")
PAUSA_ENTRE_EXECUCOES = 3  # segundos

def gerar_descricao_blip(imagem_pil):
    prompt = "Describe this image in detail, including emotions, colors, objects, actions, setting and atmosphere:"
    inputs = processor(images=imagem_pil, text=prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        saida = model.generate(**inputs, max_new_tokens=80)  # pode ajustar esse valor
    return processor.decode(saida[0], skip_special_tokens=True).strip()

def processar_imagem_ou_video(arquivo_path: Path):
    if not arquivo_path.suffix.lower() in {".webp", ".jpg", ".jpeg", ".png", ".mp4", ".mov", ".webm", ".mkv"}:
        return

    json_path = arquivo_path.with_suffix(".json")
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                dados = json.load(f)
            if dados.get("descricao"):
                return
        except:
            pass

    try:
        if arquivo_path.suffix.lower() in {".webp", ".jpg", ".jpeg", ".png"}:
            imagem = Image.open(arquivo_path).convert("RGB")
        else:
            container = av.open(str(arquivo_path))
            for frame in container.decode(video=0):
                imagem = Image.fromarray(frame.to_ndarray(format="rgb24"))
                break

        descricao = gerar_descricao_blip(imagem)
        print(f"🧠 {arquivo_path.name}: {descricao}")

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({"descricao": descricao}, f, indent=4, ensure_ascii=False)

        time.sleep(PAUSA_ENTRE_EXECUCOES)
    except Exception as e:
        print(f"❌ Erro ao processar {arquivo_path.name}: {e}")

def processar_toda_midia():
    total = 0
    for tipo in ["imagens", "videos"]:
        for subpasta in (PASTA_BASE / tipo).rglob("*"):
            if not subpasta.is_dir():
                continue
            for arquivo in subpasta.iterdir():
                processar_imagem_ou_video(arquivo)
                total += 1
    print(f"\n✅ Total de mídias processadas com descrição: {total}")

# 🚀 Inicia o processo
processar_toda_midia()
