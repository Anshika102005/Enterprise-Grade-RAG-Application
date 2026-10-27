import logfire
from app.agents.state import AgentState
from app.config import settings
from app.services.Retrieval.qdrant_service import (
    RetrievalUnavailableError,
    search_enterprise_knowledge,
)
from app.services.Retrieval.ranking_service import rerank_documents

def retrieve_node(state: AgentState):
    """
    Hybrid retrieval (dense + BM25 → RRF) followed by cross-encoder reranking.
    Re-runs on each Self-RAG rewrite attempt with the reformulated query.
    """
    query = state["current_query"]
    attempt = state.get("retry_count", 0)

    with logfire.span("🔍 Knowledge Retrieval", attempt=attempt + 1):
        logfire.info(f"Searching Qdrant for: {query}")
        try:
            raw_results = search_enterprise_knowledge(
                query, limit=settings.RETRIEVAL_FUSED_TOP_K
            )
        except RetrievalUnavailableError as e:
            # The vector DB is unreachable — no amount of query rewriting will
            # help, so report the failure instead of posing as "no context".
            logfire.error(f"❌ Vector store unavailable: {e}")
            return {
                "documents": [],
                "retrieval_error": str(e),
                "status": "Vector store unavailable — answered without documentation.",
                "plan": state["plan"] + ["Retrieval failed: vector store unavailable"],
            }

        logfire.info(f"Retrieved {len(raw_results)} candidates from Vector DB")

        if not raw_results:
            # Qdrant answered and genuinely had nothing relevant.
            logfire.info("Vector store returned no matches.")
            return {
                "documents": [],
                "retrieval_error": "",
                "status": "No context found in the knowledge base.",
                "plan": state["plan"] + [f"Context Retrieved (attempt {attempt + 1})"],
            }

        doc_contents = [doc['content'] for doc in raw_results]

        with logfire.span("⚖️ Semantic Reranking"):
            reranked_contents = rerank_documents(
                query, doc_contents, top_n=settings.RERANK_TOP_N
            )
            logfire.info(f"Reranking complete. Kept top {settings.RERANK_TOP_N} chunks.")

        formatted_docs = [f"CONTENT: {doc}" for doc in reranked_contents]

    return {
        "documents": formatted_docs,
        "retrieval_error": "",
        "status": "Found technical context.",
        "plan": state["plan"] + [f"Context Retrieved (attempt {attempt + 1})"],
    }
