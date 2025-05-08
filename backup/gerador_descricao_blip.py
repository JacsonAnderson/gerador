import os
import time
import json
from pathlib import Path
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch

# Caminho base das imagens
PASTA_IMAGENS = Path("data_midia/imagens")
PAUSA_ENTRE_IMAGENS = 3  # segundos entre execuções

# Inicializa o modelo BLIP base
device = "cuda" if torch.cuda.is_available() else "cpu"
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(device)

def gerar_descricao_blip(imagem_path):
    imagem = Image.open(imagem_path).convert("RGB")
    inputs = processor(imagem, return_tensors="pt").to(device)

    with torch.no_grad():
        saida = model.generate(**inputs, max_new_tokens=50)

    descricao = processor.decode(saida[0], skip_special_tokens=True)
    return descricao.strip()

def processar_imagens():
    total = 0

    for subpasta in PASTA_IMAGENS.glob("*"):
        if not subpasta.is_dir():
            continue

        for arquivo in subpasta.iterdir():
            if not arquivo.suffix.lower() in {".webp", ".jpg", ".jpeg", ".png"}:
                continue

            json_path = arquivo.with_suffix(".json")

            # Pula se já tem descrição válida
            if json_path.exists():
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        dados = json.load(f)
                    if dados.get("descricao"):
                        continue
                except:
                    pass

            try:
                descricao = gerar_descricao_blip(arquivo)
                print(f"🧠 {arquivo.name}: {descricao}")

                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump({"descricao": descricao}, f, indent=4, ensure_ascii=False)

                total += 1
                time.sleep(PAUSA_ENTRE_IMAGENS)

            except Exception as e:
                print(f"❌ Erro com {arquivo.name}: {e}")

    print(f"\n✅ Total de imagens descritas: {total}")

if __name__ == "__main__":
    processar_imagens()
