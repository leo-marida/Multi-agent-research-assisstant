"""Run: python test_api.py  (while uvicorn is running in another terminal)"""
import httpx


def main():
    topic = "pgvector for AI applications"
    print(f"Sending research request: '{topic}'\n")
    print("=" * 60)

    with httpx.Client(timeout=300) as client:
        with client.stream(
            "POST",
            "http://127.0.0.1:8000/api/research",
            json={"topic": topic},
            headers={"Accept": "text/event-stream"},
        ) as response:
            print(f"HTTP status: {response.status_code}\n")
            for line in response.iter_lines():
                if line:
                    print(line)


if __name__ == "__main__":
    main()
