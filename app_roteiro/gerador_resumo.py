import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Carrega a chave da OpenAI do .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError("❌ OPENAI_API_KEY não encontrada no .env")

client = OpenAI(api_key=api_key)

def gerar_resumo(canal, video_id, log=print):
    log(f"🧠 Gerando resumo para {canal}/{video_id}...")

    video_path = Path("data") / canal / video_id
    control_path = video_path / "control"
    transcript_path = control_path / "transcript_original.json"
    resumo_path = control_path / "resumo.json"

    # Se já existe o resumo, pula
    if resumo_path.exists():
        log(f"📄 Resumo já existente em {resumo_path}")
        return True

    # Verifica se existe a transcrição
    if not transcript_path.exists():
        log(f"❌ Transcrição não encontrada em {transcript_path}")
        return False

    with open(transcript_path, "r", encoding="utf-8") as f:
        texto = json.load(f)

    if not texto or not isinstance(texto, str):
        log(f"⚠️ Transcrição inválida ou vazia.")
        return False

    prompt = (
        "Você é um assistente especialista em análise de conteúdo de vídeos do YouTube, com foco em compreensão profunda, segmentação de tópicos e extração de ideias centrais. "
        "Abaixo está a transcrição completa de um vídeo. Sua tarefa é gerar um resumo avançado e estruturado, como se fosse uma apresentação escrita para um briefing editorial.\n\n"
        
        "⚙️ **Instruções específicas:**\n"
        "1. Leia todo o conteúdo cuidadosamente.\n"
        "2. Identifique e liste os principais tópicos abordados, com subtítulos claros se necessário.\n"
        "3. Para cada tópico, explique o que foi dito com detalhes, destacando as ideias principais, exemplos utilizados, dados mencionados ou histórias relatadas.\n"
        "4. Se houver momentos de opinião, crítica, humor, instrução ou ensinamento, destaque-os separadamente.\n"
        "5. Use linguagem clara, profissional e fluída, como se estivesse explicando o conteúdo a um leitor que precisa entender tudo sem ver o vídeo.\n"
        "6. Mantenha a organização lógica e sequencial do vídeo, respeitando a ordem dos acontecimentos.\n\n"
        
        f"🎙️ **Transcrição original do vídeo:**\n{texto}\n\n"
        "✍️ **Gere agora o resumo completo e detalhado conforme solicitado acima:**"
    )


    try:
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        resumo = resposta.choices[0].message.content.strip()

        with open(resumo_path, "w", encoding="utf-8") as f:
            json.dump({"resumo": resumo}, f, indent=4, ensure_ascii=False)

        log(f"✅ Resumo salvo em {resumo_path}")
        return True

    except Exception as e:
        log(f"❌ Erro ao gerar resumo: {e}")
        return False
