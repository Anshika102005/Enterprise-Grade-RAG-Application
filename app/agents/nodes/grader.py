import logfire
from langchain_groq import ChatGroq

from app.agents.state import AgentState
from app.agents.nodes.grading import parse_grade_response
from app.config import settings

# Cheap, fast model for the grading gate — same as the planner.
llm = ChatGroq(
    model=settings.GROQ_MODEL,
    api_key=settings.GROQ_API_KEY,
    temperature=0
)

# Max characters of each passage shown to the grader (token budget guard).
_PASSAGE_PREVIEW_CHARS = 800


def _strip_prefix(doc: str) -> str:
    """Remove the 'CONTENT: ' prefix added by the retriever."""
    return doc[len("CONTENT: "):] if doc.startswith("CONTENT: ") else doc


def grade_node(state: AgentState):
    """
    Self-RAG relevance gate. Scores each retrieved passage against the query
    and decides whether the context is good enough to answer.

    relevant   -> proceed to the responder
    irrelevant -> route back to the rewriter for another retrieval attempt
                  (bounded by settings.MAX_RETRIEVAL_RETRIES)
    """
    query = state["current_query"]
    documents = state.get("documents", []) or []

    with logfire.span("⚖️ Retrieval Grading", num_docs=len(documents)):
        if state.get("retrieval_error"):
            # Infrastructure failure, not a relevance problem — grading an empty
            # set would just mislabel it and trigger pointless rewrites.
            logfire.error("Vector store unavailable — skipping grading.")
            return {
                "retrieval_grade": "unavailable",
                "retrieval_confidence": 0.0,
                "status": "Vector store unavailable — answered without documentation.",
                "plan": state["plan"] + ["Grade: Skipped (vector store unavailable)"],
            }

        if not documents:
            logfire.info("No documents retrieved — marking context irrelevant.")
            return {
                "retrieval_grade": "irrelevant",
                "retrieval_confidence": 0.0,
                "status": "No context retrieved.",
                "plan": state["plan"] + ["Grade: No context"],
            }

        passages = "\n\n".join(
            f"[{i}] {_strip_prefix(doc)[:_PASSAGE_PREVIEW_CHARS]}"
            for i, doc in enumerate(documents)
        )

        prompt = f"""You are a strict retrieval relevance grader for a technical RAG system.

QUESTION:
"{query}"

CANDIDATE PASSAGES:
{passages}

Task:
Decide which passages contain information that is actually useful for answering
the QUESTION. A passage is relevant only if it helps answer the question (not
merely shares a topic).

Return ONLY a JSON object, no prose, in exactly this shape:
{{"relevant": [0, 2], "confidence": 0.0}}

- "relevant": indices of the useful passages (empty list if none are useful).
- "confidence": your confidence from 0.0 to 1.0.
"""

        try:
            verdict = llm.invoke(prompt).content
            relevant_idx, confidence = parse_grade_response(verdict, len(documents))
        except Exception as e:
            logfire.error(f"Grader LLM failed: {e} — failing open.")
            relevant_idx, confidence = list(range(len(documents))), 0.5

        if relevant_idx:
            filtered = [documents[i] for i in relevant_idx]
            grade = "relevant"
            logfire.info(
                f"✅ Context relevant: {len(filtered)}/{len(documents)} passages kept "
                f"(confidence={confidence:.2f})"
            )
        else:
            # Keep the originals so a retry-exhausted answer still has context.
            filtered = documents
            grade = "irrelevant"
            logfire.info(f"⚠️ Context graded irrelevant (confidence={confidence:.2f}).")

    return {
        "documents": filtered,
        "retrieval_grade": grade,
        "retrieval_confidence": confidence,
        "status": f"Retrieval graded: {grade}.",
        "plan": state["plan"] + [
            f"Grade: {grade} ({len(filtered)} passages, conf {confidence:.2f})"
        ],
    }
