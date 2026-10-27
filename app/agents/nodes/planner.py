from app.agents.state import AgentState 
from app.config import settings 
from langchain_groq import ChatGroq 
import logfire 

#Portkey-backed LLM: fallback + cache + retry — same .invoke() interface as ChatGroq
# get_langchain_llm = None
# def get_langchain_llm(feature: str):
#     pass
llm = ChatGroq(
    model=settings.GROQ_MODEL,
    api_key=settings.GROQ_API_KEY,
    temperature=0
)

def planner_node(state: AgentState):
    """
    The Planner determines if a search is needed based on the ENTIRE conversation.
    """
    # Get the conversation history (excluding the latest message)
    history = ""
    for msg in state["messages"][:-1]:
        role = "User" if msg["role"] == "user" else "Assistant"
        history += f"{role}: {msg['content']}\n"
    
    user_message = state["messages"][-1]["content"] if state["messages"] else ""
    
    prompt = f"""
    You are an intelligent Assistant Planner. 
    Analyze the conversation history and the latest user message.
    
    CONVERSATION HISTORY:
    {history}
    
    LATEST MESSAGE:
    "{user_message}"
    
    Task:
    1. Respond with 'CONVERSATIONAL' ONLY if the latest message is a greeting (hi, hello),
small talk, or a question answerable using ONLY the conversation history above
(e.g., "what is my name", "what did I just ask").
    2. Otherwise treat it as a technical question that needs documentation and output a
refined search query. The knowledge base covers: databases (SQL, NoSQL, ACID, CAP,
indexing, transactions, query optimisation), Python and backend APIs, data structures
and algorithms, frontend, machine learning and deep learning, MLOps and data
engineering, RAG and agentic AI, Kubernetes, cloud and DevOps, networking, and
systems/OS internals.

    When in doubt, prefer a search query over 'CONVERSATIONAL'.

    Output ONLY 'CONVERSATIONAL' or the search query (no JSON, no quotes, no explanation).
    """
    
    with logfire.span("🧠 Planner Decision"):
        decision = llm.invoke(prompt).content.strip()
        logfire.info(f"Intent identified: {decision}")
    
    # The model sometimes wraps or punctuates the sentinel ("CONVERSATIONAL.", 'CONVERSATIONAL')
    # — normalise it, otherwise the sentinel itself gets searched for as a query.
    cleaned = decision.strip().strip("\"'`.").strip()

    if cleaned.upper() == "CONVERSATIONAL":
        return {
            "current_query": "CONVERSATIONAL",
            "status": "Handling conversationally (using memory)...",
            "plan": ["Intent: Conversational/Memory", "Retrieval: Skipped"]
        }

    search_query = cleaned or decision

    return {
        "current_query": search_query,
        "status": f"Technical research needed. Searching for: {search_query}",
        "plan": ["Intent: Technical", f"Search Term: {search_query}"]
    }