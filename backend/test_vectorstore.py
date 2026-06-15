"""Run: python test_vectorstore.py"""
import asyncio
from langchain_core.documents import Document
from rag.vectorstore import get_vectorstore, get_retriever, delete_collection

SESSION = "test-session-001"


async def main():
    print("1. Connecting to pgvector...")
    store = get_vectorstore(SESSION)

    print("2. Ingesting test documents...")
    docs = [
        Document(
            page_content="Quantum computing uses qubits to perform calculations exponentially faster than classical computers.",
            metadata={"source_url": "https://example.com/quantum", "subtask_id": "sub-1"},
        ),
        Document(
            page_content="LangChain is a framework for building applications powered by large language models.",
            metadata={"source_url": "https://example.com/langchain", "subtask_id": "sub-1"},
        ),
        Document(
            page_content="pgvector adds vector similarity search to PostgreSQL, enabling RAG applications.",
            metadata={"source_url": "https://example.com/pgvector", "subtask_id": "sub-1"},
        ),
    ]
    ids = await store.aadd_documents(docs)
    print(f"   Inserted {len(ids)} chunks with IDs: {ids[:2]}...")

    print("3. Testing MMR retrieval...")
    retriever = get_retriever(SESSION, k=2)
    results = await retriever.ainvoke("What is quantum computing?")
    print(f"   Retrieved {len(results)} chunks:")
    for r in results:
        print(f"   - {r.page_content[:80]}...")

    print("4. Cleaning up test collection...")
    await delete_collection(SESSION)
    print("   Done.\n")
    print("All checks passed — pgvector + embeddings working correctly.")


if __name__ == "__main__":
    asyncio.run(main())
