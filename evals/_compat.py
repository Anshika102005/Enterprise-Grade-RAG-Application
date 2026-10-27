"""
Import-order compatibility shim.

RAGAS 0.3.x imports ``langchain_community.chat_models.vertexai`` at module load.
That path was removed in langchain-community 0.4+, which breaks ``import ragas``.
The project already depends on ``langchain-google-vertexai`` (kept for NeMo
Guardrails), so we simply re-expose ``ChatVertexAI`` under the old import path
before anything imports ragas.

Import this module (``import evals._compat  # noqa: F401``) before ``import ragas``.
"""
import sys
import types


def apply() -> None:
    # Already importable? Nothing to do.
    try:
       from langchain_google_vertexai import ChatVertexAI # noqa: F401
       return
    except Exception:
        pass

    try:
        import langchain_google_vertexai as _vertexai

        shim = types.ModuleType("langchain_community.chat_models.vertexai")
        shim.ChatVertexAI = getattr(_vertexai, "ChatVertexAI", None)
        sys.modules["langchain_community.chat_models.vertexai"] = shim
    except Exception:
        # If even the standalone package is missing we let the caller surface
        # the real ragas import error rather than masking it.
        pass


apply()
