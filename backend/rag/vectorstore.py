import os
from sqlalchemy.ext.asyncio import create_async_engine
from langchain_postgres.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()


def _build_async_url() -> str:
    url = os.getenv("DATABASE_URL_ASYNC") or os.getenv("DATABASE_URL", "")
    if not url:
        return "postgresql+asyncpg://postgres:password@localhost:5432/nexus"
    # Strip pgbouncer=true and other params asyncpg doesn't support
    url = url.split("?")[0]
    # Normalise driver prefix to asyncpg
    for prefix in ("postgresql+psycopg2://", "postgresql+psycopg://", "postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+asyncpg://" + url[len(prefix):]
    return url


_ASYNC_URL = _build_async_url()
_engine = None
_stores: dict[str, PGVector] = {}
_embeddings = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(_ASYNC_URL, pool_pre_ping=True, pool_size=5, max_overflow=5)
    return _engine


def get_embeddings() -> OpenAIEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return _embeddings


def get_vectorstore(session_id: str) -> PGVector:
    if session_id not in _stores:
        _stores[session_id] = PGVector(
            embeddings=get_embeddings(),
            collection_name=f"nexus_{session_id}",
            connection=_get_engine(),
            use_jsonb=True,
            create_extension=False,
        )
    return _stores[session_id]


def get_retriever(session_id: str, k: int = 6):
    return get_vectorstore(session_id).as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )


async def delete_collection(session_id: str) -> None:
    store = get_vectorstore(session_id)
    try:
        await store.adelete_collection()
    except Exception:
        pass
    _stores.pop(session_id, None)
