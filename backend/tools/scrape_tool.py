import httpx
from bs4 import BeautifulSoup
from langchain_core.tools import tool

_MAX_CHARS = 8000
_TIMEOUT = 10
_SKIP_CONTENT_TYPES = ("application/pdf", "application/octet-stream", "image/", "video/", "audio/")


@tool
async def scrape_url(url: str) -> str:
    """Fetch and extract the main text content from a URL. Returns plain text up to 8000 characters."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; NexusBot/1.0)"},
            )
            response.raise_for_status()

        content_type = response.headers.get("content-type", "").lower()
        if any(ct in content_type for ct in _SKIP_CONTENT_TYPES):
            return f"[skipped: binary content type '{content_type}']"

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        lines = [ln for ln in text.splitlines() if len(ln.strip()) > 30]
        content = "\n".join(lines)[:_MAX_CHARS]

        # strip null bytes and other characters PostgreSQL UTF-8 rejects
        content = content.replace("\x00", "")

        return content or "[no content extracted]"

    except Exception as e:
        return f"[scrape error: {e}]"
