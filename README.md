# Reconcrawl

Reconcrawl is a command-line tool and Python library designed to extract emails and phone numbers from websites.  
It follows redirects, crawls internal pages, and scans HTML content to identify contact information from websites.

---

## Features

- Follow HTTP redirects to get the final page URL  
- Crawl internal pages to find more contact information
- Extract email addresses from text content and mailto links
- Detect phone numbers in various formats (US phone numbers)
- Provide a simple CLI for quick usage  
- Python module for integration in your own projects  
- Configurable crawling parameters (max pages, timeout, delay)

---

## Installation

### Using `virtualenv` (recommended)

1. Install `virtualenv` if necessary:

```bash
pip install virtualenv
```

2. Create and activate a new virtual environment:

```bash
virtualenv reconcrawl-env
source reconcrawl-env/bin/activate
```

3. Install Reconcrawl locally (run this command in the project root where `setup.py` is located):

```bash
pip install -r requirements.txt
```

---

## Usage

### Command-line Interface (CLI)

After installation, use the `reconcrawl/cli.py` command:

```bash
python3 reconcrawl/cli.py <url>
```

Example:

```bash
python3 reconcrawl/cli.py https://example.com
```

Sample output:

```
Fetching content from: https://example.com
Final URL after redirects: https://www.example.com
Extracting emails and phone numbers...

Found items:

Emails (2):
  - contact@example.com
  - support@example.com
    Found on: https://www.example.com/contact

Phone numbers (1):
  - +1-555-123-4567

Summary: 2 emails, 1 phone numbers found across 3 pages
```

For help and additional options:

```bash
python3 reconcrawl/cli.py -h
```

Available options:
- `--max-pages`: Maximum number of pages to crawl (default: 50)
- `--timeout`: Request timeout in seconds (default: 30)
- `--delay`: Delay between requests in seconds (default: 1.0)
- `--verbose`: Print every page being searched
- `--recursive`: Follow every internal link (default: only crawl the final page after redirects)

---

### Python Module

You can also use Reconcrawl programmatically:

Add to your `requirements.txt`:

```bash
# requirements.txt
git+https://github.com/reconurge/reconcrawl.git
```

Or install using python:

```bash
pip install git+https://github.com/reconurge/reconcrawl.git
```

```python
from reconcrawl import Crawler

# Create a crawler instance
crawler = Crawler(
    url="https://example.com",
    max_pages=50,
    timeout=30,
    delay=1.0,
    verbose=False,
    recursive=False
)

# Fetch the URL and follow redirects
crawler.fetch()
print(f"Final URL: {crawler.final_url}")

# Extract emails and phone numbers
crawler.extract_emails()
crawler.extract_phones()

# Get results
results = crawler.get_results()

# Process results
for item in results:
    print(f"{item.type}: {item.value}")
    if item.source_url:
        print(f"  Found on: {item.source_url}")
```

Or use the TrackingItem dataclass directly:

```python
from reconcrawl import TrackingItem

# Create tracking items
email_item = TrackingItem(
    type="email",
    value="contact@example.com",
    source_url="https://example.com/contact"
)

phone_item = TrackingItem(
    type="phone", 
    value="+1-555-123-4567",
    source_url="https://example.com/contact"
)
```

---

## Dependencies

* Python 3.6+
* requests
* beautifulsoup4
* lxml

These dependencies are automatically installed via `pip` when you install the package.

---

## Development

* Core code is in the `reconcrawl/` package
* CLI script is in `reconcrawl/cli.py`
* Tests can be run with: `python -m pytest tests/`

---

## License

[MIT License](https://github.com/reconurge/reconcrawl/blob/main/LICENSE).