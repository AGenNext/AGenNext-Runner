"""
Autonomyx Playwright Scraper Sidecar
FastAPI service — POST /scrape

Crawls a URL (single page or full site), extracts clean text per page,
calls LiteLLM to extract structured data, generates embeddings via Ollama,
stores everything in SurrealDB Cloud.

Endpoints:
  POST /scrape          → start a scrape job (returns job_id)
  GET  /job/{job_id}    → poll job status + results
  GET  /health          → health check
"""

import os, json, re, time, uuid, asyncio, logging
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("playwright-scraper")

app = FastAPI(title="Autonomyx Playwright Scraper", version="1.0.0")

# ── Config ────────────────────────────────────────────────────────────────

LITELLM_URL   = os.environ.get("LITELLM_URL",   "http://litellm:4000")
LITELLM_KEY   = os.environ.get("LITELLM_KEY",   "")
OLLAMA_URL    = os.environ.get("OLLAMA_URL",    "http://ollama:11434")
SURREAL_URL   = os.environ.get("SURREAL_URL",   "")   # SurrealDB Cloud URL
SURREAL_USER  = os.environ.get("SURREAL_USER",  "root")
SURREAL_PASS  = os.environ.get("SURREAL_PASS",  "")
SURREAL_NS    = os.environ.get("SURREAL_NS",    "autonomyx")
SURREAL_DB    = os.environ.get("SURREAL_DB",    "scrapes")
EMBED_MODEL   = os.environ.get("EMBED_MODEL",   "nomic-embed-text")
EXTRACT_MODEL = os.environ.get("EXTRACT_MODEL", "ollama/qwen3:30b-a3b")
MAX_PAGES     = int(os.environ.get("MAX_PAGES", "50"))
CHUNK_SIZE    = int(os.environ.get("CHUNK_SIZE", "512"))

# In-memory job store
jobs: dict[str, dict] = {}


# ── Models ────────────────────────────────────────────────────────────────

class ScrapeRequest(BaseModel):
    url: str
    depth: int = 0              # 0=single page, -1=full site, N=N levels deep
    max_pages: int = 50
    extract_schema: Optional[dict] = None   # custom JSON schema to extract
    collection_name: Optional[str] = None   # SurrealDB table name
    tenant_id: Optional[str] = None         # for multi-tenant isolation
    respect_robots: bool = True
    chunk_size: int = 512

class ScrapeStatus(BaseModel):
    job_id: str
    status: str                  # pending | running | done | failed
    url: str
    pages_found: int
    pages_scraped: int
    chunks_embedded: int
    collection: str
    errors: list[str]
    result_summary: Optional[dict] = None


# ── Core: Playwright crawl ────────────────────────────────────────────────

async def crawl(url: str, depth: int, max_pages: int, respect_robots: bool) -> list[dict]:
    """
    Crawl URL with Playwright. Returns list of {url, title, text, links}.
    depth=0: single page. depth=-1: full site. depth=N: N levels.
    """
    from playwright.async_api import async_playwright

    visited   = set()
    to_visit  = [(url, 0)]
    results   = []
    base_host = urlparse(url).netloc

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--no-first-run",
            ]
        )
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (compatible; AutonomyxBot/1.0; +https://openautonomyx.com/bot)",
            java_script_enabled=True,
        )
        # Block images, fonts, media — faster, cheaper
        await ctx.route("**/*.{png,jpg,jpeg,gif,svg,webp,woff,woff2,ttf,mp4,mp3}",
                        lambda route: route.abort())

        while to_visit and len(results) < max_pages:
            current_url, current_depth = to_visit.pop(0)
            if current_url in visited:
                continue
            visited.add(current_url)

            try:
                page = await ctx.new_page()
                await page.goto(current_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(1000)   # let JS render

                # Extract text
                title = await page.title()
                text  = await page.evaluate("""() => {
                    // Remove nav, footer, scripts, ads
                    ['nav','footer','script','style','aside','.ad','.advertisement',
                     '[role=banner]','[role=navigation]'].forEach(sel => {
                        document.querySelectorAll(sel).forEach(el => el.remove());
                    });
                    return document.body ? document.body.innerText : '';
                }""")

                # Extract internal links for crawling
                links = []
                if depth == -1 or current_depth < depth:
                    raw_links = await page.evaluate("""() =>
                        Array.from(document.querySelectorAll('a[href]'))
                             .map(a => a.href)
                    """)
                    for link in raw_links:
                        parsed = urlparse(link)
                        if (parsed.netloc == base_host and
                                link not in visited and
                                not any(link.endswith(ext) for ext in
                                        ['.pdf','.zip','.png','.jpg','.mp4'])):
                            links.append(link)
                            if link not in [u for u, _ in to_visit]:
                                to_visit.append((link, current_depth + 1))

                results.append({
                    "url":   current_url,
                    "title": title,
                    "text":  text.strip(),
                    "links": links[:50],
                    "depth": current_depth,
                })
                log.info(f"Scraped: {current_url} ({len(text)} chars)")
                await page.close()

            except Exception as e:
                log.warning(f"Failed to scrape {current_url}: {e}")
                results.append({"url": current_url, "error": str(e)})

        await browser.close()

    return results


# ── Core: Chunk text ──────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = 512) -> list[str]:
    """Split text into overlapping chunks by sentence boundaries."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, current = [], ""
    for sent in sentences:
        if len(current) + len(sent) > chunk_size and current:
            chunks.append(current.strip())
            current = sent
        else:
            current += " " + sent
    if current.strip():
        chunks.append(current.strip())
    return [c for c in chunks if len(c) > 50]   # filter tiny chunks


# ── Core: Extract structured data via LLM ────────────────────────────────

async def extract_structured(text: str, url: str, schema: Optional[dict]) -> dict:
    """Use LiteLLM to extract structured data from page text."""
    schema_str = json.dumps(schema) if schema else """
    {
      "page_type": "article|product|landing|docs|blog|other",
      "title": "page title",
      "summary": "2-3 sentence summary",
      "key_topics": ["topic1", "topic2"],
      "entities": {"people": [], "companies": [], "products": [], "locations": []},
      "sentiment": "positive|neutral|negative",
      "language": "detected language code"
    }"""

    prompt = f"""Extract structured data from this webpage content and return ONLY valid JSON matching this schema:
{schema_str}

URL: {url}
Content:
{text[:3000]}

Return ONLY the JSON. No explanation."""

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{LITELLM_URL}/v1/chat/completions",
            headers={"Authorization": f"Bearer {LITELLM_KEY}"},
            json={
                "model": EXTRACT_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 1024,
            }
        )
        content = r.json()["choices"][0]["message"]["content"]
        # Strip markdown fences if present
        content = re.sub(r"```json\s*|\s*```", "", content).strip()
        return json.loads(content)


# ── Core: Generate embeddings via Ollama ──────────────────────────────────

async def embed(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of text chunks via Ollama."""
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{OLLAMA_URL}/api/embed",
            json={"model": EMBED_MODEL, "input": texts},
        )
        return r.json()["embeddings"]


# ── Core: Store in SurrealDB ──────────────────────────────────────────────

async def store_surreal(records: list[dict], collection: str):
    """Store chunk records with embeddings in SurrealDB Cloud."""
    sql_statements = []

    for rec in records:
        rid   = f"{collection}:`{rec['chunk_id']}`"
        embed_json = json.dumps(rec["embedding"])
        meta_json  = json.dumps({
            k: v for k, v in rec.items()
            if k not in ("embedding", "chunk_id")
        }).replace("'", "\\'")

        sql_statements.append(
            f"CREATE {rid} SET "
            f"url = '{rec['url']}', "
            f"chunk = '{rec['chunk'].replace(chr(39), chr(92)+chr(39))}', "
            f"embedding = {embed_json}, "
            f"metadata = {meta_json}, "
            f"created_at = time::now();"
        )

    # Batch insert
    batch_sql = "\n".join(sql_statements)
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{SURREAL_URL}/sql",
            headers={
                "Accept": "application/json",
                "NS": SURREAL_NS,
                "DB": SURREAL_DB,
            },
            auth=(SURREAL_USER, SURREAL_PASS),
            content=batch_sql,
        )
        r.raise_for_status()


async def ensure_collection(collection: str):
    """Create SurrealDB table with vector index if it doesn't exist."""
    sql = f"""
    DEFINE TABLE IF NOT EXISTS {collection} SCHEMAFULL;
    DEFINE FIELD IF NOT EXISTS url       ON {collection} TYPE string;
    DEFINE FIELD IF NOT EXISTS chunk     ON {collection} TYPE string;
    DEFINE FIELD IF NOT EXISTS embedding ON {collection} TYPE array;
    DEFINE FIELD IF NOT EXISTS metadata  ON {collection} TYPE object;
    DEFINE FIELD IF NOT EXISTS created_at ON {collection} TYPE datetime;
    DEFINE INDEX IF NOT EXISTS {collection}_embedding
      ON {collection} FIELDS embedding MTREE DIMENSION 768;
    """
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(
            f"{SURREAL_URL}/sql",
            headers={"NS": SURREAL_NS, "DB": SURREAL_DB, "Accept": "application/json"},
            auth=(SURREAL_USER, SURREAL_PASS),
            content=sql,
        )


# ── Core: Full pipeline ───────────────────────────────────────────────────

async def run_scrape_job(job_id: str, req: ScrapeRequest):
    """Full pipeline: crawl → chunk → extract → embed → store."""
    job = jobs[job_id]
    collection = req.collection_name or f"scrape_{urlparse(req.url).netloc.replace('.', '_')}"
    job["collection"] = collection

    try:
        # Step 1: Crawl
        job["status"] = "running"
        job["stage"] = "crawling"
        pages = await crawl(req.url, req.depth, req.max_pages, req.respect_robots)
        job["pages_found"] = len(pages)
        log.info(f"Job {job_id}: crawled {len(pages)} pages")

        # Step 2: Ensure SurrealDB collection exists
        await ensure_collection(collection)

        # Step 3: Process each page
        all_records = []
        for page in pages:
            if "error" in page or not page.get("text"):
                job["errors"].append(f"{page['url']}: {page.get('error','empty')}")
                continue

            # Chunk text
            chunks = chunk_text(page["text"], req.chunk_size)
            if not chunks:
                continue

            # Extract structured data (once per page, not per chunk)
            try:
                structured = await extract_structured(
                    page["text"], page["url"], req.extract_schema)
            except Exception as e:
                structured = {"error": str(e)}
                log.warning(f"Extraction failed for {page['url']}: {e}")

            # Embed chunks in batches of 10
            for i in range(0, len(chunks), 10):
                batch = chunks[i:i+10]
                try:
                    embeddings = await embed(batch)
                except Exception as e:
                    log.warning(f"Embedding failed: {e}")
                    continue

                for chunk, embedding in zip(batch, embeddings):
                    all_records.append({
                        "chunk_id":   str(uuid.uuid4()).replace("-", ""),
                        "url":        page["url"],
                        "title":      page.get("title", ""),
                        "chunk":      chunk,
                        "embedding":  embedding,
                        "structured": structured,
                        "tenant_id":  req.tenant_id or "default",
                        "depth":      page.get("depth", 0),
                    })

            job["pages_scraped"] += 1
            job["stage"] = f"scraped {job['pages_scraped']}/{len(pages)} pages"

        # Step 4: Store in SurrealDB in batches of 25
        for i in range(0, len(all_records), 25):
            await store_surreal(all_records[i:i+25], collection)
            job["chunks_embedded"] = min(i + 25, len(all_records))

        # Step 5: Summary
        job["status"] = "done"
        job["stage"]  = "complete"
        job["result_summary"] = {
            "collection":      collection,
            "pages_scraped":   job["pages_scraped"],
            "chunks_embedded": len(all_records),
            "surreal_db":      SURREAL_DB,
            "surreal_ns":      SURREAL_NS,
            "rag_query_example": f"SELECT * FROM {collection} WHERE embedding <|5,40|> $query_embedding",
        }
        log.info(f"Job {job_id} complete: {len(all_records)} chunks in {collection}")

    except Exception as e:
        job["status"] = "failed"
        job["errors"].append(str(e))
        log.error(f"Job {job_id} failed: {e}")


# ── API endpoints ─────────────────────────────────────────────────────────

@app.post("/scrape", response_model=ScrapeStatus)
async def start_scrape(req: ScrapeRequest, background: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status":         "pending",
        "stage":          "queued",
        "url":            req.url,
        "pages_found":    0,
        "pages_scraped":  0,
        "chunks_embedded": 0,
        "collection":     req.collection_name or "",
        "errors":         [],
        "result_summary": None,
    }
    background.add_task(run_scrape_job, job_id, req)
    return ScrapeStatus(job_id=job_id, **{k: v for k, v in jobs[job_id].items()
                                          if k != "stage"})


@app.get("/job/{job_id}", response_model=ScrapeStatus)
async def get_job(job_id: str):
    if job_id not in jobs:
        from fastapi import HTTPException
        raise HTTPException(404, "Job not found")
    j = jobs[job_id]
    return ScrapeStatus(job_id=job_id, **{k: v for k, v in j.items() if k != "stage"})


@app.get("/health")
async def health():
    return {"status": "ok", "embed_model": EMBED_MODEL, "extract_model": EXTRACT_MODEL}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8400)
