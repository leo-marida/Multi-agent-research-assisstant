from langchain_core.tools import tool
from rag.vectorstore import get_retriever


@tool
async def retrieve_context(query: str, session_id: str, k: int = 6) -> list[dict]:
    """Retrieve relevant document chunks from the vector store for a given query and session."""
    retriever = get_retriever(session_id, k=k)
    docs = await retriever.ainvoke(query)
    return [
        {
            "content": doc.page_content,
            "source_url": doc.metadata.get("source_url", ""),
            "title": doc.metadata.get("title", ""),
            "subtask_id": doc.metadata.get("subtask_id", ""),
        }
        for doc in docs
    ]
