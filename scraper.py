"""
Web scraper for building AI-ready document collections.
Handles crawling, content extraction, and metadata enrichment.
"""

import json
import time
import logging
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, asdict
from collections import deque

import requests
from bs4 import BeautifulSoup
import langdetect


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class AIDocument:
    """Document with extracted content and metadata for AI use"""

    url: str
    title: str
    body_text: str
    fetched_at: str
    content_type: str
    word_count: int
    char_count: int
    language: str
    estimated_read_time_minutes: float
    has_code_blocks: bool
    link_density: float
    paragraph_count: int
    http_status: int
    crawl_depth: int


class ContentExtractor:
    """Extract and clean main content from HTML"""

    BOILERPLATE_TAGS = {"nav", "footer", "aside", "script", "style"}

    # Pattern matching for common boilerplate class/id names
    BOILERPLATE_PATTERNS = [
        "navbar",
        "navigation",
        "menu-",
        "sidebar",
        "side-bar",
        "footer",
        "site-footer",
        "page-footer",
        "header-nav",
        "site-header",
        "advertisement",
        "ad-",
        "cookie-",
        "popup",
        "modal",
        "banner-ad",
        "share-button",
        "social-share",
    ]

    @staticmethod
    def extract_title(soup: BeautifulSoup) -> str:
        """Try multiple strategies to get page title"""
        if soup.title and soup.title.string:
            return soup.title.string.strip()

        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)

        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()

        return "Untitled"

    @staticmethod
    def is_boilerplate_element(element) -> bool:
        """Check if element is likely boilerplate (nav, footer, etc)"""
        if element.name in ContentExtractor.BOILERPLATE_TAGS:
            return True

        class_str = " ".join(element.get("class", [])).lower()
        id_str = element.get("id", "").lower()

        for pattern in ContentExtractor.BOILERPLATE_PATTERNS:
            if pattern in class_str or pattern in id_str:
                return True

        return False

    @staticmethod
    def extract_main_content(soup: BeautifulSoup) -> BeautifulSoup:
        """Find main content container and remove boilerplate"""
        # Try to find main content - skip <article> since it's often used for
        # individual items rather than the whole page
        main_content = (
            soup.find("main")
            or soup.find(
                "div",
                class_=re.compile(
                    r"page.*content|main.*content|site.*content|container.*page", re.I
                ),
            )
            or soup.find("div", id=re.compile(r"content|main", re.I))
            or soup.find("body")
        )

        if not main_content:
            main_content = soup

        # Remove boilerplate tags
        for tag in ContentExtractor.BOILERPLATE_TAGS:
            for element in main_content.find_all(tag):
                element.decompose()

        # Clean up top-level nav/footer/aside elements
        for element in list(
            main_content.find_all(["nav", "footer", "aside"], recursive=False)
        ):
            if element:
                try:
                    element.decompose()
                except Exception:
                    pass

        return main_content

    @staticmethod
    def clean_text(text: str) -> str:
        """Normalize whitespace and clean up text"""
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)
        return text

    @classmethod
    def extract_and_clean(cls, html: str, url: str) -> Dict[str, any]:
        """Main extraction pipeline - returns cleaned content + metadata"""
        soup = BeautifulSoup(html, "html.parser")

        title = cls.extract_title(soup)
        main_content = cls.extract_main_content(soup)

        if not main_content:
            main_content = soup

        body_text = main_content.get_text(separator="\n", strip=True)
        body_text = cls.clean_text(body_text)

        paragraphs = [p for p in body_text.split("\n\n") if p.strip()]
        paragraph_count = len(paragraphs)

        has_code_blocks = bool(
            main_content.find("code") or main_content.find("pre") or "```" in body_text
        )

        all_text_length = len(body_text)
        link_text = " ".join([a.get_text() for a in main_content.find_all("a")])
        link_density = len(link_text) / max(all_text_length, 1)

        return {
            "title": title,
            "body_text": body_text,
            "paragraph_count": paragraph_count,
            "has_code_blocks": has_code_blocks,
            "link_density": link_density,
        }


class ContentEnricher:
    """Add metadata and quality signals to extracted content"""

    WORDS_PER_MINUTE = 200

    @staticmethod
    def detect_language(text: str) -> str:
        """Detect language, fallback to 'unknown' if detection fails"""
        try:
            if len(text) < 50:
                return "unknown"
            return langdetect.detect(text)
        except Exception as e:
            logger.debug(f"Language detection failed: {e}")
            return "unknown"

    @staticmethod
    def classify_content_type(
        url: str, title: str, body_text: str, link_density: float
    ) -> str:
        """Heuristic classification based on URL patterns and content signals"""
        url_lower = url.lower()
        title_lower = title.lower()

        if "/docs/" in url_lower or "/documentation/" in url_lower:
            return "doc_page"

        if "/blog/" in url_lower or "/article/" in url_lower or "/post/" in url_lower:
            return "article"

        if "/product/" in url_lower or "catalogue" in url_lower:
            return "product_page"

        if link_density > 0.3:
            return "list_page"

        if len(body_text) > 1500 and any(
            word in title_lower for word in ["tutorial", "guide", "how to"]
        ):
            return "tutorial"

        return "article"

    @classmethod
    def enrich(
        cls, extracted_data: Dict, url: str, http_status: int, crawl_depth: int
    ) -> AIDocument:
        """Create AIDocument with all metadata fields populated"""
        body_text = extracted_data["body_text"]

        char_count = len(body_text)
        word_count = len(body_text.split())
        language = cls.detect_language(body_text)
        estimated_read_time_minutes = word_count / cls.WORDS_PER_MINUTE

        content_type = cls.classify_content_type(
            url, extracted_data["title"], body_text, extracted_data["link_density"]
        )

        return AIDocument(
            url=url,
            title=extracted_data["title"],
            body_text=body_text,
            fetched_at=datetime.now(timezone.utc).isoformat(),
            content_type=content_type,
            word_count=word_count,
            char_count=char_count,
            language=language,
            estimated_read_time_minutes=round(estimated_read_time_minutes, 2),
            has_code_blocks=extracted_data["has_code_blocks"],
            link_density=round(extracted_data["link_density"], 3),
            paragraph_count=extracted_data["paragraph_count"],
            http_status=http_status,
            crawl_depth=crawl_depth,
        )


class WebCrawler:
    """Web crawler with throttling, dedup, and error handling"""

    def __init__(
        self,
        start_url: str,
        max_pages: int = 100,
        max_depth: int = 3,
        delay_seconds: float = 1.0,
        timeout: int = 10,
        user_agent: str = "AI-Collections-Scraper/1.0",
    ):
        self.start_url = start_url
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay_seconds = delay_seconds
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

        self.visited_urls: Set[str] = set()
        self.url_queue: deque = deque([(start_url, 0)])  # (url, depth)
        self.documents: List[AIDocument] = []
        self.allowed_domain = urlparse(start_url).netloc

        self.stats = {
            "pages_crawled": 0,
            "pages_skipped": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None,
        }

    def is_valid_url(self, url: str) -> bool:
        """Check if URL should be crawled (same domain, not login/cart/etc)"""
        parsed = urlparse(url)

        if parsed.netloc != self.allowed_domain:
            return False

        skip_patterns = [
            "/login",
            "/logout",
            "/signin",
            "/signup",
            "/register",
            "/cart",
            "/checkout",
            "/account",
            "/search",
            "?search=",
            "?q=",
            ".pdf",
            ".jpg",
            ".png",
            ".gif",
            ".zip",
            ".exe",
            "#",
        ]

        url_lower = url.lower()
        for pattern in skip_patterns:
            if pattern in url_lower:
                return False

        return True

    def normalize_url(self, url: str) -> str:
        """Normalize URL for dedup (remove fragment, trailing slash)"""
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        if normalized.endswith("/") and normalized.count("/") > 3:
            normalized = normalized[:-1]
        return normalized

    def extract_links(self, html: str, base_url: str) -> List[str]:
        """Extract and normalize all valid internal links"""
        soup = BeautifulSoup(html, "html.parser")
        links = []

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            absolute_url = urljoin(base_url, href)
            normalized_url = self.normalize_url(absolute_url)

            if self.is_valid_url(normalized_url):
                links.append(normalized_url)

        return links

    def fetch_page(self, url: str) -> Optional[tuple]:
        """Fetch page with error handling, returns (html, status_code) or None"""
        try:
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code >= 400:
                logger.warning(f"HTTP {response.status_code} for {url}")
                self.stats["errors"] += 1
                return None

            return (response.text, response.status_code)

        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching {url}")
            self.stats["errors"] += 1
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            self.stats["errors"] += 1
            return None

    def crawl(self) -> List[AIDocument]:
        """Main crawling loop - returns list of AIDocument objects"""
        logger.info(f"Starting crawl from {self.start_url}")
        logger.info(f"Max pages: {self.max_pages}, Max depth: {self.max_depth}")
        self.stats["start_time"] = datetime.now(timezone.utc)

        while self.url_queue and len(self.documents) < self.max_pages:
            current_url, depth = self.url_queue.popleft()

            if current_url in self.visited_urls:
                continue

            if depth > self.max_depth:
                self.stats["pages_skipped"] += 1
                continue

            self.visited_urls.add(current_url)

            logger.info(
                f"Crawling [{len(self.documents) + 1}/{self.max_pages}] depth={depth}: {current_url}"
            )

            result = self.fetch_page(current_url)
            if not result:
                continue

            html, status_code = result

            try:
                extracted = ContentExtractor.extract_and_clean(html, current_url)

                # Skip pages with minimal content
                if len(extracted["body_text"]) < 100:
                    logger.debug(f"Skipping {current_url}: insufficient content")
                    self.stats["pages_skipped"] += 1
                    continue

                document = ContentEnricher.enrich(
                    extracted, current_url, status_code, depth
                )

                self.documents.append(document)
                self.stats["pages_crawled"] += 1

                if depth < self.max_depth:
                    links = self.extract_links(html, current_url)
                    for link in links:
                        if link not in self.visited_urls:
                            self.url_queue.append((link, depth + 1))

            except Exception as e:
                logger.error(f"Error processing {current_url}: {e}")
                self.stats["errors"] += 1
                continue

            time.sleep(self.delay_seconds)

        self.stats["end_time"] = datetime.now(timezone.utc)
        self._log_summary()

        return self.documents

    def _log_summary(self):
        """Print summary stats"""
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        logger.info("=" * 60)
        logger.info("Crawl Summary:")
        logger.info(f"  Pages crawled: {self.stats['pages_crawled']}")
        logger.info(f"  Pages skipped: {self.stats['pages_skipped']}")
        logger.info(f"  Errors: {self.stats['errors']}")
        logger.info(f"  Duration: {duration:.2f} seconds")
        logger.info(f"  Rate: {self.stats['pages_crawled'] / duration:.2f} pages/sec")
        logger.info("=" * 60)

    def save_to_jsonl(self, output_path: str):
        """Save documents to JSONL format."""
        with open(output_path, "w", encoding="utf-8") as f:
            for doc in self.documents:
                json_line = json.dumps(asdict(doc), ensure_ascii=False)
                f.write(json_line + "\n")

        logger.info(f"Saved {len(self.documents)} documents to {output_path}")

    def save_to_json(self, output_path: str):
        """Save documents to JSON array format."""
        with open(output_path, "w", encoding="utf-8") as f:
            documents_data = [asdict(doc) for doc in self.documents]
            json.dump(documents_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(self.documents)} documents to {output_path}")
