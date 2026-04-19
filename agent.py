import os
import asyncio
from datetime import datetime
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.tools.retriever import create_retriever_tool
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_mcp_adapters.client import MultiServerMCPClient
from tools import (
    rag_tool,
    listar_artigos,
    atualizar_status_artigo,
    adicionar_artigo,
    consultar_artigo,
    agendar_sessao,
    registrar_exercicio,
    consultar_progresso,
    sugerir_proximo_exercicio,
    consultar_leetcode75,
    marcar_exercicio_leetcode75,
    proximo_leetcode75,
)
from dotenv import load_dotenv
load_dotenv()

os.makedirs("storage", exist_ok=True)

# ── Retriever RAG ──────────────────────────────────────────────────────────
embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-large-en-v1.5",
    model_kwargs={"device": "cpu"},
)

vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings,
    collection_name="artigos",
)

retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 4},
)

rag_tool = create_retriever_tool(
    retriever=retriever,
    name="buscar_artigos",
    description=(
        "Use para buscar conteúdo dos artigos científicos indexados. "
        "Use quando o usuário perguntar sobre um tema, pedir sugestão de leitura "
        "ou quiser agendar estudo de um artigo específico."
    ),
)

# ── Tools Python ───────────────────────────────────────────────────────────
python_tools = [
    rag_tool,
    listar_artigos,
    atualizar_status_artigo,
    adicionar_artigo,
    consultar_artigo,
    agendar_sessao,
    registrar_exercicio,
    consultar_progresso,
    sugerir_proximo_exercicio,
    consultar_leetcode75,
    marcar_exercicio_leetcode75,
    proximo_leetcode75,
]

# ── System prompt ──────────────────────────────────────────────────────────
system_prompt = f"""REGRA CRÍTICA: Você JAMAIS deve mencionar, sugerir ou citar artigos que não foram retornados pela tool listar_artigos.

You are Alexandre's personal AI coach. You help him with two goals in 2025:

1. ENGLISH via scientific articles:
   - ALWAYS call listar_artigos first to list available articles
   - The result of listar_artigos IS the acervo — trust it completely
   - When user mentions an article name, find the closest match in listar_artigos result
   - When article and time are confirmed, call agendar_sessao IMMEDIATELY with tipo='artigo'
   - Do NOT call listar_artigos or buscar_artigos again after user confirms scheduling
   - data_inicio format: 'YYYY-MM-DD HH:MM'
   - Today is {datetime.now().strftime('%Y-%m-%d')}

2. LEETCODE practice:
   - When user says they completed a LeetCode 75 exercise, ALWAYS use marcar_exercicio_leetcode75, NOT registrar_exercicio
   - marcar_exercicio_leetcode75 requires only: titulo (partial match ok) and status='resolvido' — do NOT ask for difficulty or topic
   - For exercises outside LeetCode 75, use registrar_exercicio and ask for: title, difficulty, topic and observations
   - Show progress using consultar_progresso
   - Use consultar_leetcode75 to check LeetCode 75 progress
   - Use proximo_leetcode75 to suggest next LeetCode 75 exercise
   - Schedule practice sessions using agendar_sessao with tipo='leetcode'

Behavior rules:
- When user says 'sim', 'yes', 'confirma', 'pode', call agendar_sessao IMMEDIATELY
- Respond in Portuguese, but keep article titles and LeetCode exercise names in English
- Be direct and objective — Alexandre is a developer, skip unnecessary explanations
- You have memory of previous conversations — use this context to personalize your suggestions
- NEVER hallucinate articles, references or data that were not retrieved from tools"""

# ── Memória de longo prazo ─────────────────────────────────────────────────
memory = AsyncSqliteSaver.from_conn_string("storage/memory.db")


# ── Loop principal com MCP ─────────────────────────────────────────────────
async def main():
    async with AsyncSqliteSaver.from_conn_string("storage/memory.db") as memory:
        mcp_client = MultiServerMCPClient(
            {
                "google-calendar": {
                    "command": r"C:\Program Files\nodejs\npx.cmd",
                    "args": ["-y", "mcp-google-calendar"],
                    "transport": "stdio",
                    "cwd": str(os.path.abspath("./credentials")),
                }
            }
        )

        mcp_tools = await mcp_client.get_tools()
        # filtra só as tools que o agente precisa
        tools_permitidas = ["create_event", "list_events", "update_event", "delete_event"]
        mcp_tools_filtradas = [t for t in mcp_tools if t.name in tools_permitidas]

        all_tools = python_tools + mcp_tools_filtradas
        
        # lm = ChatOllama(model="llama3.2", temperature=0) <- 1 modelo
        # llm = ChatOllama(model="llama3.1:8b", temperature=0) <- 2 modelo
        llm = ChatOpenAI(model="gpt-4o", temperature=0)


        agent = create_react_agent(
            model=llm,
            tools=all_tools,
            prompt=system_prompt,
            checkpointer=memory,
        )

        config = {"configurable": {"thread_id": "alexandre-coach"}}

        print("Personal AI Coach ativo. Digite 'sair' para encerrar.\n")

        while True:
            user_input = input("Alexandre: ").strip()

            if not user_input:
                continue

            if user_input.lower() == "sair":
                break

            print("\nCoach: ", end="", flush=True)

            async for chunk in agent.astream(
                {"messages": [HumanMessage(content=user_input)]},
                config=config,
                stream_mode="values",
            ):
                last_message = chunk["messages"][-1]
                if isinstance(last_message, AIMessage) and last_message.content:
                    print(last_message.content, end="", flush=True)

        print("\n")


if __name__ == "__main__":
    asyncio.run(main())