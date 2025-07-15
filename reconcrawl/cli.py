import argparse
import sys
import os

# Add parent directory to path when run as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from reconcrawl import Crawler

def cli():
    parser = argparse.ArgumentParser(description="Extract emails and phone numbers from a website.")
    parser.add_argument("url", help="URL of the website to analyze")
    parser.add_argument("--max-pages", "-mp", type=int, default=50, help="Maximum number of pages to crawl (default: 50)")
    parser.add_argument("--timeout", "-t", type=int, default=30, help="Request timeout in seconds (default: 30)")
    parser.add_argument("--delay", "-d", type=float, default=1.0, help="Delay between requests in seconds (default: 1.0)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print every page being searched")
    parser.add_argument("--recursive", "-r", action="store_true", help="Follow every internal link (default: only crawl the final page after redirects)")
    args = parser.parse_args()

    # Create crawler instance
    crawler = Crawler(
        url=args.url,
        max_pages=args.max_pages,
        timeout=args.timeout,
        delay=args.delay,
        verbose=args.verbose,
        recursive=args.recursive
    )
    
    try:
        print(f"Fetching content from: {args.url}")
        crawler.fetch()
        print(f"Final URL after redirects: {crawler.final_url}")
        
        print("Extracting emails and phone numbers...")
        crawler.extract_emails()
        crawler.extract_phones()
        
        results = crawler.get_results()
        if results:
            print("\nFound items:")
            # Group results by type for better display
            emails = [item for item in results if item.type == "email"]
            phones = [item for item in results if item.type == "phone"]
            
            if emails:
                print(f"\nEmails ({len(emails)}):")
                for email in emails:
                    print(f"  - {email.value}")
                    if email.source_url and email.source_url != crawler.final_url:
                        print(f"    Found on: {email.source_url}")
            
            if phones:
                print(f"\nPhone numbers ({len(phones)}):")
                for phone in phones:
                    print(f"  - {phone.value}")
                    if phone.source_url and phone.source_url != crawler.final_url:
                        print(f"    Found on: {phone.source_url}")
            
            print(f"\nSummary: {len(emails)} emails, {len(phones)} phone numbers found across {len(crawler.visited_urls)} pages")
        else:
            print("\n✅ No email or phone found.")
            
    except RuntimeError as e:
        print(f"❌ Error: {e}")
    except KeyboardInterrupt:
        print("\n⏹️ Crawling interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    cli()
