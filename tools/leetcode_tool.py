import json
import os
from datetime import datetime
from langchain_core.tools import tool

STORAGE_FILE = "storage/leetcode.json"
LEETCODE75_FILE = "storage/leetcode75.json"


# ── Helpers ────────────────────────────────────────────────────────────────

def _load() -> dict:
    if not os.path.exists(STORAGE_FILE):
        return {"exercises": [], "checklist": []}
    with open(STORAGE_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return {"exercises": [], "checklist": []}
        return json.loads(content)


def _save(data: dict):
    os.makedirs("storage", exist_ok=True)
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load75() -> dict:
    if not os.path.exists(LEETCODE75_FILE):
        return {"total": 0, "exercises": []}
    with open(LEETCODE75_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return {"total": 0, "exercises": []}
        return json.loads(content)


def _save75(data: dict):
    os.makedirs("storage", exist_ok=True)
    with open(LEETCODE75_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Tool 1: registrar exercício livre ──────────────────────────────────────

@tool
def registrar_exercicio(
    titulo: str,
    dificuldade: str,
    topico: str,
    status: str = "resolvido",
    observacoes: str = "",
) -> str:
    """
    Registra um exercício do LeetCode feito pelo usuário.

    Args:
        titulo: Nome ou número do exercício. Exemplo: 'Two Sum' ou '1. Two Sum'.
        dificuldade: 'easy', 'medium' ou 'hard'.
        topico: Tópico do exercício. Exemplo: 'arrays', 'dynamic programming', 'graphs'.
        status: 'resolvido', 'tentado' ou 'revisitar'. Padrão: 'resolvido'.
        observacoes: Anotações sobre a solução ou dificuldades encontradas.

    Returns:
        Confirmação do registro.
    """
    data = _load()
    exercicio = {
        "titulo": titulo,
        "dificuldade": dificuldade,
        "topico": topico,
        "status": status,
        "observacoes": observacoes,
        "data": datetime.now().strftime("%Y-%m-%d"),
    }
    data["exercises"].append(exercicio)
    _save(data)
    return f"Exercício '{titulo}' registrado com sucesso em {exercicio['data']}."


# ── Tool 2: consultar progresso livre ──────────────────────────────────────

@tool
def consultar_progresso() -> str:
    """
    Retorna o progresso completo do usuário no LeetCode:
    total de exercícios, breakdown por dificuldade e por tópico.
    Use quando o usuário perguntar sobre seu progresso ou histórico.
    """
    data = _load()
    exercises = data["exercises"]

    if not exercises:
        return "Nenhum exercício registrado ainda."

    total = len(exercises)
    por_dificuldade = {}
    por_topico = {}

    for ex in exercises:
        d = ex.get("dificuldade", "desconhecido")
        t = ex.get("topico", "desconhecido")
        por_dificuldade[d] = por_dificuldade.get(d, 0) + 1
        por_topico[t] = por_topico.get(t, 0) + 1

    topicos_str = "\n".join(f"  - {t}: {c}" for t, c in sorted(por_topico.items()))
    dific_str = "\n".join(f"  - {d}: {c}" for d, c in sorted(por_dificuldade.items()))

    return (
        f"Total de exercícios registrados: {total}\n\n"
        f"Por dificuldade:\n{dific_str}\n\n"
        f"Por tópico:\n{topicos_str}"
    )


# ── Tool 3: sugerir próximo exercício livre ────────────────────────────────

@tool
def sugerir_proximo_exercicio() -> str:
    """
    Analisa o histórico e sugere o próximo tópico ou exercício a estudar.
    Use quando o usuário pedir sugestão do que praticar no LeetCode.
    """
    data = _load()
    exercises = data["exercises"]

    if not exercises:
        return (
            "Você ainda não registrou exercícios. "
            "Sugiro começar com Arrays - Easy: '1. Two Sum', '26. Remove Duplicates from Sorted Array'."
        )

    topicos = {}
    for ex in exercises:
        t = ex.get("topico", "desconhecido")
        topicos[t] = topicos.get(t, 0) + 1

    roadmap = [
        "arrays", "strings", "hash maps", "two pointers",
        "sliding window", "stack", "binary search",
        "linked lists", "trees", "graphs", "dynamic programming",
    ]

    for topico in roadmap:
        if topicos.get(topico, 0) < 5:
            feitos = topicos.get(topico, 0)
            return (
                f"Recomendo focar em '{topico}' — você tem {feitos} exercício(s) nesse tópico. "
                f"Meta sugerida: 5 exercícios por tópico antes de avançar."
            )

    return "Excelente progresso! Você cobriu os tópicos fundamentais. Parta para Dynamic Programming avançado."


# ── Tool 4: consultar LeetCode 75 ─────────────────────────────────────────

@tool
def consultar_leetcode75(topico: str = "") -> str:
    """
    Consulta os exercícios do LeetCode 75 — os 75 exercícios mais cobrados em entrevistas.
    Mostra progresso geral ou filtra por tópico específico.

    Args:
        topico: Tópico para filtrar. Deixe vazio para ver o progresso geral.
                Tópicos disponíveis: 'Array / String', 'Two Pointers', 'Sliding Window',
                'Prefix Sum', 'Hash Map / Set', 'Stack', 'Queue', 'Linked List',
                'Binary Tree - DFS', 'Binary Tree - BFS', 'Binary Search Tree',
                'Graphs - DFS', 'Graphs - BFS', 'Heap / Priority Queue',
                'Binary Search', 'Backtracking', 'DP - 1D', 'DP - Multidimensional',
                'Bit Manipulation', 'Trie', 'Intervals', 'Monotonic Stack'.

    Returns:
        Progresso geral ou lista de exercícios do tópico solicitado.
    """
    data = _load75()
    exercises = data.get("exercises", [])

    if not exercises:
        return "Arquivo leetcode75.json não encontrado em storage/. Adicione o arquivo para usar esta feature."

    if topico:
        # filtra por tópico (case-insensitive)
        filtrados = [e for e in exercises if topico.lower() in e["topico"].lower()]
        if not filtrados:
            return f"Tópico '{topico}' não encontrado. Verifique os tópicos disponíveis."

        linhas = [f"📚 Tópico: {filtrados[0]['topico']}\n"]
        for e in filtrados:
            emoji = "✅" if e["status"] == "resolvido" else "⏳" if e["status"] == "tentado" else "🔁" if e["status"] == "revisitar" else "⬜"
            linhas.append(f"{emoji} [{e['dificuldade'].upper()}] {e['titulo']}")

        resolvidos = sum(1 for e in filtrados if e["status"] == "resolvido")
        linhas.append(f"\nProgresso: {resolvidos}/{len(filtrados)} resolvidos")
        return "\n".join(linhas)

    else:
        # progresso geral
        total = len(exercises)
        resolvidos = sum(1 for e in exercises if e["status"] == "resolvido")
        tentados = sum(1 for e in exercises if e["status"] == "tentado")
        pendentes = sum(1 for e in exercises if e["status"] == "pendente")

        # breakdown por tópico
        topicos = {}
        for e in exercises:
            t = e["topico"]
            if t not in topicos:
                topicos[t] = {"total": 0, "resolvidos": 0}
            topicos[t]["total"] += 1
            if e["status"] == "resolvido":
                topicos[t]["resolvidos"] += 1

        topicos_str = "\n".join(
            f"  - {t}: {v['resolvidos']}/{v['total']}"
            for t, v in topicos.items()
        )

        return (
            f"🎯 LeetCode 75 — Progresso Geral\n\n"
            f"Total: {resolvidos}/{total} resolvidos\n"
            f"Tentados: {tentados}\n"
            f"Pendentes: {pendentes}\n\n"
            f"Por tópico:\n{topicos_str}"
        )


# ── Tool 5: marcar exercício do LeetCode 75 ───────────────────────────────

@tool
def marcar_exercicio_leetcode75(
    titulo: str,
    status: str,
    observacoes: str = "",
) -> str:
    """
    Marca um exercício do LeetCode 75 com um status específico.

    Args:
        titulo: Título exato ou parcial do exercício. Exemplo: 'Two Sum', 'Move Zeroes'.
        status: 'resolvido', 'tentado' ou 'revisitar'.
        observacoes: Anotações sobre a solução ou dificuldades encontradas.

    Returns:
        Confirmação da atualização.
    """
    data = _load75()
    exercises = data.get("exercises", [])

    if not exercises:
        return "Arquivo leetcode75.json não encontrado em storage/."

    # busca por título (case-insensitive, partial match)
    encontrados = [e for e in exercises if titulo.lower() in e["titulo"].lower()]

    if not encontrados:
        return f"Exercício '{titulo}' não encontrado no LeetCode 75. Verifique o título."

    if len(encontrados) > 1:
        opcoes = "\n".join(f"  - {e['titulo']}" for e in encontrados)
        return f"Encontrei mais de um exercício com '{titulo}':\n{opcoes}\n\nSeja mais específico."

    exercicio = encontrados[0]
    exercicio["status"] = status
    exercicio["observacoes"] = observacoes
    exercicio["data_atualizacao"] = datetime.now().strftime("%Y-%m-%d")

    _save75(data)

    return (
        f"✅ '{exercicio['titulo']}' marcado como '{status}' em {exercicio['data_atualizacao']}.\n"
        f"Tópico: {exercicio['topico']} | Dificuldade: {exercicio['dificuldade'].upper()}"
    )


# ── Tool 6: próximo exercício do LeetCode 75 ──────────────────────────────

@tool
def proximo_leetcode75() -> str:
    """
    Sugere o próximo exercício pendente do LeetCode 75 seguindo a ordem oficial.
    Use quando o usuário perguntar o que estudar a seguir no LeetCode 75.

    Returns:
        Próximo exercício pendente com tópico e dificuldade.
    """
    data = _load75()
    exercises = data.get("exercises", [])

    if not exercises:
        return "Arquivo leetcode75.json não encontrado em storage/."

    pendentes = [e for e in exercises if e["status"] == "pendente"]

    if not pendentes:
        return "🏆 Parabéns! Você completou todos os 75 exercícios do LeetCode 75!"

    proximo = pendentes[0]
    resolvidos = sum(1 for e in exercises if e["status"] == "resolvido")
    total = len(exercises)

    return (
        f"📌 Próximo exercício do LeetCode 75:\n\n"
        f"#{proximo['id']} — {proximo['titulo']}\n"
        f"Tópico: {proximo['topico']}\n"
        f"Dificuldade: {proximo['dificuldade'].upper()}\n\n"
        f"Progresso atual: {resolvidos}/{total} resolvidos"
    )