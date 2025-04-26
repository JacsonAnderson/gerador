# app_roteiro/modulo_idioma.py

IDIOMAS_SUPORTADOS = {
    "pt": {
        "nome": "Português Brasileiro",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Português Brasileiro correto, com clareza e sem regionalismos excessivos."
    },
    "es": {
        "nome": "Espanhol Neutro",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Espanhol neutro latino, com clareza e sem misturar português ou outros idiomas."
    },
    "en": {
        "nome": "Inglês",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Inglês fluente, natural e de fácil entendimento para o público global."
    },
    "fr": {
        "nome": "Francês",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Francês europeu padrão, com clareza e elegância."
    },
    "de": {
        "nome": "Alemão",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Alemão padrão (Hochdeutsch), formal e claro."
    },
    "it": {
        "nome": "Italiano",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Italiano formal, elegante e de fácil compreensão."
    },
    "ja": {
        "nome": "Japonês",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Japonês formal (日本語), com clareza e respeito pela cultura local."
    },
    "zh": {
        "nome": "Chinês (Mandarim Simplificado)",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Chinês Mandarim Simplificado (中文简体), de forma clara e profissional."
    },
    "ru": {
        "nome": "Russo",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Russo padrão, com linguagem formal e respeitosa."
    },
    "ar": {
        "nome": "Árabe",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Árabe moderno padrão (الفصحى), claro e respeitando normas culturais."
    },
    "hi": {
        "nome": "Hindi",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Hindi formal (हिन्दी), de forma clara e culturalmente respeitosa."
    },
    "tr": {
        "nome": "Turco",
        "instrucao": "\n\n⚠️ IMPORTANTE: Toda a resposta deve obrigatoriamente ser escrita em Turco padrão, com linguagem clara e respeitosa."
    }
}

def obter_instrucao_idioma(codigo_idioma):
    """Retorna a instrução correta para o idioma especificado."""
    idioma = codigo_idioma.lower()
    return IDIOMAS_SUPORTADOS.get(idioma, {}).get("instrucao", "")
