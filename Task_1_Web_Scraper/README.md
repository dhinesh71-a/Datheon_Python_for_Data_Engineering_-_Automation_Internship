# Autonomous Web Scraper & Data Extractor

A Python web scraper that navigates paginated book listings, extracts structured metadata, and exports the results to CSV and JSON.

## Practice website
[Books to Scrape](https://books.toscrape.com/) is a website intended for scraping practice.

## Features
- Scrapes multiple listing pages automatically.
- Extracts title, price, currency, availability, rating, category, product URL, listing page, and page number.
- Uses Requests and BeautifulSoup4.
- Uses a descriptive User-Agent, request timeouts, retry handling, and exception handling.
- Exports records to both CSV and JSON.
- Logs progress and reports the final record count.

## Requirements
- Python 3.9 or later
- Internet connection

## Setup

```bash
python -m venv .venv
```

Activate the environment:

**Windows PowerShell**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows Command Prompt**
```bat
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
python scraper.py
```

The scraper follows the pagination links until the final listing page and writes:

- `data/books.csv`
- `data/books.json`

The project aims to collect 100+ records. The exact count depends on the target site's current content and availability.

## Project structure

```text
autonomous-web-scraper/
├── data/
│   └── .gitkeep
├── scraper.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Data fields

| Field | Description |
|---|---|
| title | Book title |
| price | Numeric price |
| price_currency | Currency code (GBP) |
| price_display | Original displayed price |
| availability | Stock availability text |
| rating | Star rating as text |
| category | Book category |
| product_url | Absolute product page URL |
| listing_page | Listing page URL |
| page_number | Listing page number |

## Notes
- This project is for educational practice using a designated scraping demo website.
- Keep the request delay enabled and do not use this scraper against sites without permission.
- The scraper does not bypass logins, CAPTCHAs, paywalls, or access controls.
