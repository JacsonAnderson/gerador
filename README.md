# 🧠 Gerador de Conteúdo Automatizado

Aqui você vai encontrar **todas** as minhas ferramentas para gerar conteúdo automaticamente. Conforme as ideias (ou surtos) forem surgindo, adiciono tudo aqui — com tutorial e um pouco de sarcasmo.

> ⚡ **Importante:**  
> A função de **geração de roteiros** ainda está em **BETA**. Melhorias estão sendo feitas na marra.

> ⚠️ **Atenção:**  
> Projeto testado com **Python 3.11.9**.  
> Use essa versão se não quiser sofrer com bugs randômicos.

---

## 🚀 Instalação

1. **Clone o repositório**

```bash
git clone https://github.com/JacsonAnderson/gerador.git
```

2. **Acesse a pasta**

```bash
cd gerador
```

3. **Crie um ambiente virtual**

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

5. **Configure o ambiente**

Renomeie o `.env.example` para `.env` e insira sua chave da OpenAI:

```
OPENAI_API_KEY=sua_chave_aqui
```

6. **Execute o app**

```bash
python app.py
```

(Sim, ainda é manual… mas funciona.)

---

## 📋 Status do Projeto

- ✅ Interface simples e funcional (com potencial pra ficar bonita).
- ✅ Banco de dados em SQLite, pastas geradas automaticamente.
- 🔄 Geração de roteiro com tópicos, resumos e introdução (funciona, mas exige ajustes).
- 🚧 Geração de conteúdo conectado entre tópicos está **em testes**.
- 🚀 Novas ideias e melhorias surgindo no caos (como sempre).

---

## 🎯 Observações

- Os modelos GPT foram escolhidos pelo melhor custo-benefício (sim, eu pesquisei).
- **Não troque** o modelo à toa. Você pode quebrar tudo e me culpar depois.
- Se algo não funcionar... provavelmente é culpa do universo. Ou do Python. Ou sua.

---

## 📬 Contato

Quer sugerir algo, reclamar ou apenas dizer “oi”?  
Abra uma **Issue** ou me ache no [GitHub](https://github.com/JacsonAnderson).

> Feito com cafeína, teimosia e algumas lágrimas por [Jacson Anderson](https://github.com/JacsonAnderson) 🚀

---

## 🗓️ Histórico de Mudanças & Diário da Depressão (meme ou verdade?)

### 🧩 19/06/2025

- Voltei pro projeto depois de um mês parado. Estava pronto pra deletar tudo, mas a culpa venceu.
- A YouTube Transcript API decidiu me trolar com erros obscuros.
- Criei um `db_manager.py` pra consertar uma lógica zoada. Um dia eu junto tudo no `app.py`… talvez.

### 📉 21/06/2025

- Passei a manhã inteira lutando com as transcrições automáticas.
- A solução: usar `yt_dlp` pra baixar `.vtt` e `webvtt` pra limpar tudo.
- **Bug nojento**: eu nomeava os arquivos com o `video_id` interno, mas buscava usando o **YouTube ID**. O `glob` não achava nada. Corrigido. Agora baixa UMA legenda e salva tudo direitinho em `transcript_original.json`.

E seguimos... entre bugs e cafés.
