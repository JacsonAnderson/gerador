# Gerador de Conteúdo Automatizado

Aqui você encontrará todas as minhas ferramentas para geração automática de conteúdo. Conforme forem surgindo novas aplicações, também adicionarei os tutoriais aqui.

> ⚡ **Importante:**  
> A função para **geração de roteiros** ainda está em **BETA**. Melhorias e ajustes estão em andamento para garantir a máxima qualidade dos conteúdos.

> ⚠️ **Atenção:**  
> O projeto foi desenvolvido utilizando **Python 3.11.9**.  
> Para evitar incompatibilidades, recomenda-se utilizar a mesma versão.

---

## 🚀 Como instalar e configurar

Siga os passos abaixo para rodar o projeto localmente:

### 1. Clone o repositório

```bash
git clone https://github.com/JacsonAnderson/gerador.git
```

### 2. Entre na pasta do projeto

```bash
cd gerador
```

### 3. Crie um ambiente virtual

```bash
python -m venv .venv
```

> Obs: No Windows, ative o ambiente virtual com:
> ```bash
> .venv\Scripts\activate
> ```

### 4. Instale as dependências

```bash
pip install -r requirements.txt
```

### 5. Configure o ambiente

Renomeie o arquivo `.env.example` para `.env` e adicione sua chave da OpenAI no campo apropriado:

```
OPENAI_API_KEY=coloque_sua_chave_aqui
```

### 6. Execute o Instalador de Dependências

Dê um duplo clique no arquivo:

```
Instalador_de_dependencias.bat
```

Isso criará automaticamente os diretórios necessários:

- `data/`
- `db/`
- `db/canais/`

---

## 🎯 Observações Importantes

- Este projeto utiliza **modelos GPT selecionados estrategicamente** com base no **melhor custo-benefício** para geração em massa de conteúdos **sem comprometer a qualidade**.
- **Cada modelo** foi cuidadosamente estudado antes de ser adotado no sistema.
- ⚠️ **Não altere os modelos GPT** usados no código sem antes entender a estrutura e otimização aplicada.

---

## 📋 Status do Projeto

- ✅ Estrutura básica de geração de roteiros
- ✅ Geração de tópicos, resumos e introduções
- 🚧 Geração de conteúdo fluido e conectado entre tópicos (**em BETA**)
- 🚀 Novas funções e melhorias contínuas sendo planejadas

---

## 📬 Contato

Caso tenha dúvidas, sugestões ou queira acompanhar as atualizações, fique à vontade para abrir uma **Issue** ou entrar em contato!

---

> **Feito com dedicação por [Jacson Anderson](https://github.com/JacsonAnderson)** 🚀✨
