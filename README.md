# Scalable Business Lead Scraper

A production-ready, modular web scraping system built with Python and Playwright.

## Features
- **Modern Web Support**: Handles JavaScript-rendered pages using Playwright.
- **Auto-Pagination**: Automatically navigates through multiple pages.
- **Robustness**: Includes retries, throttling, and error handling.
- **Data Quality**: Normalizes phone numbers (+91 format), deduplicates entries, and validates data.
- **Flexible Export**: Saves data to CSV, Excel, and JSON.
- **Configurable**: Fully controlled via `config/settings.yaml` and `config/selectors.yaml`.

## Installation

1. **Clone the repository** (if applicable) or download the source.
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Install Playwright Browsers**:
   ```bash
   playwright install chromium
   ```

## Configuration

### 1. Target Website
Edit `config/settings.yaml`:
```yaml
scraper:
  target_url: "https://example.com/directory"
  max_pages: 10
```

### 2. Selectors
Edit `config/selectors.yaml` to match the CSS selectors of your target website.
```yaml
listing_container: ".business-card"
fields:
  business_name:
    selector: ".name-tag"
  phone:
    selector: ".contact-info"
```

## Usage

Run the scraper:
```bash
python main.py
```

## Output
Data is saved in the `output/` directory by default.

## Project Structure
- `src/`: Source code
  - `scraper.py`: Main engine
  - `parser.py`: HTML parsing
  - `pipeline.py`: Data cleaning
- `config/`: Configuration files
- `tests/`: Local verification tests
