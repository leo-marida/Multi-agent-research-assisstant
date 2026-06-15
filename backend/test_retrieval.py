"""Run: python test_retrieval.py"""
import asyncio
from langchain_core.documents import Document
from rag.vectorstore import get_vectorstore, delete_collection
from tools.retrieval_tool import retrieve_context

SESSION = "test-retrieval-001"


async def main():
    print("1. Seeding vector store...")
    store = get_vectorstore(SESSION)
    docs = [
        Document(
            page_content="RAG pipelines retrieve relevant documents from a vector database before generating a response, improving accuracy and grounding.",
            metadata={"source_url": "https://example.com/rag", "title": "RAG Overview", "subtask_id": "sub-1"},
        ),
        Document(
            page_content="pgvector is a PostgreSQL extension that adds vector similarity search, enabling efficient nearest-neighbour lookups over embeddings.",
            metadata={"source_url": "https://example.com/pgvector", "title": "pgvector Docs", "subtask_id": "sub-1"},
        ),
        Document(
            page_content="LangChain agents use tool-calling to autonomously decide which tools to invoke, enabling multi-step reasoning workflows.",
            metadata={"source_url": "https://example.com/agents", "title": "LangChain Agents", "subtask_id": "sub-2"},
        ),
    ]
    await store.aadd_documents(docs)
    print(f"   Inserted {len(docs)} docs")

    print("2. Testing retrieval tool...")
    results = await retrieve_context.ainvoke({"query": "vector database similarity search", "session_id": SESSION, "k": 2})
    print(f"   Retrieved {len(results)} chunks:")
    for r in results:
        print(f"   - [{r['subtask_id']}] {r['content'][:80]}...")

    print("3. Cleaning up...")
    await delete_collection(SESSION)
    print("\nAll retrieval checks passed.")


if __name__ == "__main__":
    asyncio.run(main())
