"""Run: python test_synthesizer.py"""
import asyncio, json
from agents.synthesizer import synthesize_report

TOPIC = "pgvector and vector databases in AI applications"

FINDINGS = [
    {
        "title": "pgvector Overview",
        "finding": "pgvector is a PostgreSQL extension for vector similarity search. It supports HNSW and IVFFlat indexing, cosine and Euclidean distance metrics, and integrates seamlessly with SQL queries.",
        "sources": ["https://github.com/pgvector/pgvector", "https://supabase.com/docs/guides/database/extensions/pgvector"],
    },
    {
        "title": "Use Cases in AI",
        "finding": "Vector databases power semantic search, RAG pipelines, recommendation systems, and anomaly detection. pgvector enables all of these within an existing PostgreSQL deployment, reducing infrastructure complexity.",
        "sources": ["https://www.datacamp.com/tutorial/pgvector-tutorial", "https://severalnines.com/blog/vector-similarity-search-with-postgresqls-pgvector-a-deep-dive"],
    },
]


async def main():
    print(f"Synthesizing report on: {TOPIC}\n")
    print("=" * 60)

    report = ""
    async for event in synthesize_report(TOPIC, FINDINGS):
        for line in event.strip().split("\n"):
            if line.startswith("event:"):
                etype = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data = json.loads(line.split(":", 1)[1].strip())
                if etype == "agent_start":
                    print("[Synthesizer streaming...]\n")
                elif etype == "report_chunk":
                    chunk = data["chunk"]
                    report += chunk
                    print(chunk, end="", flush=True)
                elif etype == "agent_complete":
                    print("\n" + "=" * 60)
                    print(f"\nTotal report length: {len(report)} chars")

    print("\nSynthesizer test passed.")


if __name__ == "__main__":
    asyncio.run(main())
