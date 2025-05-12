# Direct Derma Scraper

A robust web scraping tool built with Scrapy and Selenium to extract product pricing information from the Direct Derma Supplies website.

## Project Overview

This scraper is designed to reliably extract product prices from Direct Derma Supplies' website, even when prices are dynamically loaded with JavaScript. It combines Scrapy's powerful crawling capabilities with Selenium's browser automation to handle JavaScript rendering.

## Features

- Extracts product prices using multiple fallback methods for reliability
- Handles JavaScript-rendered content with Selenium
- Supports scraping multiple URLs from an input file
- Extracts product names and currency information
- Timestamps all scraped data
- Configurable request delays to respect website's server load
- Cleans and formats extracted price data automatically
- Supports output in JSON format
- Provides detailed error logging
- Creates HTML snapshots for debugging
- Gracefully handles 404 and other HTTP error responses
- Search for products by keyword and get their prices

## Project Structure

```
direct_derma_scraper/
├── direct_derma/
│   ├── __init__.py
│   ├── items.py
│   ├── middlewares.py
│   ├── pipelines.py
│   ├── settings.py
│   ├── requirements.txt
│   └── spiders/
│       ├── __init__.py
│       └── product_price.py
├── debug_output/        # Contains HTML snapshots for debugging
├── run_scraper.py       # Utility script for easy execution
├── search_products.py   # Tool for searching products by keyword
├── urls_to_scrape.txt   # Sample file with URLs to scrape
├── requirements.txt     # Main requirements file
├── scraper.log          # Log file with detailed execution information
├── search_results.log   # Log file for search operations
├── scrapy.cfg
├── README.md
├── price_data.json      # Output data file
└── search_results.json  # Results from keyword searches
```

## Requirements

- Python 3.6+
- Scrapy 2.13.0
- Selenium 4.32.0
- Chrome/Chromium browser
- Other dependencies listed in requirements.txt

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd direct_derma_scraper
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Ensure you have Chrome/Chromium browser installed on your system

## Usage

### Basic Usage

Run the scraper with the utility script:

```
python run_scraper.py --url "https://www.directdermasupplies.com/products/thermage/thermage-eye-tip-0-25cm2-450-rep" --output results.json
```

### Scraping Multiple URLs

Create a text file with one URL per line, then run:

```
python run_scraper.py --input urls_to_scrape.txt --output results.json
```

### Searching Products by Keyword

Search for products using a keyword and get their prices:

```
python search_products.py --keyword "thermage" --output search_results.json
```

This will:
1. Search the Direct Derma website for products matching the keyword
2. Extract prices for all matching products
3. Display the results in a readable format with a price summary table
4. Save detailed results to the specified output file

### Batch Searching with Multiple Keywords

To search for multiple products using keywords from a file:

1. Create a text file with one keyword per line, e.g., `keywords_to_scrape.txt`
2. Run the batch search script:

```
python batch_search.py --input keywords_to_scrape.txt --output-dir search_results
```

This will:
1. Process each keyword in the file
2. Search for products matching each keyword
3. Save results to separate JSON files in the output directory
4. Create a summary file with statistics for all searches

### Exporting Results to Excel

To export search results to an Excel spreadsheet for easier analysis:

```
python export_to_excel.py --input-dir search_results --output direct_derma_prices.xlsx
```

This will:
1. Process all JSON result files in the specified directory
2. Compile all product data into a single Excel spreadsheet
3. Create a summary sheet with price statistics for each keyword
4. Format the data for easy viewing and analysis

### Additional Options

```
python run_scraper.py --help
```

This will display all available options, including:
- `--log-level`: Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### Direct Scrapy Command

You can also use the standard Scrapy command:

```
scrapy crawl product_price -o price_data.json
```

## How It Works

1. The spider initializes a headless Chrome browser using Selenium
2. It navigates to the target URL and waits for JavaScript content to load
3. Multiple extraction methods are attempted to reliably get the price:
   - Direct CSS selector targeting
   - XPath selection
   - Regular expression pattern matching
   - Fallback to Scrapy selectors on the rendered page
4. Product name and currency information are also extracted when available
5. The extracted price is cleaned and normalized
6. Results are returned as structured data with timestamps

## Configuration

The scraper behavior can be adjusted in `direct_derma/settings.py`:

- `DOWNLOAD_DELAY`: Time in seconds between consecutive requests (default: 1)
- `CONCURRENT_REQUESTS`: Number of simultaneous requests (default: 16)
- `COOKIES_ENABLED`: Whether to enable cookies (default: False)
- `AUTOTHROTTLE_ENABLED`: Enable automatic throttling to avoid server overload (default: True)
- `HTTPCACHE_ENABLED`: Enable HTTP caching for faster development (default: True)

## Troubleshooting

### HTTP Errors (404, 500, etc.)

The scraper is designed to handle HTTP errors gracefully:

1. When a 404 error occurs, the spider will still generate a result entry but with:
   - `price` set to `null`
   - `error` field containing the HTTP error information

Check the `debug_output` directory for HTML snapshots of the rendered pages and the `scraper.log` file for detailed error information.

Common reasons for 404 errors:
- The product URL has changed or the product has been removed
- The URL format is incorrect
- The website structure has changed

### Price Extraction Issues

If you encounter issues with price extraction:

1. Check the `debug_output` directory for HTML snapshots of the rendered pages
2. Look at the spider logs for detailed extraction attempts
3. Try adjusting the CSS selectors in the `product_price.py` file
4. Ensure the website hasn't changed its HTML structure

### Selenium WebDriver Issues

If you encounter issues with the Selenium WebDriver:

1. Ensure you have the correct version of Chrome installed
2. Try updating the webdriver-manager package: `pip install --upgrade webdriver-manager`
3. Check the `scraper.log` for detailed error messages

## License

This project is licensed under the MIT License.