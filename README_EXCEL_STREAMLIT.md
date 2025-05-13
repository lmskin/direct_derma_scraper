# Direct Derma Scraper with Excel Support and Streamlit Frontend

This enhanced version of the Direct Derma scraper includes Excel input/output capabilities and a Streamlit web interface.

## Features

- **Excel Input Support**: Read keywords from Excel files
- **Excel Output**: Export search results to Excel with organized columns
- **Streamlit Web App**: User-friendly interface for uploading files and downloading results
- **Batch Processing**: Search multiple keywords in one operation
- **Direct URL Scraping**: Scrape specific product URLs directly, bypassing the search step

## Installation

1. Clone this repository
2. Install required dependencies:

```bash
pip install -r requirements.txt
```

## Command-Line Usage

### Batch Search with Text File

```bash
python batch_search.py --input keywords_to_scrape.txt --output-dir my_results
```

### Batch Search with Excel File

```bash
python batch_search.py --excel keywords.xlsx --column "Keywords" --output-dir my_results
```

### Direct URL Scraping

```bash
python run_scraper.py --input urls_to_scrape.txt --output url_results.json
```

### Export Results to Excel

```bash
python export_to_excel.py --input-dir my_results --output search_results.xlsx
```

## Web Application Usage

1. Start the Streamlit app:

```bash
streamlit run app.py
```

2. Open your browser to http://localhost:8501

3. Use the interface to:
   - Upload keyword files (TXT or Excel) for product searching
   - Enter URLs directly or upload URL files for specific product scraping
   - View results in an interactive table
   - Download Excel reports

## Scraper Options

### Keyword Search
- Use when you want to find all products matching certain keywords
- Upload a text file with one keyword per line or an Excel file with keywords
- The system will search for products and scrape details for all matches

### URL Scraper
- Use when you already know the exact product URLs
- Enter URLs manually or upload a text file with one URL per line
- Bypasses the search step and directly scrapes the specified products
- Ideal for targeted data collection of specific products

## Excel File Format

The Excel output will contain the following columns:
1. **keyword**: The search term used (for keyword search only)
2. **product_name**: Name of the product
3. **price**: Price value
4. **currency**: Currency code (e.g., EUR)
5. **product_url**: URL to the product page
6. **timestamp**: When the data was scraped

## Files Overview

- **batch_search.py**: Runs multiple searches using keywords from text or Excel files
- **export_to_excel.py**: Exports JSON results to an Excel file
- **app.py**: Streamlit web application with both keyword search and URL scraping
- **search_products.py**: Core search functionality that finds products by keyword
- **run_scraper.py**: Manages the Scrapy spider to scrape product details

## Troubleshooting

- Make sure Chrome is installed (required for Selenium)
- Check log files for errors: batch_search.log, export_excel.log, streamlit_app.log
- Ensure all dependencies are installed correctly
- For Excel-related issues, make sure pandas and openpyxl are installed

## Example Workflow

### Keyword Search Workflow:
1. Create an Excel file with a column of keywords
2. Upload the file to the Streamlit app's Keyword Search tab
3. Run the search
4. Download the results Excel file with all product data organized by keyword

### URL Scraper Workflow:
1. Collect specific product URLs you want to scrape
2. Enter them in the URL Scraper tab or upload a text file
3. Run the URL scraper
4. View and download the results 