import json
from scraper import NetworkDocScraper

def read_urls_from_file(filename):
    with open(filename, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    return urls

def main():
    sitemap_file = 'sitemap_urls.txt'
    output_file = 'scraped_sitemap_data.json'
    scraper = NetworkDocScraper()
    all_results = []

    urls = read_urls_from_file(sitemap_file)
    print(f"Found {len(urls)} URLs to scrape.")

    for idx, url in enumerate(urls, 1):
        print(f"Scraping {idx}/{len(urls)}: {url}")
        html = scraper.get_page(url)
        if not html:
            print(f"Failed to fetch {url}")
            continue

        # Build metadata using the methods in scraper.py
        soup = None
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
        except Exception as e:
            print(f"BeautifulSoup error for {url}: {e}")
            continue

        metadata = {
            "url": url,
            "vendor": scraper.extract_vendor(url, soup),
            "product_line": scraper.extract_product_line(url, soup),
            "release": scraper.extract_release(url, soup),
            "features": scraper.extract_features(url, soup),
            "categories": scraper.extract_categories(url, soup),
            "deployment": scraper.extract_deployment(url, soup)
        }

        # Use extract_document_content to get the main content
        content = scraper.extract_document_content(metadata)
        all_results.append({
            "url": url,
            "metadata": metadata,
            "content": content
        })

    # Save all results to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"Saved scraped data to {output_file}")

if __name__ == "__main__":
    main()
#adding
