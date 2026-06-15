import os
from sqlalchemy.ext.asyncio import create_async_engine
from langchain_postgres.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

# asyncpg driver for async operations
_ASYNC_URL = os.getenv(
    "DATABASE_URL_ASYNC",
    "postgresql+asyncpg://postgres:password@localhost:5432/nexus",
)


def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model="text-embedding-3-small")


def get_vectorstore(session_id: str) -> PGVector:
    engine = create_async_engine(_ASYNC_URL)
    return PGVector(
        embeddings=get_embeddings(),
        collection_name=f"nexus_{session_id}",
        connection=engine,
        use_jsonb=True,
        create_extension=False,
    )


def get_retriever(session_id: str, k: int = 6):
    return get_vectorstore(session_id).as_retriever(
        search_type="mmr",
        search_kwargs={"k": k, "fetch_k": k * 3},
    )


async def delete_collection(session_id: str) -> None:
    store = get_vectorstore(session_id)
    await store.adelete_collection()
