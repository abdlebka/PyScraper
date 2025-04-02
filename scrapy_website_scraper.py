import json
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
        self.collected_text = ""

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

        # Extract content intelligently, similar to the original extract_content function
        main_content = response.xpath(
            '//*[self::main or self::article or self::section or self::div][contains(@class, "content") or contains(@class, "main") or contains(@class, "article") or contains(@class, "body")]')

        if main_content:
            text = ' '.join(main_content.xpath('.//text()').getall())
            text = ' '.join(text.split())
            if len(text) > 200:
                self.collected_text += " " + text
        else:
            # Fallback: get text from common content elements
            content_elements = response.xpath(
                '//*[self::p or self::li or self::h1 or self::h2 or self::h3 or self::h4 or self::h5 or self::span or self::div]/text()').getall()
            text = ' '.join([el.strip() for el in content_elements if len(el.strip()) > 20])

            # If still not enough content, get all text
            if len(text) < 200:
                text = ' '.join(response.xpath('//body//text()').getall())
                text = ' '.join(text.split())

            self.collected_text += " " + text

        print(f"Scraped {len(text)} characters from {response.url} (depth: {current_depth})")

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

            # Remove duplicates and limit links to avoid overwhelming the site
            unique_links = list(set(internal_links))[:10]  # Follow max 10 links per page

            for link in unique_links:
                yield Request(
                    url=link,
                    callback=self.parse,
                    cb_kwargs={'current_depth': current_depth + 1},
                    meta={'dont_redirect': True},
                )

    def spider_closed(self, spider):
        """Called when spider closes - store the collected text."""
        # Clean up the text
        self.collected_text = self.collected_text.strip()

        # Update the business data with the collected text
        self.business_data["text"] = self.collected_text

        # The item will be captured by the assigned spider_closed handler


def scrape_with_scrapy(businesses, max_depth=6):
    """Scrape websites using Scrapy."""
    # Set up a list to collect results
    scraped_data = []

    # Configure Scrapy settings
    settings = get_project_settings()
    settings.update({
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1.5,  # Increase delay between requests
        'COOKIES_ENABLED': False,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'LOG_LEVEL': 'WARNING',
        'DEPTH_PRIORITY': 1,  # Prioritize depth-first crawling
        'SCHEDULER_DISK_QUEUE': 'scrapy.squeues.PickleFifoDiskQueue',
        'SCHEDULER_MEMORY_QUEUE': 'scrapy.squeues.FifoMemoryQueue',
    })

    # Set up the Crawler Process
    process = CrawlerProcess(settings)

    # Add a spider for each business
    for business in businesses:
        website = business.get("website")
        if not website:
            print(f"No website found for {business.get('name', 'unknown business')}, skipping...")
            # Add the business with empty text to maintain consistency
            scraped_data.append({
                "name": business.get("name", ""),
                "website": website,
                "text": "",
                "latitude": business.get("latitude"),
                "longitude": business.get("longitude")
            })
            continue

        try:
            # Create business data to be updated by the spider
            business_data = {
                "name": business.get("name", ""),
                "website": website,
                "text": "",
                "latitude": business.get("latitude"),
                "longitude": business.get("longitude")
            }

            # Simply use the process.crawl method directly - this is the key fix
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
                "text": "",
                "latitude": business.get("latitude"),
                "longitude": business.get("longitude"),
                "error": str(e)
            })

    # Start the crawling process
    print("Starting the crawl process...")
    process.start()  # This will only start if there are crawlers
    print("Crawl process completed.")

    return scraped_data

if __name__ == "__main__":
    # Get crawl depth from user
    max_depth = input("Enter max crawl depth (default is 2): ")
    max_depth = int(max_depth) if max_depth else 2

    # Load businesses from file
    with open("places.json", "r") as f:
        businesses = json.load(f)

    # Scrape websites using Scrapy
    scraped_data = scrape_with_scrapy(businesses, max_depth)

    # Save results to JSON file
    with open("raw_text.json", "w", encoding="utf-8") as f:
        json.dump(scraped_data, f, ensure_ascii=False, indent=2)

    print(f"Scraping complete. Processed {len(scraped_data)} businesses.")
    print(f"Results saved to raw_text.json")