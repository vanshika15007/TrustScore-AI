import asyncio
import logging
import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

logger = logging.getLogger("trustscore.scraper")

MIN_VISIBLE_TEXT_LENGTH = 150


@dataclass
class ScrapeResult:
    url: str
    final_url: str
    title: str
    description: str
    visible_text: str
    chunks: list[str]
    sample_sentences: list[str]
    internal_links: list[str]
    external_links: list[str]
    blocked: bool


def _extract_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    raw_sentences = re.split(r"(?<=[.!?])\s+", normalized)
    return [sentence.strip(" -|\t") for sentence in raw_sentences if 35 <= len(sentence.strip()) <= 260]


def _build_chunks(sentences: list[str], max_chars: int = 480) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        if current and current_len + len(sentence) > max_chars:
            chunks.append(" ".join(current))
            current = [sentence]
            current_len = len(sentence)
            continue
        current.append(sentence)
        current_len += len(sentence)

    if current:
        chunks.append(" ".join(current))

    return chunks[:10]


def _normalize_visible_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _classify_links(hrefs: list[str], final_url: str) -> tuple[list[str], list[str]]:
    final_parsed = urlparse(final_url)
    internal_links: list[str] = []
    external_links: list[str] = []

    for href in hrefs[:200]:
        href_parsed = urlparse(href)
        if href_parsed.scheme not in {"http", "https"}:
            continue
        if href_parsed.netloc == final_parsed.netloc:
            internal_links.append(href)
        else:
            external_links.append(href)

    return sorted(set(internal_links))[:25], sorted(set(external_links))[:25]


def _build_result(
    *,
    url: str,
    final_url: str,
    title: str,
    description: str,
    body_text: str,
    hrefs: list[str],
    rendered_via_browser: bool,
) -> ScrapeResult:
    visible_text = _normalize_visible_text(body_text)
    if len(visible_text) < MIN_VISIBLE_TEXT_LENGTH:
        raise ValueError("Low content / blocked: not enough readable page content was extracted.")

    sentences = _extract_sentences(visible_text)
    if not sentences:
        raise ValueError("Low content / blocked: extracted page text was not meaningful enough.")

    chunks = _build_chunks(sentences)
    internal_links, external_links = _classify_links(hrefs, final_url)
    parsed_target = urlparse(url)
    final_parsed = urlparse(final_url)

    logger.info(
        "Extracted %s chunks from %s using %s",
        len(chunks),
        final_url,
        "playwright" if rendered_via_browser else "http-fallback",
    )
    return ScrapeResult(
        url=url,
        final_url=final_url,
        title=title or "",
        description=(description or "").strip(),
        visible_text=visible_text[:10000],
        chunks=chunks,
        sample_sentences=sentences[:6],
        internal_links=internal_links,
        external_links=external_links,
        blocked=parsed_target.netloc != final_parsed.netloc and len(visible_text) < 250,
    )


async def _scrape_with_playwright(url: str) -> ScrapeResult:
    try:
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError
        from playwright.async_api import async_playwright
    except Exception as exc:  # pragma: no cover - dependency/runtime dependent
        raise RuntimeError(
            "Playwright is not installed. Run `playwright install` after installing dependencies."
        ) from exc

    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
                )
            )

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_timeout(2500)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1200)

                title = await page.title()
                description = await page.locator("meta[name='description']").get_attribute("content")
                body_text = await page.locator("body").inner_text(timeout=8000)
                hrefs = await page.eval_on_selector_all(
                    "a[href]",
                    "elements => elements.map(el => el.href).filter(Boolean)",
                )
                final_url = page.url
            except PlaywrightTimeoutError as exc:
                raise asyncio.TimeoutError from exc
            finally:
                await browser.close()
    except asyncio.TimeoutError as exc:
        raise RuntimeError("The page timed out during browser rendering.") from exc
    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Browser rendering failed: {exc}") from exc

    return _build_result(
        url=url,
        final_url=final_url,
        title=title,
        description=description or "",
        body_text=body_text,
        hrefs=hrefs,
        rendered_via_browser=True,
    )


def _extract_with_bs4(html: str, base_url: str) -> tuple[str, str, str, list[str]]:
    try:
        from bs4 import BeautifulSoup
    except Exception as exc:  # pragma: no cover - dependency/runtime dependent
        raise RuntimeError("BeautifulSoup is required for HTML fallback scraping.") from exc

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    description_tag = soup.select_one("meta[name='description']")
    description = description_tag.get("content", "").strip() if description_tag else ""
    body_text = soup.get_text(" ", strip=True)
    hrefs = [
        urljoin(base_url, anchor.get("href", "").strip())
        for anchor in soup.select("a[href]")
        if anchor.get("href")
    ]
    return title, description, body_text, hrefs


async def _scrape_with_http(url: str) -> ScrapeResult:
    try:
        import httpx

        async with httpx.AsyncClient(
            timeout=20,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
                )
            },
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            final_url = str(response.url)
            html = response.text
    except Exception as exc:  # pragma: no cover - network/runtime dependent
        raise RuntimeError(f"HTTP fallback failed: {exc}") from exc

    title, description, body_text, hrefs = _extract_with_bs4(html, final_url)
    return _build_result(
        url=url,
        final_url=final_url,
        title=title,
        description=description,
        body_text=body_text,
        hrefs=hrefs,
        rendered_via_browser=False,
    )


async def scrape_website(url: str) -> ScrapeResult:
    """Try browser rendering first, then fall back to direct HTML extraction."""
    browser_error: Exception | None = None

    try:
        return await _scrape_with_playwright(url)
    except Exception as exc:
        browser_error = exc
        logger.warning("Playwright scrape failed for %s: %s", url, exc)

    try:
        return await _scrape_with_http(url)
    except Exception as fallback_exc:
        logger.warning("HTTP fallback scrape failed for %s: %s", url, fallback_exc)

        if browser_error is not None:
            raise ValueError(
                "Low content / blocked: browser and fallback extraction both failed."
            ) from fallback_exc

        raise ValueError(f"Low content / blocked: {fallback_exc}") from fallback_exc
