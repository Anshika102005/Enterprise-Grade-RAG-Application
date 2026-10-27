from typing import TypedDict, List, Annotated
import operator


class AgentState(TypedDict):
    # Using Annotated with operator.add ensures that messages 
    # are appended to the history rather than replaced.
    messages: Annotated[List[dict], operator.add]
    current_query: str
    documents: List[str]
    plan: List[str]
    status: str
    final_answer: str
    # --- Self-RAG corrective loop ---
    # Number of query-rewrite retries attempted so far (bounded by
    # settings.MAX_RETRIEVAL_RETRIES). Defaults to 0 in the graph entrypoint.
    retry_count: int
    # Grader verdict on the retrieved context: "relevant", "irrelevant", or
    # "unavailable" when the vector database could not be reached.
    retrieval_grade: str
    # Running confidence score reported by the grader (0.0 - 1.0).
    retrieval_confidence: float
    # Set when retrieval failed for infrastructure reasons (empty string when
    # the vector DB answered normally). Distinct from "no relevant results".
    retrieval_error: str
