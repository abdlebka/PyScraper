import requests
from bs4 import BeautifulSoup
import json


def scrape_website(url):
    """Scrapes text content from a website."""
    print(f"Scraping website: {url}")
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    if response.status_code != 200:
        print(f"Failed to fetch {url}, status code: {response.status_code}")
        return ""

    soup = BeautifulSoup(response.text, 'html.parser')
    text = ' '.join([p.get_text() for p in soup.find_all(['p', 'li', 'h1', 'h2', 'h3'])])
    print(f"Scraped {len(text)} characters from {url}")
    return text


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
                "text": text,
                "latitude": business.get("latitude"),
                "longitude": business.get("longitude")
            })
        except Exception as e:
            print(f"Error processing {business.get('name', 'unknown business')}: {str(e)}")
            continue

    with open("raw_text.json", "w") as f:
        json.dump(scraped_data, f)
    print("Scraped text saved to raw_text.json")

