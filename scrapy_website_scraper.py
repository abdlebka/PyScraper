import json
import os
from scrapy.crawler import CrawlerProcess
from scrapy import Spider, Request, signals
from scrapy.utils.project import get_project_settings
from urllib.parse import urlparse


class BusinessSpider(Spider):
    name = 'business_spider'

    def __init__(self, url=None, max_depth=2, business_data=None, *args, **kwargs):
        super(BusinessSpider, self).__init__(*args, **kwargs)
        self.start_urls = [url] if url else []
        self.max_depth = int(max_depth)
        self.visited_urls = set()
        self.business_data = business_data or {}
        self.page_contents = []

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(BusinessSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def parse(self, response, current_depth=0):
        # Skip if already visited
        if response.url in self.visited_urls:
            return

        self.visited_urls.add(response.url)

        # Extract content intelligently
        main_content = response.xpath(
            '//*[self::main or self::article or self::section or self::div][contains(@class, "content") or contains(@class, "main") or contains(@class, "article") or contains(@class, "body")]')

        if main_content:
            text = ' '.join(main_content.xpath('.//text()').getall())
            text = ' '.join(text.split())
            if len(text) > 200:
                page_content = text
        else:
            # Fallback: get text from common content elements
            content_elements = response.xpath(
                '//*[self::p or self::li or self::h1 or self::h2 or self::h3 or self::h4 or self::h5 or self::span or self::div]/text()').getall()
            text = ' '.join([el.strip() for el in content_elements if len(el.strip()) > 20])

            # If still not enough content, get all text
            if len(text) < 200:
                text = ' '.join(response.xpath('//body//text()').getall())
                text = ' '.join(text.split())

            page_content = text

        # Store page content with its URL
        if page_content and len(page_content) > 100:  # Only store pages with sufficient content
            self.page_contents.append({
                "url": response.url,
                "content": page_content,
                "depth": current_depth
            })
            print(f"Scraped {len(page_content)} characters from {response.url} (depth: {current_depth})")

        # Follow links if we haven't reached max depth
        if current_depth < self.max_depth:
            links = response.css('a::attr(href)').getall()

            # Filter to internal links
            base_domain = urlparse(response.url).netloc
            internal_links = []

            for link in links:
                if link and not link.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                    absolute_url = response.urljoin(link)
                    link_domain = urlparse(absolute_url).netloc
                    if base_domain == link_domain and absolute_url not in self.visited_urls:
                        internal_links.append(absolute_url)

            # Remove duplicates and limit links
            unique_links = list(set(internal_links))[:10]  # Follow max 10 links per page

            for link in unique_links:
                yield Request(
                    url=link,
                    callback=self.parse,
                    cb_kwargs={'current_depth': current_depth + 1},
                    meta={'dont_redirect': True},
                )

    def spider_closed(self, spider):
        """Called when spider closes - store the collected pages."""
        # Update the business data with the collected pages
        self.business_data["pages"] = self.page_contents
        self.business_data["base_url"] = self.start_urls[0] if self.start_urls else None


def scrape_with_scrapy(businesses, max_depth=2, output_file="scraped_data.json"):
    """Scrape websites using Scrapy."""
    # Set up a list to collect results
    scraped_data = []

    # Configure Scrapy settings
    settings = get_project_settings()
    settings.update({
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1.5,
        'COOKIES_ENABLED': False,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'LOG_LEVEL': 'WARNING',
        'DEPTH_PRIORITY': 1,
        'SCHEDULER_DISK_QUEUE': 'scrapy.squeues.PickleFifoDiskQueue',
        'SCHEDULER_MEMORY_QUEUE': 'scrapy.squeues.FifoMemoryQueue',
        'DOWNLOAD_TIMEOUT': 15,
        'RETRY_TIMES': 2
    })

    # Set up the Crawler Process
    process = CrawlerProcess(settings)

    # Add a spider for each business
    for business in businesses:
        website = business.get("website")
        if not website:
            print(f"No website found for {business.get('name', 'unknown business')}, skipping...")
            # Add the business with empty pages to maintain consistency
            scraped_data.append({
                "name": business.get("name", ""),
                "website": None,
                "pages": [],
                "latitude": business.get("latitude"),
                "longitude": business.get("longitude")
            })
            continue

        try:
            # Create business data to be updated by the spider
            business_data = {
                "name": business.get("name", ""),
                "website": website,
                "pages": [],
                "latitude": business.get("latitude"),
                "longitude": business.get("longitude")
            }

            process.crawl(
                BusinessSpider,
                url=website,
                max_depth=max_depth,
                business_data=business_data
            )

            # Store the business data to retrieve after crawling
            scraped_data.append(business_data)
            print(f"Added spider for {website} with max depth {max_depth}")

        except Exception as e:
            print(f"Error processing {business.get('name', 'unknown business')}: {str(e)}")
            # Add the business with error information
            scraped_data.append({
                "name": business.get("name", ""),
                "website": website,
                "pages": [],
                "latitude": business.get("latitude"),
                "longitude": business.get("longitude"),
                "error": str(e)
            })

    # Start the crawling process
    print("Starting the crawl process...")
    process.start()
    print("Crawl process completed.")

    # Save the scraped data
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(scraped_data, f, ensure_ascii=False, indent=2)

    print(f"Scraped data for {len(scraped_data)} businesses and saved to {output_file}")

    return scraped_data


if __name__ == "__main__":
    places_file = "places.json"

    if not os.path.exists(places_file):
        print(f"Error: {places_file} not found. Please run find_places.py first.")
        exit(1)

    try:
        with open(places_file, "r", encoding="utf-8") as f:
            businesses = json.load(f)
            print(f"Loaded {len(businesses)} businesses from {places_file}")
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Error loading {places_file}: {str(e)}")
        exit(1)

    # Filter out businesses without websites
    businesses_with_websites = [b for b in businesses if "website" in b and b["website"]]
    print(f"Found {len(businesses_with_websites)} businesses with websites")

    # Run the scraper
    scraped_data = scrape_with_scrapy(businesses_with_websites, max_depth=2)