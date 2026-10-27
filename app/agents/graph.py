from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.agents.state import AgentState
from app.agents.nodes.planner import planner_node
from app.agents.nodes.retriever import retrieve_node
from app.agents.nodes.grader import grade_node
from app.agents.nodes.rewriter import rewrite_node
from app.agents.nodes.responder import generate_node
from app.config import settings


# 1. Initialize the State Graph
workflow = StateGraph(AgentState)


# 2. Define the Nodes
workflow.add_node("planner", planner_node)
workflow.add_node("retriever", retrieve_node)
workflow.add_node("grader", grade_node)
workflow.add_node("rewriter", rewrite_node)
workflow.add_node("responder", generate_node)

# 3. Define the Edges & Routing Logic
def route_planner(state: AgentState):
    """
    Routes the workflow based on the planner's decision.
    """
    if state["current_query"] == "CONVERSATIONAL":
        return "responder"
    return "retriever"


def route_grader(state: AgentState):
    """
    Self-RAG gate: only answer when the context is relevant, or when the
    rewrite budget is exhausted (bounded loop — prevents infinite retries).
    """
    grade = state.get("retrieval_grade", "relevant")
    retries = state.get("retry_count", 0)

    # A vector-DB outage is not fixable by reformulating the query — skip the
    # corrective loop and answer with the failure disclosed.
    if state.get("retrieval_error"):
        return "responder"

    if grade == "relevant" or retries >= settings.MAX_RETRIEVAL_RETRIES:
        return "responder"
    return "rewriter"


workflow.set_entry_point("planner")


# Conditional Edge: Planner -> Router -> (Retriever OR Responder)
workflow.add_conditional_edges(
    "planner",
    route_planner,
    {
        "retriever": "retriever",
        "responder": "responder"
    }
)


# Corrective loop: retriever -> grader -> (rewriter -> retriever) OR responder
workflow.add_edge("retriever", "grader")
workflow.add_conditional_edges(
    "grader",
    route_grader,
    {
        "rewriter": "rewriter",
        "responder": "responder"
    }
)
workflow.add_edge("rewriter", "retriever")

workflow.add_edge("responder", END)


# --- MEMORY UPGRADE ---
# MemorySaver allows the agent to remember conversations based on 'thread_id'
checkpointer = MemorySaver()


# 4. Compile the Graph with Memory
rag_agent = workflow.compile(checkpointer=checkpointer)