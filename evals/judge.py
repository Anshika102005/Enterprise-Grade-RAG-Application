"""
Judge models for the eval harness.

Both RAGAS and DeepEval need an LLM (to act as the grader) and, for some
metrics, an embedding model. We route the judge LLM through Groq using a
dedicated JUDGE_GROQ key (so evaluation spend never eats production quota) and
reuse the project's local sentence-transformer for embeddings.
"""
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

from app.config import settings


# ── Shared base models ────────────────────────────────────────────────────────

def get_langchain_judge_llm() -> ChatGroq:
    """LangChain chat model used as the grader."""
    if not settings.JUDGE_API_KEY:
        raise RuntimeError(
            "No judge API key. Set JUDGE_GROQ (preferred) or GROQ_API_KEY in .env."
        )
    return ChatGroq(
        model=settings.JUDGE_MODEL,
        api_key=settings.JUDGE_API_KEY,
        temperature=0,
    )


def get_langchain_embeddings() -> HuggingFaceEmbeddings:
    """Local embeddings (same model the pipeline indexes with)."""
    return HuggingFaceEmbeddings(model_name=settings.HUGGINGFACE_EMBEDDING_MODEL)


# ── RAGAS wrappers ────────────────────────────────────────────────────────────

def get_ragas_llm():
    from ragas.llms import LangchainLLMWrapper

    return LangchainLLMWrapper(get_langchain_judge_llm())


def get_ragas_embeddings():
    from ragas.embeddings import LangchainEmbeddingsWrapper

    return LangchainEmbeddingsWrapper(get_langchain_embeddings())


# ── DeepEval custom models ────────────────────────────────────────────────────

def _deepeval_bases():
    from deepeval.models import DeepEvalBaseEmbeddingModel, DeepEvalBaseLLM

    return DeepEvalBaseLLM, DeepEvalBaseEmbeddingModel


DeepEvalBaseLLM, DeepEvalBaseEmbeddingModel = _deepeval_bases()


class GroqJudgeLLM(DeepEvalBaseLLM):
    """DeepEval-native wrapper around the Groq judge model."""

    def __init__(self, model: ChatGroq | None = None):
        self._model = model or get_langchain_judge_llm()

    def load_model(self):
        return self._model

    def generate(self, prompt: str) -> str:
        return self._model.invoke(prompt).content

    async def a_generate(self, prompt: str) -> str:
        result = await self._model.ainvoke(prompt)
        return result.content

    def get_model_name(self) -> str:
        return f"groq:{settings.JUDGE_MODEL}"


class LocalJudgeEmbeddings(DeepEvalBaseEmbeddingModel):
    """DeepEval-native wrapper around the local sentence-transformer."""

    def __init__(self, model: HuggingFaceEmbeddings | None = None):
        self._model = model or get_langchain_embeddings()

    def load_model(self):
        return self._model

    def embed_text(self, text: str) -> list[float]:
        return self._model.embed_query(text)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return self._model.embed_documents(texts)

    async def a_embed_text(self, text: str) -> list[float]:
        return self.embed_text(text)

    async def a_embed_texts(self, texts: list[str]) -> list[list[float]]:
        return self.embed_texts(texts)

    def get_model_name(self) -> str:
        return settings.HUGGINGFACE_EMBEDDING_MODEL
