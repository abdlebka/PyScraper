import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse
import time
import random


def is_internal_link(base_url, link):
    """Check if a link is internal to the base URL."""
    base_domain = urlparse(base_url).netloc
    link_domain = urlparse(link).netloc
    return base_domain == link_domain or not link_domain


def extract_content(soup):
    """Extract content using multiple strategies to handle different website structures."""
    # Strategy 1: Try to find main content containers
    main_content = soup.find_all(['main', 'article', 'section', 'div'],
                                 class_=lambda c: c and any(term in str(c).lower()
                                                            for term in ['content', 'main', 'article', 'body']))

    if main_content:
        # Extract text from the identified main content areas
        text = ' '.join([el.get_text(strip=True, separator=' ') for el in main_content])
        if len(text) > 200:  # If we found substantial content
            return text

    # Strategy 2: Get text from common content elements, more inclusive than before
    content_elements = soup.find_all(['p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'span', 'div'])
    text = ' '.join([el.get_text(strip=True) for el in content_elements if len(el.get_text(strip=True)) > 20])

    # Strategy 3: If still not enough content, get all text but try to clean it
    if len(text) < 200:
        text = soup.body.get_text(separator=' ', strip=True) if soup.body else soup.get_text(separator=' ', strip=True)

    return text


def scrape_website(url, max_depth=2, current_depth=0, visited=None):
    """Scrapes text content from a website and follows internal links up to a specified depth."""
    if visited is None:
        visited = set()

    if url in visited or current_depth > max_depth:
        return ""

    visited.add(url)

    print(f"Scraping website: {url} at depth {current_depth}")
    try:
        # Add random delay to be respectful
        time.sleep(random.uniform(1, 3))

        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
        if response.status_code != 200:
            print(f"Failed to fetch {url}, status code: {response.status_code}")
            return ""

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract text content more intelligently
        text = extract_content(soup)
        print(f"Scraped {len(text)} characters from {url}")

        # Find and follow internal links
        if current_depth < max_depth:
            links_to_follow = []
            for link in soup.find_all('a', href=True):
                link_url = urljoin(url, link['href'])
                if link_url not in visited and is_internal_link(url, link_url):
                    links_to_follow.append(link_url)

            # Limit the number of links to follow to avoid overwhelming the site
            for link_url in links_to_follow[:3]:  # Follow max 3 links per page
                text += " " + scrape_website(link_url, max_depth, current_depth + 1, visited)

        return text
    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return ""


if __name__ == "__main__":
    with open("places.json", "r") as f:
        businesses = json.load(f)

    scraped_data = []
    for business in businesses:
        try:
            website = business.get("website")
            if not website:
                print(f"No website found for {business.get('name', 'unknown business')}, skipping...")
                continue
            text = scrape_website(website)
            scraped_data.append({
                "name": business.get("name", ""),
                "website": website,  # Add website URL to output
                "text": text,
                "latitude": business.get("latitude"),
                "longitude": business.get("longitude")
            })
        except Exception as e:
            print(f"Error processing {business.get('name', 'unknown business')}: {str(e)}")
            # Add the business with error information to maintain a record
            scraped_data.append({
                "name": business.get("name", ""),
                "website": website,  # Add website URL to output
                "text": "",
                "latitude": business.get("latitude"),
                "longitude": business.get("longitude"),
                "error": str(e)
            })
            continue

    with open("raw_text.json", "w", encoding="utf-8") as f:
        json.dump(scraped_data, f, ensure_ascii=False, indent=2)