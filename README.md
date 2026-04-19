# 🤖 Personal AI Coach

Agente de IA pessoal construído com LangGraph e GPT-4o para auxiliar em dois objetivos de desenvolvimento profissional: leitura de artigos científicos em inglês e prática de algoritmos no LeetCode.

---

## 🎯 Funcionalidades

### 📚 Gestão de Artigos Científicos
- Lista artigos disponíveis no acervo local
- Atualiza status de leitura: `pendente`, `lendo`, `lido`
- Busca semântica de conteúdo via RAG (resumos, tópicos, conceitos)
- Agenda sessões de estudo no Google Calendar

### 💻 LeetCode Tracker
- Rastreia os 75 exercícios mais cobrados em entrevistas (LeetCode 75)
- Marca exercícios como resolvidos, tentados ou para revisitar
- Sugere próximo exercício seguindo a ordem oficial do LeetCode 75
- Consulta progresso por tópico e dificuldade
- Agenda sessões de prática no Google Calendar

### 🗓️ Google Calendar
- Cria eventos de estudo automaticamente via OAuth2
- Suporte a artigos e exercícios de LeetCode
- Lembretes configurados automaticamente

### 🧠 Memória de Longo Prazo
- Histórico de conversas persistido entre sessões via AsyncSqliteSaver
- Contexto personalizado baseado em interações anteriores

---

## 🏗️ Arquitetura

```
personal-ai-coach/
├── agent.py              # Agente principal com LangGraph
├── ingest.py             # Pipeline de indexação dos PDFs
├── data/
│   └── articles/         # PDFs dos artigos científicos
├── storage/
│   ├── articles.json     # Metadados e status dos artigos
│   ├── leetcode.json     # Exercícios livres registrados
│   ├── leetcode75.json   # LeetCode 75 com status de cada exercício
│   └── memory.db         # Memória de longo prazo (SQLite)
├── chroma_db/            # Índice vetorial dos artigos (ChromaDB)
├── credentials/          # Credenciais OAuth2 (não versionado)
└── tools/
    ├── articles_tool.py  # Gestão do acervo de artigos
    ├── calendar_tool.py  # Integração com Google Calendar
    ├── leetcode_tool.py  # Tracker do LeetCode e LeetCode 75
    └── rag_tool.py       # Busca semântica via ChromaDB
```

### Stack Técnica

| Camada | Tecnologia |
|---|---|
| Orquestração do agente | LangGraph + LangChain |
| LLM | GPT-4o (OpenAI) |
| Embedding | BAAI/bge-large-en-v1.5 (HuggingFace) |
| Vector Store | ChromaDB |
| Memória | AsyncSqliteSaver (LangGraph) |
| Calendário | Google Calendar API (OAuth2) |
| MCP | mcp-google-calendar |
| Extração de PDF | PyMuPDF (fitz) |

---

## ⚙️ Instalação

### Pré-requisitos
- Python 3.10+
- Node.js 18+ (para o MCP Server do Google Calendar)
- Ollama (opcional, para rodar modelos locais)
- Conta Google com Calendar API habilitada

### 1. Clone o repositório

```bash
git clone https://github.com/Alebeiruth/my-coach-agent.git
cd my-coach-agent
```

### 2. Crie o ambiente virtual

```bash
python -m venv agent_env

# Linux/Mac
source agent_env/bin/activate

# Windows
agent_env\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
OPENAI_API_KEY=sk-...
```

### 5. Configure o Google Calendar

1. Acesse [console.cloud.google.com](https://console.cloud.google.com)
2. Crie um projeto e ative a **Google Calendar API**
3. Crie credenciais OAuth2 do tipo **Desktop App**
4. Baixe o JSON e salve em `credentials/credentials.json`
5. Gere o token de acesso:

```bash
python -c "
from google_auth_oauthlib.flow import InstalledAppFlow
SCOPES = ['https://www.googleapis.com/auth/calendar']
flow = InstalledAppFlow.from_client_secrets_file('credentials/credentials.json', SCOPES)
creds = flow.run_local_server(port=0)
with open('credentials/token_python.json', 'w') as f:
    f.write(creds.to_json())
"
```

### 6. Adicione seus artigos

Coloque os PDFs em `data/articles/` e rode o pipeline de indexação:

```bash
python ingest.py
```

### 7. Registre os artigos no acervo

Crie ou atualize `storage/articles.json` com os metadados dos seus artigos:

```json
{
  "articles": [
    {
      "id": 1,
      "titulo": "Nome do Artigo",
      "arquivo": "nome_do_arquivo.pdf",
      "status": "pendente",
      "data_inicio": null,
      "data_conclusao": null,
      "observacoes": ""
    }
  ]
}
```

---

## 🚀 Uso

```bash
python agent.py
```

### Exemplos de interação

```
# Artigos
Alexandre: quais artigos tenho no acervo?
Alexandre: agenda sessão de estudo do artigo Digital Twin para amanhã às 9h
Alexandre: me explica o abstract do Smart Cities
Alexandre: marquei o Digital Twin como lendo

# LeetCode 75
Alexandre: qual o próximo exercício do LeetCode 75?
Alexandre: acabei de fazer o Merge Strings Alternately
Alexandre: me mostre os exercícios easy disponíveis
Alexandre: agenda sessão de prática para amanhã às 10h

# Progresso
Alexandre: mostre meu progresso no LeetCode 75
Alexandre: quais artigos já li?
```

---

## 🧩 Padrões de Design

**RAG (Retrieval-Augmented Generation):** Conteúdo dos artigos indexado no ChromaDB com embeddings `bge-large-en-v1.5`. Busca por similaridade semântica com cosine similarity.

**Arquitetura híbrida de recuperação:** Metadados estruturados em JSON (artigos, LeetCode 75) separados do índice vetorial (ChromaDB). Cada camada tem responsabilidade clara.

**ReAct Agent:** O agente raciocina sobre qual tool invocar a cada turno usando o padrão Reason + Act do LangGraph.

**Memória de longo prazo:** Histórico de conversas persistido em SQLite via `AsyncSqliteSaver` — o agente lembra de interações anteriores entre sessões.

**MCP (Model Context Protocol):** Integração com Google Calendar via MCP Server rodando como processo Node.js em stdio transport.

---

## 📝 Licença

MIT