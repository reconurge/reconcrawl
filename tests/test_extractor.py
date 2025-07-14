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
    
    def test_international_phone_numbers(self):
        """Test international phone number extraction with various country codes."""
        crawler = Crawler("https://example.com")
        
        # Test various international formats
        # French numbers (+33)
        self.assertIn("+33 1 42 86 12 34", crawler._extract_phones("Contact: +33 1 42 86 12 34"))
        self.assertIn("+33 1 42 86 12 34", crawler._extract_phones("Phone: +33.1.42.86.12.34"))
        self.assertIn("+33 1 42 86 12 34", crawler._extract_phones("Call +33-1-42-86-12-34"))
        
        # UK numbers (+44)
        self.assertIn("+44 20 7946 0958", crawler._extract_phones("UK office: +44 20 7946 0958"))
        self.assertIn("+44 20 7946 0958", crawler._extract_phones("London: +44.20.7946.0958"))
        self.assertIn("+44 20 7946 0958", crawler._extract_phones("Contact: +44-20-7946-0958"))
        
        # German numbers (+49)
        self.assertIn("+49 30 12345678", crawler._extract_phones("Berlin: +49 30 12345678"))
        self.assertIn("+49 30 12345678", crawler._extract_phones("Germany: +49.30.12345678"))
        self.assertIn("+49 30 12345678", crawler._extract_phones("Call: +49-30-12345678"))
        
        # Spanish numbers (+34)
        self.assertIn("+34 91 123 45 67", crawler._extract_phones("Madrid: +34 91 123 45 67"))
        self.assertIn("+34 91 123 45 67", crawler._extract_phones("Spain: +34.91.123.45.67"))
        
        # Italian numbers (+39)
        self.assertIn("+39 02 12345678", crawler._extract_phones("Milan: +39 02 12345678"))
        self.assertIn("+39 02 12345678", crawler._extract_phones("Italy: +39.02.12345678"))
        
        # Japanese numbers (+81)
        self.assertIn("+81 3 1234 5678", crawler._extract_phones("Tokyo: +81 3 1234 5678"))
        self.assertIn("+81 3 1234 5678", crawler._extract_phones("Japan: +81.3.1234.5678"))
        
        # Australian numbers (+61)
        self.assertIn("+61 2 1234 5678", crawler._extract_phones("Sydney: +61 2 1234 5678"))
        self.assertIn("+61 2 1234 5678", crawler._extract_phones("Australia: +61.2.1234.5678"))
        
        # Canadian numbers (+1) - different from US
        self.assertIn("+1 416 123 4567", crawler._extract_phones("Toronto: +1 416 123 4567"))
        self.assertIn("+1 416 123 4567", crawler._extract_phones("Canada: +1.416.123.4567"))
        
        # Numbers with parentheses
        self.assertIn("+33 1 42 86 12 34", crawler._extract_phones("Paris: +33 (1) 42 86 12 34"))
        self.assertIn("+44 20 7946 0958", crawler._extract_phones("London: +44 (20) 7946 0958"))
        
        # Should NOT match invalid international formats
        self.assertEqual(crawler._extract_phones("Invalid: +12345678901234567890"), [])
        self.assertEqual(crawler._extract_phones("Too short: +123"), [])
        self.assertEqual(crawler._extract_phones("No separators: +123456789012345"), [])
    
    def test_clean_international_phone(self):
        """Test the international phone number cleaning function."""
        crawler = Crawler("https://example.com")
        
        # Test various cleaning scenarios
        self.assertEqual(crawler._clean_international_phone("+33 1 42 86 12 34"), "+33 1 42 86 12 34")
        self.assertEqual(crawler._clean_international_phone("+33.1.42.86.12.34"), "+33 1 42 86 12 34")
        self.assertEqual(crawler._clean_international_phone("+33-1-42-86-12-34"), "+33 1 42 86 12 34")
        self.assertEqual(crawler._clean_international_phone("+33 (1) 42 86 12 34"), "+33 1 42 86 12 34")
        self.assertEqual(crawler._clean_international_phone("+33  1  42  86  12  34"), "+33 1 42 86 12 34")
        self.assertEqual(crawler._clean_international_phone("+44.20.7946.0958"), "+44 20 7946 0958")
        self.assertEqual(crawler._clean_international_phone("+44-20-7946-0958"), "+44 20 7946 0958")


if __name__ == '__main__':
    unittest.main()
