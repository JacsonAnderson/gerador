import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from app_roteiro.modulo_idioma import obter_instrucao_idioma

# Carrega API KEY
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("❌ OPENAI_API_KEY não encontrada no .env")

client = OpenAI(api_key=api_key)

def gerar_conteudos_topicos(canal, video_id, log=print):
    log(f"📝 Iniciando geração de conteúdos dos tópicos para {canal}/{video_id}...")

    control_path = Path("data") / canal / video_id / "control"
    topicos_path = control_path / "topicos.json"
    resumo_path = control_path / "resumo.json"
    introducao_path = control_path / "introducao.txt"
    config_canal_path = Path("db") / "canais" / f"{canal}.json"

    # Verificações
    if not topicos_path.exists():
        log(f"❌ Arquivo de tópicos não encontrado: {topicos_path}")
        return False
    if not resumo_path.exists():
        log(f"❌ Resumo geral não encontrado: {resumo_path}")
        return False
    if not introducao_path.exists():
        log(f"❌ Introdução não encontrada: {introducao_path}")
        return False
    if not config_canal_path.exists():
        log(f"❌ Configuração do canal não encontrada: {config_canal_path}")
        return False

    # Carrega dados
    with open(topicos_path, "r", encoding="utf-8") as f:
        topicos_json = json.load(f)

    with open(resumo_path, "r", encoding="utf-8") as f:
        resumo_transcricao = json.load(f).get("resumo", "")

    with open(introducao_path, "r", encoding="utf-8") as f:
        base_anterior = f.read().strip()

    with open(config_canal_path, "r", encoding="utf-8") as f:
        config_canal = json.load(f)
        idioma = config_canal.get("idioma", "").lower()
        prompt_roteiro = config_canal.get("prompt_roteiro", "").strip()

    if not prompt_roteiro:
        log(f"⚠️ Prompt de roteiro não definido para o canal {canal}.")
        return False

    instrucoes_idioma = obter_instrucao_idioma(idioma)
    topicos = topicos_json.get("topicos", [])

    if not topicos:
        log(f"⚠️ Nenhum tópico encontrado no arquivo {topicos_path}")
        return False

    roteiros_gerados = []

    for i, topico in enumerate(topicos):
        numero = topico.get("numero")
        titulo = topico.get("titulo", "")
        resumo_topico = topico.get("resumo", "")

        # Pega o resumo do próximo tópico (se existir)
        proximo_resumo = ""
        if i + 1 < len(topicos):
            proximo_resumo = topicos[i + 1].get("resumo", "")

        # ⚡ Instrução de idioma bem explícita
        idioma_instrucao = ""
        if idioma == "es":
            idioma_instrucao = "⚡ Escreva TODO o conteúdo completamente em espanhol latino natural, sem misturar com português ou inglês."
        elif idioma == "en":
            idioma_instrucao = "⚡ Write ALL the content completely in natural American English, without mixing with other languages."
        else:
            idioma_instrucao = "⚡ Escreva TODO o conteúdo completamente em português brasileiro natural, sem misturar com outros idiomas."

        prompt = f"""
{idioma_instrucao}

Você é um especialista em desenvolver conteúdos narrativos de altíssima qualidade para vídeos de YouTube, elaborados para criar uma forte conexão emocional e intelectual com o público, independentemente do tema (saúde, esportes, espiritualidade, finanças, desenvolvimento pessoal, entre outros).

⚡ Diretrizes obrigatórias:

- O texto deve ser uma extensão contínua da base fornecida (não criar sensação de reinício nem introduções paralelas).
- A linguagem deve ser intimista, concreta, emocionalmente vívida, falando diretamente ao espectador como se fosse um conselho único e pessoal.
- Não utilizar expressões genéricas, metáforas vazias, clichês emocionais ou frases de transição como ("vamos começar", "vem comigo", "fique até o final", "no próximo tópico", "no próximo tema", "em breve veremos", "logo exploraremos", etc.).
- Proibido mencionar técnicas de escrita, marketing, roteirização ou qualquer referência metalinguística.
- Proibido concluir o texto com tom de encerramento: o final deve ser fluido e naturalmente aberto, mantendo a atmosfera viva para o próximo trecho.
- Importante: Você está construindo um único vídeo dividido em partes (tópicos), portanto, **NUNCA** finalize ideias como se fossem fechar o assunto ou concluir um raciocínio.
- Também é proibido preparar o público explicitamente para o próximo tópico. Não faça previsões, chamadas ou antecipações forçadas. Mantenha a fluidez emocional contínua e natural.
- Cada frase deve carregar peso emocional real, com força narrativa e elegância, evitando exageros, redundâncias ou qualquer quebra de atmosfera emocional.
- Foque em agregar valor real ao telespectador em cada parágrafo, transmitindo autoridade, emoção e credibilidade.

📜 Estrutura obrigatória baseada em frameworks de alta conversão:

- **ATENCIÓN**: Capturar imediatamente a atenção emocional do espectador nos primeiros 5 segundos.
- **INTERÉS**: Desenvolver uma conexão genuína e profunda com os problemas, desejos ou aspirações do público.
- **DESEO + AUTORIDAD**: Apresentar soluções, caminhos ou reflexões práticas com credibilidade natural, sem soar instrucional ou arrogante.

---

{prompt_roteiro}

Contexto geral do vídeo:
"{resumo_transcricao}"

Base do conteúdo anterior para conexão:
"{base_anterior}"

Novo Título do Tópico:
"{titulo}"

Resumo do Novo Tópico:
"{resumo_topico}"

Resumo do Próximo Tópico (para transição emocional natural, se aplicável):
"{proximo_resumo}"

{instrucoes_idioma}

📝 Gere agora a continuação fluida, emocional, extremamente envolvente e conectada naturalmente com o próximo tema, sem criar expectativas explícitas e sem finalizar o raciocínio:
"""

        try:
            resposta = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
            )

            conteudo_gerado = resposta.choices[0].message.content.strip()
            base_anterior = conteudo_gerado

            roteiros_gerados.append({
                "numero": numero,
                "titulo": titulo,
                "conteudo": conteudo_gerado
            })

            log(f"✅ Conteúdo gerado para Tópico {numero}")

        except Exception as e:
            log(f"❌ Erro ao gerar conteúdo para Tópico {numero}: {e}")
            return False

    roteiros_path = control_path / "roteiros.json"
    with open(roteiros_path, "w", encoding="utf-8") as f:
        json.dump({"roteiros": roteiros_gerados}, f, indent=4, ensure_ascii=False)

    log(f"✅ Todos conteúdos salvos em {roteiros_path}")
    return True
