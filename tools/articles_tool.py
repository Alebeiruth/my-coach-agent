import json
import os
from datetime import datetime
from langchain_core.tools import tool

ARTICLES_FILE = "storage/articles.json"


# ── Helpers ────────────────────────────────────────────────────────────────

def _load() -> dict:
    if not os.path.exists(ARTICLES_FILE):
        return {"articles": []}
    with open(ARTICLES_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return {"articles": []}
        return json.loads(content)


def _save(data: dict):
    os.makedirs("storage", exist_ok=True)
    with open(ARTICLES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _find_article(titulo: str, articles: list) -> dict | None:
    """Busca artigo por título (case-insensitive, partial match)."""
    titulo_lower = titulo.lower()
    for a in articles:
        if titulo_lower in a["titulo"].lower():
            return a
    return None


# ── Tool 1: listar artigos ─────────────────────────────────────────────────

@tool
def listar_artigos(status: str = "") -> str:
    """
    Lista todos os artigos do acervo com seus status.
    Use esta tool SEMPRE que o usuário perguntar sobre artigos disponíveis,
    quiser agendar uma sessão de estudo ou perguntar o que está lendo.

    Args:
        status: Filtro opcional. Valores: 'pendente', 'lendo', 'lido'.
                Deixe vazio para listar todos.

    Returns:
        Lista de artigos com título, status e observações.
    """
    data = _load()
    articles = data.get("articles", [])

    if not articles:
        return "Nenhum artigo cadastrado no acervo."

    if status:
        articles = [a for a in articles if a["status"] == status]
        if not articles:
            return f"Nenhum artigo com status '{status}'."

    linhas = []
    for a in articles:
        emoji = "📖" if a["status"] == "lendo" else "✅" if a["status"] == "lido" else "⬜"
        linha = f"{emoji} [{a['status'].upper()}] {a['titulo']}"
        if a["observacoes"]:
            linha += f"\n   Obs: {a['observacoes']}"
        linhas.append(linha)

    total = len(data["articles"])
    lidos = sum(1 for a in data["articles"] if a["status"] == "lido")
    lendo = sum(1 for a in data["articles"] if a["status"] == "lendo")

    header = f"📚 Acervo: {lidos}/{total} lidos | {lendo} em leitura\n"
    return header + "\n".join(linhas)


# ── Tool 2: atualizar status do artigo ────────────────────────────────────

@tool
def atualizar_status_artigo(
    titulo: str,
    status: str,
    observacoes: str = "",
) -> str:
    """
    Atualiza o status de leitura de um artigo do acervo.

    Args:
        titulo: Título ou parte do título do artigo.
        status: Novo status. Valores: 'pendente', 'lendo', 'lido'.
        observacoes: Anotações sobre o artigo (opcional).

    Returns:
        Confirmação da atualização.
    """
    data = _load()
    artigo = _find_article(titulo, data["articles"])

    if not artigo:
        titulos = "\n".join(f"- {a['titulo']}" for a in data["articles"])
        return f"Artigo '{titulo}' não encontrado. Artigos disponíveis:\n{titulos}"

    status_validos = ["pendente", "lendo", "lido"]
    if status not in status_validos:
        return f"Status inválido. Use: {', '.join(status_validos)}"

    artigo["status"] = status
    if observacoes:
        artigo["observacoes"] = observacoes
    if status == "lendo" and not artigo["data_inicio"]:
        artigo["data_inicio"] = datetime.now().strftime("%Y-%m-%d")
    if status == "lido":
        artigo["data_conclusao"] = datetime.now().strftime("%Y-%m-%d")

    _save(data)
    return f"✅ '{artigo['titulo']}' atualizado para '{status}'."


# ── Tool 3: adicionar novo artigo ─────────────────────────────────────────

@tool
def adicionar_artigo(
    titulo: str,
    arquivo: str,
    observacoes: str = "",
) -> str:
    """
    Adiciona um novo artigo ao acervo.
    Use quando o usuário informar que adicionou um novo PDF ao acervo.

    Args:
        titulo: Título do artigo.
        arquivo: Nome do arquivo PDF. Exemplo: 'meu_artigo.pdf'.
        observacoes: Observações iniciais sobre o artigo (opcional).

    Returns:
        Confirmação do cadastro.
    """
    data = _load()

    # verifica se já existe
    existente = _find_article(titulo, data["articles"])
    if existente:
        return f"Artigo '{titulo}' já está cadastrado no acervo."

    novo_id = max((a["id"] for a in data["articles"]), default=0) + 1

    novo_artigo = {
        "id": novo_id,
        "titulo": titulo,
        "arquivo": arquivo,
        "status": "pendente",
        "data_inicio": None,
        "data_conclusao": None,
        "observacoes": observacoes,
    }

    data["articles"].append(novo_artigo)
    _save(data)

    return f"✅ Artigo '{titulo}' adicionado ao acervo com sucesso."


# ── Tool 4: consultar artigo específico ───────────────────────────────────

@tool
def consultar_artigo(titulo: str) -> str:
    """
    Retorna os detalhes de um artigo específico do acervo.
    Use para verificar status, datas e observações de um artigo.

    Args:
        titulo: Título ou parte do título do artigo.

    Returns:
        Detalhes completos do artigo.
    """
    data = _load()
    artigo = _find_article(titulo, data["articles"])

    if not artigo:
        titulos = "\n".join(f"- {a['titulo']}" for a in data["articles"])
        return f"Artigo '{titulo}' não encontrado. Artigos disponíveis:\n{titulos}"

    return (
        f"📄 {artigo['titulo']}\n"
        f"Status: {artigo['status'].upper()}\n"
        f"Arquivo: {artigo['arquivo']}\n"
        f"Início: {artigo['data_inicio'] or 'não iniciado'}\n"
        f"Conclusão: {artigo['data_conclusao'] or 'não concluído'}\n"
        f"Observações: {artigo['observacoes'] or 'nenhuma'}"
    )