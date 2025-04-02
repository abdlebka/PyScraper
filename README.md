# Place Activity Processor

A collection of Python scripts for finding, scraping, and processing activity information from places.

## Scripts Overview

### 1. `find_places.py`
- Queries the Google Places API to find businesses matching a keyword
- Need an api key from google. Will send separately. 
- Retrieves place details including websites
- Saves the data to `places.json`

### 2. `scrape_website.py`
- ignore this, no longer relevant

### 3. `scrapy_website_scraper.py`
- Advanced scraper using the Scrapy framework
- More robust than the basic scraper with proper rate limiting and error handling
- Outputs to `scraped_data.json`

### 4. `extract_activities.py`
- Uses the Ollama library with Mistral 7B to extract structured activity information
- Processes text content from `scraped_data.json`
- Outputs to `activities.json`

### 5. `dedupe_activities.py`
- Removes duplicate activities based on name and description similarity
- Groups similar activities and merges their information
- Outputs to `deduplicated_activities.json`

### 6. `activity_merger.py`
- Merges place data from `places.json` with activity data
- Enriches activities with place information like ratings and website URLs
- Outputs to `merged_data.json`

### 7. `store_to_firestore.py`
- Uploads the processed activities to Firebase Firestore database

## Running Sequence

1. Run `find_places.py` to search for businesses **MAKE SURE TO ADD GOOGLE PLACES API KEY**
2. Run scrapy_website_scraper.py` (advanced scraper)
3. Run `extract_activities.py` to process the scraped content
4. Run `dedupe_activities.py` to remove duplicates (optional)
5. Run `activity_merger.py` to enrich with place data (optional)
6. Run `store_to_firestore.py` to upload to Firestore (optional)

## Requirements

- Python 3.x
- Google Places API key
- Firebase credentials (for Firestore)
- Ollama with Mistral 7B model installed locally
- Libraries: requests, BeautifulSoup, Scrapy, firebase-admin
