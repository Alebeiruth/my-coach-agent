from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import fitz
import os

def load_pdfs(directory: str) -> list[dict]:
    docs = []
    for path in Path (directory).glob("*.pdf"):
        doc = fitz.open(str(path))
        text = "\n".join(page.get_text() for page in doc)
        docs.append({"text": text, "source": path.name})
    return docs

def chunk_docs(docs: list[dict]) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1024,
        chunk_overlap=100, # perguntar ao Claude o que é overlap
        length_function=len,
    )
    chunks = []
    for doc in docs:
        splits = splitter.create_documents(
            texts=[doc["text"]],
            metadatas=[{"source": doc["source"]}]
        )
        chunks.extend(splits)
    return chunks

def ingest():
    docs = load_pdfs("data/articles/")
    if not docs:
        print("Nenhum PDF encontrado em data/articles/")
        return
    chunks = chunk_docs(docs)

    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-large-en-v1.5",
        model_kwargs={"device": "cpu"},
    )

    # deleta a collection existente antes de recriar
    # garante que o ChromaDB reflete exatamente o que está na pasta
    import shutil
    if os.path.exists("./chroma_db"):
        shutil.rmtree("./chroma_db")

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="./chroma_db",
        collection_name="artigos",
    )
    print(f"{len(chunks)} chunks indexados — {len(docs)} arquivo(s) processado(s).")

if __name__ == "__main__":
    ingest()