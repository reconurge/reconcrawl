import unittest
from unittest.mock import patch, Mock
from reconcrawl import Crawler, TrackingItem


class TestCrawler(unittest.TestCase):
    
    def test_crawler_initialization(self):
        """Test that Crawler initializes correctly."""
        crawler = Crawler("https://example.com")
        self.assertEqual(crawler.url, "https://example.com")
        self.assertEqual(crawler.max_pages, 50)
        self.assertEqual(crawler.timeout, 30)
        self.assertEqual(crawler.delay, 1.0)
        self.assertEqual(crawler.final_url, "https://example.com")
        self.assertEqual(len(crawler.visited_urls), 0)
        self.assertEqual(len(crawler.results), 0)
    
    def test_ensure_protocol(self):
        """Test URL protocol handling."""
        crawler = Crawler("example.com")
        self.assertEqual(crawler._ensure_protocol("example.com"), "https://example.com")
        self.assertEqual(crawler._ensure_protocol("https://example.com"), "https://example.com")
        self.assertEqual(crawler._ensure_protocol("http://example.com"), "http://example.com")
    
    def test_extract_emails_from_text(self):
        """Test email extraction from text."""
        crawler = Crawler("https://example.com")
        text = "Contact us at test@example.com or support@test.com"
        emails = crawler._extract_emails_from_text(text)
        self.assertIn("test@example.com", emails)
        self.assertIn("support@test.com", emails)
        self.assertEqual(len(emails), 2)
    
    def test_extract_phones(self):
        """Test phone number extraction."""
        crawler = Crawler("https://example.com")
        text = "Call us at (555) 123-4567 or +1-555-987-6543"
        phones = crawler._extract_phones(text)
        self.assertIn("+1-555-123-4567", phones)
        self.assertIn("+1-555-987-6543", phones)
    
    def test_tracking_item(self):
        """Test TrackingItem dataclass."""
        item = TrackingItem(type="email", value="test@example.com", source_url="https://example.com/contact")
        self.assertEqual(item.type, "email")
        self.assertEqual(item.value, "test@example.com")
        self.assertEqual(item.source_url, "https://example.com/contact")
    
    @patch('requests.head')
    def test_get_final_url(self, mock_head):
        """Test final URL resolution."""
        mock_response = Mock()
        mock_response.url = "https://example.com/final"
        mock_head.return_value = mock_response
        
        crawler = Crawler("https://example.com")
        final_url = crawler._get_final_url("https://example.com")
        self.assertEqual(final_url, "https://example.com/final")
    
    def test_is_same_domain(self):
        """Test domain comparison."""
        crawler = Crawler("https://example.com")
        self.assertTrue(crawler._is_same_domain("https://example.com/page", "https://example.com"))
        self.assertTrue(crawler._is_same_domain("https://sub.example.com/page", "https://sub.example.com"))
        self.assertFalse(crawler._is_same_domain("https://other.com/page", "https://example.com"))

    def test_extract_phones_strict(self):
        """Test stricter phone number extraction logic."""
        crawler = Crawler("https://example.com")
        # Should match
        self.assertIn("+1-555-123-4567", crawler._extract_phones("Call us at (555) 123-4567"))
        self.assertIn("+1-555-123-4567", crawler._extract_phones("Phone: 555-123-4567"))
        self.assertIn("+1-555-123-4567", crawler._extract_phones("Contact: +1-555-123-4567"))
        self.assertIn("+1-555-123-4567", crawler._extract_phones("555.123.4567"))
        # Should NOT match plain digit sequences
        self.assertNotIn("+1-123-456-7890", crawler._extract_phones("Product ID: 1234567890"))
        self.assertNotIn("+1-123-456-7890", crawler._extract_phones("Order #1234567890"))
        self.assertNotIn("+1-123-456-7890", crawler._extract_phones("ISBN: 1234567890"))
        self.assertNotIn("+1-123-456-7890", crawler._extract_phones("1234567890"))
        self.assertNotIn("+1-123-456-7890", crawler._extract_phones("Order ID: 1234567890"))
        # Should NOT match 16-digit numbers
        self.assertEqual(crawler._extract_phones("Credit card: 1234567890123456"), [])
        # Should NOT match long digit sequences
        self.assertEqual(crawler._extract_phones("12345678901234567890"), [])
        # Should match international with separators
        self.assertIn("+44 20 7946 0958", crawler._extract_phones("Call +44 20 7946 0958"))
        # Should NOT match numbers with no separators
        self.assertEqual(crawler._extract_phones("9876543210"), [])


if __name__ == '__main__':
    unittest.main()
