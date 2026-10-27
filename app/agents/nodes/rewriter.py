import logfire
from langchain_groq import ChatGroq

from app.agents.state import AgentState
from app.config import settings

# Same fast model as planner/grader for a cheap, deterministic rewrite.
llm = ChatGroq(
    model=settings.GROQ_MODEL,
    api_key=settings.GROQ_API_KEY,
    temperature=0
)


def _clean(text: str) -> str:
    """Strip wrapping quotes/backticks the model may add around the query."""
    cleaned = text.strip().strip('"').strip("'").strip("`").strip()
    return cleaned


def rewrite_node(state: AgentState):
    """
    Corrective-RAG rewriter. When retrieval is graded irrelevant, reformulate
    the search query to surface better context on the next retrieval attempt.

    Increments retry_count so the graph's routing edge can bound the loop.
    """
    query = state.get("current_query", "")
    retries = state.get("retry_count", 0)
    user_msg = state["messages"][-1]["content"] if state.get("messages") else query

    with logfire.span("♻️ Query Rewrite", attempt=retries + 1, current_query=query):
        prompt = f"""A technical RAG system failed to retrieve useful context for a question.

ORIGINAL USER QUESTION:
"{user_msg}"

CURRENT SEARCH QUERY (returned irrelevant documents):
"{query}"

Rewrite the search query to retrieve better documentation. Use different
keywords, expand acronyms, or add technical synonyms.

Return ONLY the rewritten search query — no quotes, no explanation, no prefix.
"""

        try:
            rewritten = _clean(llm.invoke(prompt).content)
        except Exception as e:
            logfire.error(f"Rewrite LLM failed: {e} — keeping current query.")
            rewritten = query

        if not rewritten:
            rewritten = query

        logfire.info(f"Rewrote query: '{query}' -> '{rewritten}'")

    return {
        "current_query": rewritten,
        "retry_count": retries + 1,
        "status": f"Reformulating search (attempt {retries + 2})...",
        "plan": state["plan"] + [f"Query rewrite #{retries + 1}: {rewritten}"],
    }
