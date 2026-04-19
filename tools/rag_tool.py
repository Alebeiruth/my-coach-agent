from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.tools.retriever import create_retriever_tool
from pathlib import Path
from langchain_core.tools import tool

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-large-en-v1.5",
    model_kwargs={"device": "cpu"},
)

vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings,
    collection_name="artigos",  # precisa bater com o que foi indexado
)

retriever = vectorstore.as_retriever(
    search_type="similarity", # pergunta sobre
    search_kwargs={"k": 4}, # pergunta sobre
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

@tool
def listar_artigos() -> str:
    """
    Lista todos os artigos científicos disponíveis no acervo do usuário.
    SEMPRE use esta tool primeiro quando o usuário perguntar sobre artigos disponíveis
    ou quiser agendar uma sessão de estudo de um artigo específico.
    """
    pasta = Path("data/articles")
    print(f"[DEBUG PATH] Procurando em: {pasta.resolve()}")
    pdfs = list(pasta.glob("*.pdf"))
    print(f"[DEBUG PATH] PDFs encontrados: {pdfs}")

    if not pdfs:
        return "Nenhum artigo encontrado no acervo."

    nomes = "\n".join(f"- {p.stem}" for p in pdfs)
    return f"Artigos disponíveis no acervo ({len(pdfs)}):\n{nomes}"