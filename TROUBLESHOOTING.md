# 🛠️ Problemas e Soluções — Personal AI Coach

Registro técnico dos principais problemas encontrados durante o desenvolvimento do projeto e como foram resolvidos.

---

## 1. Ambiente Virtual — Windows não reconhece `source`

**Problema:** Ao tentar ativar o ambiente virtual com `source agent_env/bin/activate`, o Windows retorna erro de comando não encontrado.

**Causa:** O comando `source` é exclusivo de shells Unix/Linux. No Windows o equivalente é diferente.

**Solução:**
```bash
# Windows PowerShell
agent_env\Scripts\activate

# Se der erro de política de execução
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
agent_env\Scripts\activate
```

---

## 2. HuggingFaceEmbeddings deprecado

**Problema:** `from langchain_community.embeddings import HuggingFaceEmbeddings` gerava warning de depreciação.

**Causa:** O pacote foi movido para `langchain-huggingface` a partir da versão 0.2.2 do LangChain.

**Solução:**
```bash
pip install -U langchain-huggingface
```
```python
from langchain_huggingface import HuggingFaceEmbeddings
```

---

## 3. ChromaDB — argumento inesperado `embeddings`

**Problema:** `Chroma.__init__() got an unexpected keyword argument 'embeddings'`

**Causa:** A API do ChromaDB mudou — o parâmetro correto é `embedding` (sem o `s`).

**Solução:**
```python
Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,  # sem o 's'
    persist_directory="./chroma_db",
    collection_name="artigos",
)
```

---

## 4. Encoding de arquivos TXT no Windows

**Problema:** `UnicodeDecodeError: 'utf-8' codec can't decode byte` ao ler arquivos `.txt`.

**Causa:** Arquivos gerados no Windows são salvos em `cp1252` por padrão, não em UTF-8.

**Solução:**
```python
text = path.read_text(encoding="cp1252")
# ou para ignorar bytes inválidos:
text = path.read_text(encoding="utf-8", errors="ignore")
```

---

## 5. `RecursiveCharacterTextSplitter` — import quebrado

**Problema:** `Cannot import name 'RecursiveCharacterTextSplitter' from 'langchain.text_splitter'`

**Causa:** A partir do LangChain 1.x, o módulo de text splitters foi separado em pacote próprio.

**Solução:**
```bash
pip install langchain-text-splitters
```
```python
from langchain_text_splitters import RecursiveCharacterTextSplitter
```

---

## 6. `create_openai_tools_agent` e `AgentExecutor` removidos

**Problema:** `ImportError: cannot import name 'create_openai_tools_agent'`

**Causa:** Com o LangChain 1.x e LangGraph 1.x, o sistema de agentes foi completamente migrado para o LangGraph. `AgentExecutor` foi depreciado.

**Solução:**
```python
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt=system_prompt,
    checkpointer=memory,
)
```

---

## 7. `SqliteSaver` não suporta métodos async

**Problema:** `NotImplementedError: The SqliteSaver does not support async methods. Consider using AsyncSqliteSaver`

**Causa:** O agente usa `astream` (assíncrono), mas o `SqliteSaver` é síncrono.

**Solução:**
```bash
pip install aiosqlite
```
```python
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

async with AsyncSqliteSaver.from_conn_string("storage/memory.db") as memory:
    agent = create_react_agent(..., checkpointer=memory)
```

---

## 8. `MultiServerMCPClient` não pode ser usado como context manager

**Problema:** `NotImplementedError: As of langchain-mcp-adapters 0.1.0, MultiServerMCPClient cannot be used as a context manager`

**Causa:** API do `langchain-mcp-adapters` mudou na versão 0.1.0.

**Solução:**
```python
mcp_client = MultiServerMCPClient({...})
mcp_tools = await mcp_client.get_tools()
```

---

## 9. MCP Server não encontra `npx` no Windows

**Problema:** `FileNotFoundError: [WinError 2] O sistema não pode encontrar o arquivo especificado` ao iniciar o MCP Server.

**Causa:** O processo filho do Python não herda o PATH completo do Windows, então não encontra o `npx`.

**Solução:** Usar o caminho absoluto do `npx.cmd`:
```python
mcp_client = MultiServerMCPClient({
    "google-calendar": {
        "command": r"C:\Program Files\nodejs\npx.cmd",
        "args": ["-y", "mcp-google-calendar"],
        "transport": "stdio",
        "cwd": str(os.path.abspath("./credentials")),
    }
})
```

---

## 10. Google Calendar MCP — credencial do tipo Web em vez de Desktop

**Problema:** `Error: The provided keyfile does not define a valid redirect URI`

**Causa:** A credencial OAuth2 foi criada como "Web Application" em vez de "Desktop App". A credencial Web não tem o `redirect_uris` necessário para fluxo local.

**Solução:** Criar nova credencial no Google Cloud Console do tipo **Desktop App** e substituir o `credentials.json`.

---

## 11. Google Calendar MCP — usuário não adicionado como tester

**Problema:** `Error 403: access_denied — app has not completed Google verification`

**Causa:** O app OAuth está em modo de teste e o email não estava na lista de usuários de teste.

**Solução:** No Google Cloud Console → "Tela de permissão OAuth" → "Usuários de teste" → adicionar o email da conta Google.

---

## 12. MCP Server do Google Calendar — schema inválido rejeitado pelo GPT-4o

**Problema:** `openai.BadRequestError: Invalid schema for function 'list_calendars': schema must be a JSON Schema of 'type: "object"'`

**Causa:** A tool `list_calendars` do MCP Server não define parâmetros, gerando schema inválido que o GPT-4o rejeita.

**Solução:** Filtrar as tools do MCP para expor apenas as que têm schema válido:
```python
tools_permitidas = ["create_event", "list_events", "update_event", "delete_event"]
mcp_tools_filtradas = [t for t in mcp_tools if t.name in tools_permitidas]
```

---

## 13. Token do MCP incompatível com SDK Python do Google

**Problema:** O `calendar_tool.py` não conseguia autenticar usando o token gerado pelo MCP Server.

**Causa:** O MCP Server gera o token em formato próprio (`mcp-google-calendar-token.json`) incompatível com o formato esperado pelo SDK Python `google-auth`.

**Solução:** Gerar um token separado no formato correto:
```python
from google_auth_oauthlib.flow import InstalledAppFlow
SCOPES = ['https://www.googleapis.com/auth/calendar']
flow = InstalledAppFlow.from_client_secrets_file('credentials/credentials.json', SCOPES)
creds = flow.run_local_server(port=0)
with open('credentials/token_python.json', 'w') as f:
    f.write(creds.to_json())
```

---

## 14. Ollama sem memória RAM suficiente para modelos maiores

**Problema:** `ResponseError: model requires more system memory (2.7 GiB) than is available (2.3 GiB)`

**Causa:** O `llama3.1:8b` exige 2.7GB de RAM livre, mas o sistema estava com 83% de uso — principalmente Chrome (2.3GB) e Ollama (3.8GB).

**Solução:** Fechar o Chrome para liberar RAM. Para sistemas com pouca memória, usar `llama3.2` (2GB) ou `llama3.2:1b` (900MB). Para melhor qualidade de tool calling, migrar para GPT-4o via API.

---

## 15. Modelos locais pequenos não seguem tool calling corretamente

**Problema:** `llama3.2` entrava em loop ao tentar registrar exercícios — perguntava a mesma coisa repetidamente sem invocar a tool.

**Causa:** Modelos menores têm dificuldade com tool calling multi-parâmetro e raciocínio multi-turno. O `llama3.2` (3B parâmetros) não é suficientemente capaz para seguir instruções complexas de tools.

**Solução:** Migrar para GPT-4o que tem tool calling nativo e robusto:
```python
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o", temperature=0)
```

---

## 16. Histórico corrompido no SQLite causando loop

**Problema:** `ValueError: Found AIMessages with tool_calls that do not have a corresponding ToolMessage`

**Causa:** Uma tool foi invocada mas o processo foi interrompido antes de retornar o resultado. O SQLite salvou uma `AIMessage` com `tool_calls` sem a `ToolMessage` correspondente, corrompendo o histórico.

**Solução:** Deletar o `memory.db` para limpar o histórico corrompido:
```bash
del storage\memory.db
```
Em produção, implementar tratamento de erro para garantir que toda `tool_call` tenha uma `ToolMessage` correspondente antes de salvar o checkpoint.

---

## 17. GPT-4o alucinando artigos não existentes no acervo

**Problema:** O agente listava referências bibliográficas dos PDFs como se fossem artigos do acervo do usuário.

**Causa:** O ChromaDB retornava chunks que continham seções de referências bibliográficas dos artigos. O GPT-4o interpretava essas referências como artigos disponíveis.

**Solução:** Criar um `articles.json` como fonte de verdade estruturada dos artigos, separando metadados (JSON) de conteúdo semântico (ChromaDB). O agente consulta o JSON para saber quais artigos existem e o ChromaDB apenas para buscar conteúdo:
```
articles.json  →  controle de metadados e status
ChromaDB       →  busca semântica de conteúdo
```

---

## 18. Agente usando tool errada para LeetCode 75

**Problema:** Ao registrar exercícios do LeetCode 75, o agente usava `registrar_exercicio` (que salva no `leetcode.json`) em vez de `marcar_exercicio_leetcode75` (que atualiza o `leetcode75.json`).

**Causa:** O system prompt não deixava claro quando usar cada tool.

**Solução:** Adicionar instrução explícita no system prompt:
```
- When user says they completed a LeetCode 75 exercise, ALWAYS use marcar_exercicio_leetcode75
- Do NOT ask for difficulty or topic — that info is already in leetcode75.json
- For exercises outside LeetCode 75, use registrar_exercicio
```

---

## 19. `datetime.strftime` usado no lugar de `datetime.strptime`

**Problema:** `TypeError` ao tentar somar `timedelta` ao resultado de `datetime.strftime`.

**Causa:** `strftime` converte datetime → string. O código precisava do inverso: string → datetime (`strptime`).

**Solução:**
```python
# errado
inicio = datetime.strftime(data_inicio, "%Y-%m-%d %H:%M")

# correto
inicio = datetime.strptime(data_inicio, "%Y-%m-%d %H:%M")
fim = inicio + timedelta(minutes=duracao_minutos)
```

---

## 20. ChromaDB retendo chunks de artigos deletados

**Problema:** Após deletar PDFs da pasta `data/articles/`, o ChromaDB continuava retornando chunks dos arquivos removidos.

**Causa:** O `Chroma.from_documents` adiciona/atualiza documentos mas não remove chunks de arquivos que não estão mais na pasta.

**Solução:** Recriar o índice do zero a cada execução do `ingest.py`:
```python
import shutil
if os.path.exists("./chroma_db"):
    shutil.rmtree("./chroma_db")

Chroma.from_documents(documents=chunks, embedding=embeddings, ...)
```