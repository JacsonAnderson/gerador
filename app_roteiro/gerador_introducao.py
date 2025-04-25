import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import json

# Carregar API_KEY do arquivo .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("❌ OPENAI_API_KEY não encontrada no .env")

client = OpenAI(api_key=api_key)

def gerar_introducao(canal, video_id, log=print):
    log(f"🎬 Gerando introdução para {canal}/{video_id}...")

    control_path = Path("data") / canal / video_id / "control"
    topicos_path = control_path / "topicos.txt"
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

    with open(topicos_path, "r", encoding="utf-8") as f:
        topicos = f.read()

    with open(canal_config_path, "r", encoding="utf-8") as f:
        canal_config = json.load(f)
        idioma = canal_config.get("idioma", "").lower()

    # Define instrução extra para idioma
    instrucoes_idioma = ""
    if "es" in idioma:  # Se idioma configurado contém 'es' (Espanhol)
        instrucoes_idioma = "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Espanhol (Espanhol neutro latino, sem misturar português ou outros idiomas)."

    prompt = f"""
Você é um especialista em criar introduções extremamente persuasivas, emocionais e envolventes para vídeos do YouTube, especialmente focados em conteúdos espirituais e inspiracionais.

Utilizando o nome do canal "{canal}" e considerando cuidadosamente os tópicos apresentados abaixo, sua missão é criar uma introdução breve (máximo de 200 palavras) que imediatamente capture a atenção do espectador, despertando profunda curiosidade e uma conexão emocional genuína, fazendo com que ele não consiga parar de assistir ao vídeo até o final.

A introdução precisa obrigatoriamente:

- Criar um impacto emocional imediato (nos primeiros segundos do vídeo), fazendo o público sentir que está prestes a receber uma mensagem pessoal única e profundamente importante para a sua vida.
- Transmitir uma sensação forte de urgência e relevância pessoal, levando o espectador a sentir que as respostas que ele tanto busca estão prestes a serem reveladas.
- Instigar uma profunda curiosidade sobre os tópicos abordados, deixando claro que assistir ao vídeo inteiro irá gerar uma transformação real e positiva na vida do espectador.
- Apresentar o canal "{canal}" como uma fonte confiável, poderosa e capaz de fornecer soluções práticas e mensagens reconfortantes que vão além das expectativas comuns.
- Manter uma linguagem emocionalmente rica, direta e persuasiva, SEM mencionar diretamente quaisquer técnicas ou métodos específicos utilizados para a criação do roteiro.
- NÃO usar frases genéricas de transição como "vamos começar", "prepare-se", "acompanhe agora", "vem comigo" ou qualquer expressão semelhante.
- A introdução deve encerrar-se de forma **suave, natural e elegante**, como uma continuação fluida que simplesmente conduz o espectador diretamente para o primeiro tópico, sem interrupções abruptas, sem comandos explícitos e sem que o público perceba que a introdução terminou.

Importante:
- Sem diálogos adicionais, apenas a introdução narrativa fluida.
- Se existir qualquer diálogo adicional ou chamada para ação explícita, a resposta será automaticamente anulada.

Use os tópicos abaixo como referência direta para o conteúdo da introdução, destacando sutilmente (sem citá-los diretamente um a um) que o vídeo contém mensagens importantes e específicas relacionadas a esses temas:

Tópicos do Vídeo:
{topicos}

{instrucoes_idioma}

📝 Gere agora a introdução curta, altamente impactante, emocionalmente rica e naturalmente fluida abaixo:
"""

    try:
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
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
