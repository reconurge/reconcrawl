import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Set, Dict, Any, Optional
from dataclasses import dataclass
import time

# Disable SSL warnings
requests.packages.urllib3.disable_warnings()


@dataclass
class TrackingItem:
    """Represents a found tracking item (email or phone)."""
    type: str
    value: str
    source_url: str = ""


class Crawler:
    """A web crawler that extracts emails and phone numbers from websites."""
    
    def __init__(self, url: str, max_pages: int = 50, timeout: int = 30, delay: float = 1.0, verbose: bool = False, recursive: bool = False):
        """
        Initialize the crawler.
        
        Args:
            url: The URL to crawl
            max_pages: Maximum number of pages to crawl
            timeout: Request timeout in seconds
            delay: Delay between requests in seconds
            verbose: Print every page being searched
            recursive: Follow every internal link (default: only crawl the final page after redirects)
        """
        self.url = url
        self.max_pages = max_pages
        self.timeout = timeout
        self.delay = delay
        self.verbose = verbose
        self.recursive = recursive
        self.final_url = url
        self.visited_urls: Set[str] = set()
        self.results: List[TrackingItem] = []
        
    def _ensure_protocol(self, url: str) -> str:
        """Ensure URL has a protocol."""
        if not url.startswith(('http://', 'https://')):
            return 'https://' + url
        return url
    
    def _get_final_url(self, url: str) -> str:
        """Follow redirects to get the final URL."""
        try:
            response = requests.head(url, verify=False, timeout=self.timeout, allow_redirects=True)
            return response.url
        except Exception:
            return url
    
    def _is_same_domain(self, url: str, base_domain: str) -> bool:
        """Check if URL belongs to the same domain."""
        try:
            parsed_url = urlparse(url)
            parsed_base = urlparse(base_domain)
            return parsed_url.netloc == parsed_base.netloc
        except Exception:
            return False
    
    def _extract_internal_links(self, soup: BeautifulSoup, base_url: str) -> Set[str]:
        """Extract internal links from the page."""
        internal_links = set()
        
        try:
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if not href:
                    continue
                    
                # Resolve relative URLs
                absolute_url = urljoin(base_url, href)
                
                # Check if it's an internal link and not already visited
                if self._is_same_domain(absolute_url, base_url) and absolute_url not in self.visited_urls:
                    # Filter out common non-content URLs
                    if not any(exclude in absolute_url.lower() for exclude in [
                        '#', 'javascript:', 'mailto:', 'tel:', '.pdf', '.doc', '.docx', 
                        '.jpg', '.jpeg', '.png', '.gif', '.css', '.js', '.xml', '.rss',
                        'logout', 'admin', 'login', 'register', 'signup', 'signin'
                    ]):
                        internal_links.add(absolute_url)
                        
        except Exception:
            pass
            
        return internal_links
    
    def _extract_emails_from_text(self, text: str) -> List[str]:
        """Extract emails from text content."""
        try:
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
            emails = re.findall(email_pattern, text)
            # Remove duplicates while preserving order
            return list(dict.fromkeys(emails))
        except Exception:
            return []
    
    def _extract_emails_from_mailto(self, html: str) -> List[str]:
        """Extract emails from mailto links in HTML content."""
        try:
            emails = []
            
            # Extract mailto patterns from the entire content
            mailto_pattern = r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})'
            mailto_matches = re.findall(mailto_pattern, html, re.IGNORECASE)
            for email in mailto_matches:
                email_clean = email.strip()
                if len(email_clean) <= 100:
                    emails.append(email_clean)
            
            # If it looks like HTML, also try to parse it with BeautifulSoup
            if '<' in html and '>' in html:
                try:
                    soup = BeautifulSoup(html, 'lxml')
                    mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.IGNORECASE))
                    
                    for link in mailto_links:
                        href = link.get('href', '')
                        email_match = re.search(r'^mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})', href, re.IGNORECASE)
                        if email_match:
                            email = email_match.group(1).strip()
                            if len(email) <= 100:
                                emails.append(email)
                except Exception:
                    pass
            
            # Remove duplicates while preserving order
            return list(dict.fromkeys(emails))
            
        except Exception:
            return []
    
    def _extract_phones(self, text: str) -> List[str]:
        """Extract phone numbers from text content."""
        try:
            phones = []
            
            # More specific patterns with word boundaries and context validation
            patterns = [
                # US phone numbers with country code
                r'\b\+1[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
                # US phone numbers without country code (but with context)
                r'\b\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
                # International format (more flexible)
                r'\+[1-9]\d{0,3}[-.\s]?([0-9]{2,4})[-.\s]?([0-9]{2,4})[-.\s]?([0-9]{2,4})\b',
            ]
            
            for pattern in patterns:
                # Use finditer to get the actual matched substring
                for match_obj in re.finditer(pattern, text, re.IGNORECASE):
                    original_match = match_obj.group(0)  # The actual matched substring
                    
                    if self._is_valid_phone(original_match, text):
                        # Format the phone number consistently
                        if pattern == patterns[2]:  # International format
                            # Keep international format as is
                            phone = original_match
                        else:
                            # For US numbers, extract groups and format consistently
                            groups = match_obj.groups()
                            if len(groups) == 3:
                                phone = f"+1-{groups[0]}-{groups[1]}-{groups[2]}"
                            else:
                                phone = original_match
                        
                        phones.append(phone)
            
            # Remove duplicates while preserving order
            return list(dict.fromkeys(phones))
        except Exception:
            return []
    
    def _is_valid_phone(self, phone: str, context: str = "") -> bool:
        """Validate if a phone number is reasonable."""
        try:
            # Remove common separators and get just digits
            digits = re.sub(r'[^\d]', '', phone)
            
            # Must have 10-15 digits (reasonable for phone numbers)
            if len(digits) < 10 or len(digits) > 15:
                return False
            
            # Reject if the phone value is just a sequence of digits (no separators)
            if re.fullmatch(r'\d{10,15}', phone):
                return False
            
            # Require at least one separator (space, dash, dot, parenthesis, or plus)
            if not re.search(r'[\s\-\.\(\)\+]', phone):
                return False
            
            return True
        except Exception:
            return False
    
    def _process_page(self, url: str) -> Dict[str, List[str]]:
        """Process a single page and extract emails and phones."""
        try:
            # Add delay to be respectful to the server
            if len(self.visited_urls) > 0:
                time.sleep(self.delay)
            
            if self.verbose:
                print(f"🔍 Searching: {url}")
            
            # Get the page
            response = requests.get(url, verify=False, timeout=self.timeout)
            
            # Only proceed if we get a 200 status code
            if response.status_code != 200:
                if self.verbose:
                    print(f"❌ Skipping {url}: HTTP {response.status_code}")
                return {"emails": [], "phones": []}
            
            # Parse HTML content
            html_content = response.text
            soup = BeautifulSoup(html_content, 'lxml')
            visible_text = soup.get_text(separator=' ')
            
            # Extract emails from both HTML content and visible text
            emails_from_text = self._extract_emails_from_text(visible_text)
            emails_from_mailto = self._extract_emails_from_mailto(html_content)
            all_emails = list(dict.fromkeys(emails_from_text + emails_from_mailto))
            
            # Extract phone numbers
            phones = self._extract_phones(visible_text)
            
            if self.verbose and (all_emails or phones):
                print(f"✅ Found on {url}: {len(all_emails)} emails, {len(phones)} phones")
            
            return {
                "emails": all_emails,
                "phones": phones
            }
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Error processing {url}: {str(e)}")
            return {"emails": [], "phones": []}
    
    def fetch(self):
        """Fetch the initial URL and follow redirects."""
        try:
            # Ensure URL has protocol
            self.url = self._ensure_protocol(self.url)
            
            # Get final URL after redirects
            self.final_url = self._get_final_url(self.url)
            
        except Exception as e:
            raise RuntimeError(f"Failed to fetch URL: {str(e)}")
    
    def extract_emails(self):
        """Extract emails from the website."""
        self._crawl_and_extract()
    
    def extract_phones(self):
        """Extract phone numbers from the website."""
        # This is handled in _crawl_and_extract, but we keep the method for API consistency
        pass
    
    def _crawl_and_extract(self):
        """Crawl the website and extract emails and phone numbers."""
        if not self.final_url:
            raise RuntimeError("Must call fetch() before extracting data")
        
        if self.recursive:
            # Recursive mode: crawl multiple pages
            urls_to_visit = {self.final_url}
            page_count = 0
            
            while urls_to_visit and page_count < self.max_pages:
                current_url = urls_to_visit.pop()
                
                if current_url in self.visited_urls:
                    continue
                    
                self.visited_urls.add(current_url)
                page_count += 1
                
                # Process the page
                page_data = self._process_page(current_url)
                
                # Add emails to results
                for email in page_data["emails"]:
                    self.results.append(TrackingItem(
                        type="email",
                        value=email,
                        source_url=current_url
                    ))
                
                # Add phones to results
                for phone in page_data["phones"]:
                    self.results.append(TrackingItem(
                        type="phone",
                        value=phone,
                        source_url=current_url
                    ))
                
                # Extract internal links for further crawling
                if page_count < self.max_pages:
                    try:
                        response = requests.get(current_url, verify=False, timeout=self.timeout)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'lxml')
                            new_links = self._extract_internal_links(soup, current_url)
                            urls_to_visit.update(new_links)
                    except Exception:
                        continue
        else:
            # Non-recursive mode: only crawl the final page
            self.visited_urls.add(self.final_url)
            page_data = self._process_page(self.final_url)
            
            # Add emails to results
            for email in page_data["emails"]:
                self.results.append(TrackingItem(
                    type="email",
                    value=email,
                    source_url=self.final_url
                ))
            
            # Add phones to results
            for phone in page_data["phones"]:
                self.results.append(TrackingItem(
                    type="phone",
                    value=phone,
                    source_url=self.final_url
                ))
    
    def get_results(self) -> List[TrackingItem]:
        """Get the extracted results."""
        return self.results