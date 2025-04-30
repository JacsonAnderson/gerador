import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from app_roteiro.modulo_idioma import obter_instrucao_idioma

# Carregar API_KEY do arquivo .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("❌ OPENAI_API_KEY não encontrada no .env")

client = OpenAI(api_key=api_key)

def gerar_introducao(canal, video_id, log=print):
    log(f"🎬 Gerando introdução para {canal}/{video_id}...")

    control_path = Path("data") / canal / video_id / "control"
    topicos_path = control_path / "topicos.json"
    introducao_path = control_path / "introducao.txt"
    canal_config_path = Path("db") / "canais" / f"{canal}.json"

    if introducao_path.exists():
        log(f"⚠️ Introdução já existente para {canal}/{video_id}.")
        return True

    if not topicos_path.exists():
        log(f"❌ Arquivo de tópicos não encontrado em {topicos_path}.")
        return False

    if not canal_config_path.exists():
        log(f"❌ Arquivo de configuração do canal não encontrado em {canal_config_path}.")
        return False

    # Corrigido para carregar o JSON
    with open(topicos_path, "r", encoding="utf-8") as f:
        topicos_json = json.load(f)

    # Monta o texto dos tópicos para usar no prompt
    topicos = ""
    for topico in topicos_json.get("topicos", []):
        topicos += f'- {topico["titulo"]}: {topico["resumo"]}\n'

    with open(canal_config_path, "r", encoding="utf-8") as f:
        canal_config = json.load(f)
        idioma_configurado = canal_config.get("idioma", "").lower()

    # Pega a instrução correta do idioma
    instrucoes_idioma = obter_instrucao_idioma(idioma_configurado)

    prompt = f"""
Você é um especialista em criação de introduções altamente persuasivas e emocionalmente impactantes para vídeos de YouTube. Seu trabalho é capturar imediatamente a atenção do público e gerar um forte desejo de continuar assistindo, usando frases que toquem nas dores reais, nos desejos ocultos e nas promessas transformadoras que o vídeo pode entregar.

Sua missão é criar uma introdução curta (máximo 150 palavras) para o canal "{canal}", baseada nos tópicos abaixo, respeitando as diretrizes obrigatórias:

⚡ Diretrizes obrigatórias:
- A primeira frase deve **impactar diretamente o emocional ou o racional do espectador em menos de 5 segundos**, com uma dor, desejo ou pergunta instigante.
- A introdução deve criar uma **conexão real com o público**, fazendo com que ele se sinta compreendido em sua dor, ansiedade, dúvida ou busca pessoal.
- Em seguida, apresente **uma promessa concreta**, uma transformação que será abordada no vídeo — **sem soar como técnica de marketing**, mas com **autoridade natural** e tom de revelação importante.
- Finalize com uma **frase fluida e emocional**, sem dar fechamento ou comandos explícitos — apenas mantendo a tensão emocional viva, como um gancho natural que conduz ao próximo conteúdo.

📌 Linguagem:
- Escreva com frases fortes, curtas, emocionalmente vívidas e específicas.
- Fale com **clareza**, **urgência emocional**, **sem abstrações**, **sem metáforas místicas** e **sem floreios poéticos genéricos**.
- Parece uma conversa sincera com alguém que realmente precisa ouvir isso — e **não** uma abertura formal de vídeo.

🚫 Proibições obrigatórias:
- **NÃO** use frases como: “Neste vídeo você verá…”, “Hoje falaremos sobre…”, “Em um rincón do universo…”, “Prepare-se para…”, “Acompanhe até o final…”.
- **NÃO** mencione técnicas, métodos, sistemas, estratégias, marketing, nem qualquer termo metalinguístico.
- **NÃO** escreva de forma genérica, mística, vaga, motivacional de autoajuda ou fantasiosa.
- **NÃO** finalize o texto com frases de encerramento. A introdução deve ser como um “gancho emocional” que leva direto para o primeiro tópico do vídeo.

Use os tópicos abaixo como referência **sem copiá-los literalmente**, para construir uma introdução intensa e altamente persuasiva:

Tópicos do Vídeo:
{topicos}

{instrucoes_idioma}

📝 Crie agora a introdução: curta, impactante, emocionalmente envolvente, com promessa clara, sem encerramento explícito e com um gancho natural que leve ao primeiro conteúdo.
"""



    try:
        resposta = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
        )

        introducao_gerada = resposta.choices[0].message.content.strip()

        with open(introducao_path, "w", encoding="utf-8") as f:
            f.write(introducao_gerada)

        log(f"✅ Introdução salva em {introducao_path}")
        return True

    except Exception as e:
        log(f"❌ Erro ao gerar introdução: {e}")
        return False
