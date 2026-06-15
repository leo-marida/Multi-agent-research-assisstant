from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from .vectorstore import get_vectorstore

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
)


async def ingest_content(
    content: str,
    session_id: str,
    metadata: dict,
) -> int:
    content = content.replace("\x00", "")
    doc = Document(page_content=content, metadata=metadata)
    chunks = _splitter.split_documents([doc])
    if not chunks:
        return 0
    store = get_vectorstore(session_id)
    await store.aadd_documents(chunks)
    return len(chunks)
