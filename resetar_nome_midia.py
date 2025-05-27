import json
from pathlib import Path

def resetar_nome_midia():
    caminho = Path(r"D:\Gerador\data\Salud Y Bienestar\001\control\segmentos.json")

    if not caminho.exists():
        print(f"❌ Arquivo não encontrado: {caminho}")
        return

    with open(caminho, "r", encoding="utf-8") as f:
        data = json.load(f)

    alterado = False
    for seg in data.get("segments", []):
        if "nome_midia" in seg:
            seg["nome_midia"] = ""
            alterado = True

    if alterado:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"✅ Campos 'nome_midia' limpos com sucesso: {caminho}")
    else:
        print("⚠️ Nenhum campo 'nome_midia' encontrado para limpar.")

if __name__ == "__main__":
    resetar_nome_midia()
