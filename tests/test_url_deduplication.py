import unittest
from reconcrawl.extractor import Crawler


class TestURLDeduplication(unittest.TestCase):
    """Test URL deduplication functionality."""
    
    def setUp(self):
        """Set up test crawler instance."""
        self.crawler = Crawler("https://example.com", recursive=True, verbose=False)
    
    def test_url_normalization(self):
        """Test that URLs are properly normalized for deduplication."""
        # Test cases: (url1, url2, should_be_duplicate)
        test_cases = [
            # Same URL with different trailing slashes
            ("https://example.com/page", "https://example.com/page/", True),
            
            # Same URL with different fragments
            ("https://example.com/page", "https://example.com/page#section", True),
            
            # Same URL with different query parameters
            ("https://example.com/page", "https://example.com/page?param=value", True),
            
            # Same URL with different cases
            ("https://example.com/Page", "https://example.com/page", True),
            
            # Different URLs
            ("https://example.com/page1", "https://example.com/page2", False),
            
            # Same URL with different protocols (should be treated as different for security)
            ("http://example.com/page", "https://example.com/page", False),
            
            # Same URL with different ports (should be treated as different)
            ("https://example.com/page", "https://example.com:443/page", False),
        ]
        
        for url1, url2, should_be_duplicate in test_cases:
            normalized1 = self.crawler._normalize_url(url1)
            normalized2 = self.crawler._normalize_url(url2)
            
            if should_be_duplicate:
                self.assertEqual(normalized1, normalized2, 
                               f"URLs should be normalized to same value: {url1} vs {url2}")
            else:
                self.assertNotEqual(normalized1, normalized2, 
                                  f"URLs should be normalized to different values: {url1} vs {url2}")
    
    def test_visited_urls_deduplication(self):
        """Test that the visited_urls set properly prevents duplicate visits."""
        # Add some normalized URLs to visited_urls
        self.crawler.visited_urls.add(self.crawler._normalize_url("https://example.com/page"))
        
        # Test that the same URL with different formatting is not added again
        test_urls = [
            "https://example.com/page/",
            "https://example.com/page#section",
            "https://example.com/page?param=value",
            "https://example.com/Page",
        ]
        
        for url in test_urls:
            normalized = self.crawler._normalize_url(url)
            self.assertIn(normalized, self.crawler.visited_urls,
                         f"Normalized URL should be in visited_urls: {normalized}")
    
    def test_different_urls_not_deduplicated(self):
        """Test that different URLs are not incorrectly deduplicated."""
        # Add a URL to visited_urls
        self.crawler.visited_urls.add(self.crawler._normalize_url("https://example.com/page1"))
        
        # Test that different URLs are not considered duplicates
        different_urls = [
            "https://example.com/page2",
            "https://example.com/page1/subpage",
            "https://example.com/",
        ]
        
        for url in different_urls:
            normalized = self.crawler._normalize_url(url)
            self.assertNotIn(normalized, self.crawler.visited_urls,
                           f"Different URL should not be in visited_urls: {normalized}")


if __name__ == '__main__':
    unittest.main() 