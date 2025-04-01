import requests
from bs4 import BeautifulSoup
import json


def scrape_website(url):
    """Scrapes text content from a website."""
    print(f"Scraping website: {url}")
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
        if response.status_code != 200:
            print(f"Failed to fetch {url}, status code: {response.status_code}")
            return ""

        soup = BeautifulSoup(response.text, 'html.parser')
        text = ' '.join([p.get_text() for p in soup.find_all(['p', 'li', 'h1', 'h2', 'h3'])])
        print(f"Scraped {len(text)} characters from {url}")
        return text
    except requests.exceptions.SSLError as e:
        print(f"SSL error for {url}: {str(e)}")
        return ""
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error for {url}: {str(e)}")
        return ""
    except requests.exceptions.Timeout as e:
        print(f"Timeout error for {url}: {str(e)}")
        return ""
    except requests.exceptions.RequestException as e:
        print(f"Request error for {url}: {str(e)}")
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
                "text": text,
                "latitude": business.get("latitude"),
                "longitude": business.get("longitude")
            })
        except Exception as e:
            print(f"Error processing {business.get('name', 'unknown business')}: {str(e)}")
            # Add the business with error information to maintain a record
            scraped_data.append({
                "name": business.get("name", ""),
                "text": "",
                "latitude": business.get("latitude"),
                "longitude": business.get("longitude"),
                "error": str(e)
            })
            continue

    with open("raw_text.json", "w", encoding="utf-8") as f:
        json.dump(scraped_data, f, ensure_ascii=False, indent=2)

    # Log summary statistics
    successful_scrapes = len([item for item in scraped_data if item.get("text")])
    failed_scrapes = len(scraped_data) - successful_scrapes
    print(f"Scraping completed: {successful_scrapes} successful, {failed_scrapes} failed")
    print("Scraped text saved to raw_text.json")