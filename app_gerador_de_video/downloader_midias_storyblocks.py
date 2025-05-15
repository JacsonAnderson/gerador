import asyncio
import pyautogui
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from slugify import slugify

# Coordenadas de clique: (elemento, botão de download)
COORDS = [
    ((211, 586), (403, 671)),  # Vídeo 1
    ((642, 583), (809, 669)),  # Vídeo 2
    ((1072, 571), (1230, 663)) # Vídeo 3
]

# Caminho vindo do argumento
if len(sys.argv) < 2:
    print("❌ Caminho para faltando_midias.json não foi fornecido.")
    sys.exit(1)

FALTANDO_JSON = Path(sys.argv[1])
if not FALTANDO_JSON.exists():
    print(f"❌ Arquivo não encontrado: {FALTANDO_JSON}")
    sys.exit(1)

# Verifica se já foi baixado antes
FLAG_BAIXADAS = FALTANDO_JSON.parent / "midias_baixadas.txt"
if FLAG_BAIXADAS.exists():
    print("⚠️ Mídias já foram baixadas anteriormente. Abortando...")
    sys.exit(0)

# midias_temporais na raiz
PASTA_DESTINO = Path(__file__).resolve().parent.parent / "midias_temporais"
PASTA_DESTINO.mkdir(exist_ok=True)

# Carrega credenciais
load_dotenv()
EMAIL = os.getenv("email_storyblocks")
SENHA = os.getenv("password_storyblocks")

async def baixar_top_3_videos(page, desc):
    print("⏳ Aguardando carregamento visual...")
    await page.wait_for_timeout(3000)

    slug = slugify(desc)[:50]

    for i, ((x_card, y_card), (x_btn, y_btn)) in enumerate(COORDS, start=1):
        nome_arquivo = f"{slug}_video_{i:02d}.mp4"
        destino = PASTA_DESTINO / nome_arquivo

        if destino.exists():
            print(f"⚠️ Já existe: {nome_arquivo}, pulando...")
            continue

        print(f"🎬 Simulando clique no vídeo {i}...")

        pyautogui.moveTo(x_card, y_card, duration=0.5)
        await page.wait_for_timeout(1000)
        pyautogui.moveTo(x_btn, y_btn, duration=0.3)
        await page.wait_for_timeout(500)

        try:
            async with page.expect_download() as download_info:
                pyautogui.click()
            download = await download_info.value
            await download.save_as(destino)
            print(f"✅ Baixado: {nome_arquivo}")

        except Exception as e:
            print(f"❌ Erro ao baixar vídeo {i}: {e}")

async def buscar_segmentos(page, descricoes):
    for i, desc in enumerate(descricoes):
        termo = desc.strip().replace(" ", "-").lower()
        url = f"https://www.storyblocks.com/all-video/search/{termo}"
        print(f"\n🔎 ({i+1}/{len(descricoes)}) Buscando: {desc}")
        await page.goto(url)
        await page.wait_for_timeout(3000)
        await baixar_top_3_videos(page, desc)

async def login_e_buscar():
    with open(FALTANDO_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    descricoes = data.get("descricao_faltando", [])

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        print("🔐 Acessando página de login...")
        await page.goto("https://www.storyblocks.com/login")
        await page.wait_for_selector("input[type='email']")
        await page.fill("input[type='email']", EMAIL)
        await page.fill("input[type='password']", SENHA)
        await page.check("#agreement-checkbox")
        await page.click("button[type='submit']")
        print("🚪 Login enviado...")
        await page.wait_for_timeout(5000)
        await page.evaluate("window.moveTo(0,0); window.resizeTo(screen.width, screen.height);")

        await buscar_segmentos(page, descricoes)
        print("✅ Todas as buscas e downloads concluídas.")

        # Marca como concluído
        with open(FLAG_BAIXADAS, "w", encoding="utf-8") as f:
            f.write("✅ Mídias baixadas com sucesso.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(login_e_buscar())
