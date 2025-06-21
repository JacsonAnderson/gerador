````markdown
# Gerador de Conteúdo Automatizado

Aqui você vai encontrar *todas* as minhas ferramentas de geração automática de conteúdo. Conforme surgem novas maluquices, adiciono os tutoriais aqui.

> ⚡ **Importante:**  
> A geração de roteiros ainda está em **BETA** — melhorias e ajustes pipocando toda hora.

> ⚠️ **Atenção:**  
> Este projeto foi testado com **Python 3.11.9**.  
> Pra evitar dor de cabeça, use a mesma versão.

---

## 🚀 Instalação e configuração

1. **Clone o repositório**  
   ```bash
   git clone https://github.com/JacsonAnderson/gerador.git
````

2. **Entre na pasta**

   ```bash
   cd gerador
   ```

3. **Crie um virtualenv**

   ```bash
   python -m venv .venv
   ```

   > No Windows:
   >
   > ```bash
   > .venv\Scripts\activate
   > ```

4. **Instale as dependências**

   ```bash
   pip install -r requirements.txt
   ```

5. **Configure sua chave OpenAI**

   * Renomeie `.env.example` para `.env`
   * Preencha:

     ```
     OPENAI_API_KEY=sua_chave_aqui
     ```

6. **Rode o app**

   ```bash
   python app.py
   ```

   (por enquanto)

---

## 🎯 Observações

* Modelos GPT foram escolhidos a dedo pelo melhor custo-benefício sem fritar sua fatura.
* **Não** fique trocando o modelo no código sem entender a bagunça toda.
* Quase tudo aqui é pipoca: melhorias contínuas, funções novas e… bug fixes (muitos).

---

## 📋 Status do Projeto

* ✅ Interface simples e dinâmica (vou dar aquele tapa depois).
* ✅ Banco de dados SQLite + criação automática de pastas.
* 🔄 Roteiro no `videoforge`: gera tópicos, resumos e introduções, mas ainda tá meio **experimental**.
* 🚧 Geração de conteúdo fluido e conectado entre tópicos (**em testes**).
* 🚀 Novas funcionalidades pipocando toda hora.

---

## 📬 Contato

Dúvidas, sugestões ou só pra brincar: abra uma **Issue** ou me ache no GitHub!

> **Feito com café, códigos e healthy sarcasm por [Jacson Anderson](https://github.com/JacsonAnderson)** 🚀✨

---

## 📬 Histórico de Mudanças & Diário da Depressão (meme ou verdade? você decide) kk 👌😎

**19/06/2025**
– Voltei ao projeto após 1 mês largado — quase joguei tudo no lixo, mas aquela vergonha me segurou.
– A YouTube Transcript API tava me zuando com erros sem sentido. Criei um `db_manager.py` pra dar um tapa na lógica, mas prometo fusionar tudo num `app.py` decente… um dia.

**21/06/2025**
– Manhã inteira caçando transcrição automática, tentando não surtar.
– Solução feliz: `yt_dlp` baixa o `.vtt`, `webvtt` limpa o texto.
– **O bug da vez**: meu nome de arquivo era o meu `video_id` interno, mas eu procurava pelo **YouTube ID**. Glob nunca achava, e eu rodava tudo em vão. Corrigi pra usar sempre o **YouTube ID** no nome do `.vtt` — agora baixa UMA legenda, limpa e cospe no `transcript_original.json`.


```
```
