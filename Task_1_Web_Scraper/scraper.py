"""
Autonomous Web Scraper & Data Extractor
Practice target: https://books.toscrape.com/
Extracts book listings across paginated pages into CSV and JSON.
"""

import csv
import json
import logging
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://books.toscrape.com/"
OUTPUT_DIR = Path("data")
CSV_FILE = OUTPUT_DIR / "books.csv"
JSON_FILE = OUTPUT_DIR / "books.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; InternshipPracticeScraper/1.0; "
        "+https://books.toscrape.com/)"
    )
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def create_session() -> requests.Session:
    """Create a session with retry handling for temporary HTTP failures."""
    session = requests.Session()
    session.headers.update(HEADERS)

    retry_strategy = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def clean_price(price_text: str):
    """Return a numeric price while preserving the original currency text."""
    match = re.search(r"(\d+(?:\.\d+)?)", price_text.replace(",", ""))
    return float(match.group(1)) if match else None


def extract_rating(article) -> str:
    """Convert the site's CSS rating class into a readable rating."""
    rating_tag = article.select_one("p.star-rating")
    if not rating_tag:
        return "Unknown"

    rating_classes = rating_tag.get("class", [])
    known_ratings = {"One", "Two", "Three", "Four", "Five"}
    for value in rating_classes:
        if value in known_ratings:
            return value
    return "Unknown"


def extract_books_from_page(soup: BeautifulSoup, page_url: str, page_number: int):
    """Extract all book cards from one listing page."""
    records = []

    for article in soup.select("article.product_pod"):
        title_tag = article.select_one("h3 a")
        price_tag = article.select_one(".price_color")
        availability_tag = article.select_one(".availability")

        if not title_tag or not price_tag:
            logger.warning("Skipping a book card with missing title or price.")
            continue

        title = title_tag.get("title") or title_tag.get_text(strip=True)
        relative_url = title_tag.get("href", "")
        product_url = urljoin(page_url, relative_url)

        price_text = price_tag.get_text(strip=True)
        availability = (
            " ".join(availability_tag.stripped_strings)
            if availability_tag
            else "Unknown"
        )

        breadcrumb = soup.select("ul.breadcrumb li a")
        category = breadcrumb[-1].get_text(strip=True) if len(breadcrumb) >= 3 else "Books"

        records.append({
            "title": title,
            "price": clean_price(price_text),
            "price_currency": "GBP",
            "price_display": price_text,
            "availability": availability,
            "rating": extract_rating(article),
            "category": category,
            "product_url": product_url,
            "listing_page": page_url,
            "page_number": page_number,
        })

    return records


def scrape_books(max_pages=None, delay_seconds=0.5):
    """
    Visit listing pages until pagination ends.
    max_pages=None means scrape all available listing pages.
    """
    session = create_session()
    current_url = BASE_URL
    page_number = 1
    all_records = []

    while current_url and (max_pages is None or page_number <= max_pages):
        logger.info("Scraping page %s: %s", page_number, current_url)

        try:
            response = session.get(current_url, timeout=20)
            response.raise_for_status()
        except requests.RequestException as error:
            logger.error("Could not retrieve page %s: %s", page_number, error)
            break

        soup = BeautifulSoup(response.text, "html.parser")
        page_records = extract_books_from_page(soup, current_url, page_number)

        if not page_records:
            logger.warning("No records found on page %s; stopping.", page_number)
            break

        all_records.extend(page_records)
        logger.info("Extracted %s records (total: %s).",
                    len(page_records), len(all_records))

        next_link = soup.select_one("li.next a")
        current_url = urljoin(current_url, next_link["href"]) if next_link else None
        page_number += 1

        if current_url:
            time.sleep(delay_seconds)

    return all_records


def save_csv(records, path=CSV_FILE):
    """Save records as UTF-8 CSV."""
    if not records:
        logger.warning("No records to save as CSV.")
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(records[0].keys())

    with path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    logger.info("CSV saved: %s", path)


def save_json(records, path=JSON_FILE):
    """Save records as readable JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as json_file:
        json.dump(records, json_file, indent=4, ensure_ascii=False)

    logger.info("JSON saved: %s", path)


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    records = scrape_books()

    if len(records) < 100:
        logger.warning(
            "Only %s records were extracted. Check the connection or website structure.",
            len(records),
        )

    save_csv(records)
    save_json(records)

    print("\n========== SCRAPING SUMMARY ==========")
    print(f"Total records extracted : {len(records)}")
    print(f"CSV output              : {CSV_FILE}")
    print(f"JSON output             : {JSON_FILE}")
    print("======================================")

    if len(records) >= 100:
        print("SUCCESS: The 100+ record target has been achieved.")
    else:
        print("NOTICE: The 100+ record target was not achieved in this run.")


if __name__ == "__main__":
    main()
