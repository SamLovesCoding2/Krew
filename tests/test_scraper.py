"""
Unit tests for the AI Collections Web Scraper.

Run with: python -m pytest tests/test_scraper.py -v
"""

import pytest
from scraper import (
    ContentExtractor,
    ContentEnricher,
    WebCrawler,
    AIDocument
)
from bs4 import BeautifulSoup


class TestContentExtractor:
    """Tests for content extraction and cleaning."""
    
    def test_extract_title_from_title_tag(self):
        html = "<html><head><title>Test Page</title></head><body></body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        title = ContentExtractor.extract_title(soup)
        assert title == "Test Page"
    
    def test_extract_title_from_h1_fallback(self):
        html = "<html><body><h1>Main Heading</h1></body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        title = ContentExtractor.extract_title(soup)
        assert title == "Main Heading"
    
    def test_extract_title_from_og_title_fallback(self):
        html = """
        <html>
        <head><meta property="og:title" content="OG Title"></head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        title = ContentExtractor.extract_title(soup)
        assert title == "OG Title"
    
    def test_extract_title_untitled_fallback(self):
        html = "<html><body></body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        title = ContentExtractor.extract_title(soup)
        assert title == "Untitled"
    
    def test_is_boilerplate_element_nav(self):
        html = "<nav>Navigation</nav>"
        soup = BeautifulSoup(html, 'html.parser')
        nav = soup.find('nav')
        assert ContentExtractor.is_boilerplate_element(nav) == True
    
    def test_is_boilerplate_element_by_class(self):
        html = '<div class="sidebar">Sidebar content</div>'
        soup = BeautifulSoup(html, 'html.parser')
        div = soup.find('div')
        assert ContentExtractor.is_boilerplate_element(div) == True
    
    def test_is_boilerplate_element_by_id(self):
        html = '<div id="footer-menu">Footer</div>'
        soup = BeautifulSoup(html, 'html.parser')
        div = soup.find('div')
        assert ContentExtractor.is_boilerplate_element(div) == True
    
    def test_clean_text_whitespace(self):
        text = "This   has    multiple     spaces"
        cleaned = ContentExtractor.clean_text(text)
        assert cleaned == "This has multiple spaces"
    
    def test_clean_text_leading_trailing(self):
        text = "   Leading and trailing   "
        cleaned = ContentExtractor.clean_text(text)
        assert cleaned == "Leading and trailing"
    
    def test_extract_and_clean_basic(self):
        html = """
        <html>
        <head><title>Test Article</title></head>
        <body>
            <nav>Skip this</nav>
            <article>
                <h1>Test Article</h1>
                <p>This is the main content.</p>
                <p>Another paragraph here.</p>
            </article>
            <footer>Skip this too</footer>
        </body>
        </html>
        """
        result = ContentExtractor.extract_and_clean(html, "https://example.com")
        
        assert result['title'] == "Test Article"
        assert "main content" in result['body_text']
        assert "Skip this" not in result['body_text']
        assert result['paragraph_count'] >= 1
        assert result['has_code_blocks'] == False
    
    def test_extract_and_clean_with_code(self):
        html = """
        <html>
        <body>
            <main>
                <p>Some text</p>
                <pre><code>def hello(): pass</code></pre>
            </main>
        </body>
        </html>
        """
        result = ContentExtractor.extract_and_clean(html, "https://example.com")
        assert result['has_code_blocks'] == True


class TestContentEnricher:
    """Tests for content enrichment."""
    
    def test_detect_language_english(self):
        text = "This is a simple English sentence for language detection testing."
        lang = ContentEnricher.detect_language(text)
        assert lang == 'en'
    
    def test_detect_language_short_text(self):
        text = "Hi"
        lang = ContentEnricher.detect_language(text)
        assert lang == 'unknown'
    
    def test_classify_content_type_doc_page(self):
        url = "https://example.com/docs/api/reference"
        content_type = ContentEnricher.classify_content_type(url, "API Reference", "Some text", 0.1)
        assert content_type == 'doc_page'
    
    def test_classify_content_type_article(self):
        url = "https://example.com/blog/my-post"
        content_type = ContentEnricher.classify_content_type(url, "My Blog Post", "Some text", 0.1)
        assert content_type == 'article'
    
    def test_classify_content_type_product_page(self):
        url = "https://example.com/product/widget-123"
        content_type = ContentEnricher.classify_content_type(url, "Widget 123", "Some text", 0.1)
        assert content_type == 'product_page'
    
    def test_classify_content_type_list_page_high_link_density(self):
        url = "https://example.com/category/widgets"
        content_type = ContentEnricher.classify_content_type(url, "Widgets", "Some text", 0.5)
        assert content_type == 'list_page'
    
    def test_enrich_creates_document(self):
        extracted = {
            'title': 'Test Page',
            'body_text': 'This is a test page with some content for testing. ' * 10,
            'paragraph_count': 3,
            'has_code_blocks': False,
            'link_density': 0.15
        }
        
        doc = ContentEnricher.enrich(
            extracted,
            url="https://example.com/test",
            http_status=200,
            crawl_depth=1
        )
        
        assert isinstance(doc, AIDocument)
        assert doc.url == "https://example.com/test"
        assert doc.title == "Test Page"
        assert doc.word_count > 0
        assert doc.char_count > 0
        assert doc.language == 'en'
        assert doc.estimated_read_time_minutes > 0
        assert doc.http_status == 200
        assert doc.crawl_depth == 1


class TestWebCrawler:
    """Tests for web crawler functionality."""
    
    def test_normalize_url_removes_fragment(self):
        crawler = WebCrawler("https://example.com", max_pages=10)
        url = "https://example.com/page#section"
        normalized = crawler.normalize_url(url)
        assert '#' not in normalized
        assert normalized == "https://example.com/page"
    
    def test_normalize_url_removes_trailing_slash(self):
        crawler = WebCrawler("https://example.com", max_pages=10)
        url = "https://example.com/page/"
        normalized = crawler.normalize_url(url)
        assert normalized == "https://example.com/page"
    
    def test_normalize_url_preserves_query(self):
        crawler = WebCrawler("https://example.com", max_pages=10)
        url = "https://example.com/search?q=test"
        normalized = crawler.normalize_url(url)
        assert '?q=test' in normalized
    
    def test_is_valid_url_same_domain(self):
        crawler = WebCrawler("https://example.com", max_pages=10)
        assert crawler.is_valid_url("https://example.com/page") == True
    
    def test_is_valid_url_different_domain(self):
        crawler = WebCrawler("https://example.com", max_pages=10)
        assert crawler.is_valid_url("https://other.com/page") == False
    
    def test_is_valid_url_skips_login(self):
        crawler = WebCrawler("https://example.com", max_pages=10)
        assert crawler.is_valid_url("https://example.com/login") == False
    
    def test_is_valid_url_skips_cart(self):
        crawler = WebCrawler("https://example.com", max_pages=10)
        assert crawler.is_valid_url("https://example.com/cart") == False
    
    def test_is_valid_url_skips_pdf(self):
        crawler = WebCrawler("https://example.com", max_pages=10)
        assert crawler.is_valid_url("https://example.com/document.pdf") == False
    
    def test_extract_links_basic(self):
        crawler = WebCrawler("https://example.com", max_pages=10)
        html = """
        <html>
        <body>
            <a href="/page1">Page 1</a>
            <a href="/page2">Page 2</a>
            <a href="https://other.com/page">External</a>
        </body>
        </html>
        """
        links = crawler.extract_links(html, "https://example.com")
        
        # Should have 2 internal links (external filtered out)
        internal_links = [l for l in links if 'example.com' in l]
        assert len(internal_links) == 2
        assert any('/page1' in l for l in internal_links)
        assert any('/page2' in l for l in internal_links)
    
    def test_extract_links_resolves_relative(self):
        crawler = WebCrawler("https://example.com", max_pages=10)
        html = '<html><body><a href="./relative">Link</a></body></html>'
        links = crawler.extract_links(html, "https://example.com/base/")
        
        assert len(links) > 0
        assert links[0].startswith('https://example.com')
    
    def test_url_deduplication(self):
        crawler = WebCrawler("https://example.com", max_pages=10)
        
        url1 = "https://example.com/page"
        url2 = "https://example.com/page#section"  # Same page, different fragment
        
        normalized1 = crawler.normalize_url(url1)
        normalized2 = crawler.normalize_url(url2)
        
        assert normalized1 == normalized2


class TestAIDocument:
    """Tests for AIDocument data model."""
    
    def test_document_creation(self):
        doc = AIDocument(
            url="https://example.com/page",
            title="Test Page",
            body_text="This is test content.",
            fetched_at="2024-01-01T00:00:00+00:00",
            content_type="article",
            word_count=4,
            char_count=21,
            language="en",
            estimated_read_time_minutes=0.02,
            has_code_blocks=False,
            link_density=0.0,
            paragraph_count=1,
            http_status=200,
            crawl_depth=0
        )
        
        assert doc.url == "https://example.com/page"
        assert doc.word_count == 4
        assert doc.content_type == "article"
    
    def test_document_serialization(self):
        from dataclasses import asdict
        
        doc = AIDocument(
            url="https://example.com/page",
            title="Test",
            body_text="Content",
            fetched_at="2024-01-01T00:00:00+00:00",
            content_type="article",
            word_count=1,
            char_count=7,
            language="en",
            estimated_read_time_minutes=0.01,
            has_code_blocks=False,
            link_density=0.0,
            paragraph_count=1,
            http_status=200,
            crawl_depth=0
        )
        
        doc_dict = asdict(doc)
        assert isinstance(doc_dict, dict)
        assert doc_dict['url'] == "https://example.com/page"
        assert 'word_count' in doc_dict


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

