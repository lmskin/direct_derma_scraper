#!/usr/bin/env python
"""
Direct Derma Product Search Tool

This script allows you to search for products on the Direct Derma website
by keyword and outputs the prices of all matching products.

Usage:
    python search_products.py --keyword KEYWORD [--output OUTPUT_FILE]
"""

import argparse
import os
import sys
import logging
import json
import tempfile
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import subprocess
from datetime import datetime

def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler("search_results.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def search_products(keyword):
    """
    Search for products by keyword on Direct Derma website and return URLs of matching products
    
    Args:
        keyword (str): The keyword to search for
        
    Returns:
        list: List of URLs for products matching the keyword
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Searching for products with keyword: {keyword}")
    
    # URL for search
    search_url = f"https://www.directdermasupplies.com/products?Search={keyword}"
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=direct_derma_price_scraper (+http://www.yourdomain.com)")
    
    # Initialize the Chrome driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        # Navigate to search results page
        logger.info(f"Accessing search URL: {search_url}")
        driver.get(search_url)
        
        # Wait for search results to load
        time.sleep(5)
        
        # Find product links
        product_links = []
        try:
            # Look for product elements
            product_elements = driver.find_elements(By.CSS_SELECTOR, ".product-item")
            
            if not product_elements:
                # Try alternative selector
                product_elements = driver.find_elements(By.CSS_SELECTOR, ".grid__item a[href*='/products/']")
            
            if not product_elements:
                # Try another alternative
                product_elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/products/')]")
            
            # Extract URLs
            for element in product_elements:
                try:
                    if element.tag_name != 'a':
                        element = element.find_element(By.CSS_SELECTOR, "a[href*='/products/']")
                    
                    url = element.get_attribute('href')
                    if url and '/products/' in url and url not in product_links:
                        product_links.append(url)
                except Exception as e:
                    logger.warning(f"Error extracting URL from element: {str(e)}")
            
            logger.info(f"Found {len(product_links)} matching products")
            
        except Exception as e:
            logger.error(f"Error finding product elements: {str(e)}")
        
        return product_links
    
    finally:
        driver.quit()

def scrape_product_prices(urls, output_file):
    """
    Scrape prices for the given product URLs using the existing scraper
    
    Args:
        urls (list): List of product URLs to scrape
        output_file (str): Path to save the output results
    """
    logger = logging.getLogger(__name__)
    
    if not urls:
        logger.warning("No product URLs to scrape")
        return []
    
    # Create a temporary file with the URLs
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp:
        for url in urls:
            temp.write(f"{url}\n")
        temp_filename = temp.name
    
    logger.info(f"Created temporary URL file with {len(urls)} URLs: {temp_filename}")
    
    try:
        # Use the existing scraper to scrape the URLs
        cmd = ["python", "run_scraper.py", "--input", temp_filename, "--output", output_file]
        logger.info(f"Running scraper with command: {' '.join(cmd)}")
        
        subprocess.run(cmd, check=True)
        
        # Read and return the results
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                try:
                    data = json.load(f)
                    logger.info(f"Successfully scraped {len(data)} products")
                    return data
                except json.JSONDecodeError:
                    logger.error(f"Output file {output_file} does not contain valid JSON")
                    return []
        else:
            logger.error(f"Output file {output_file} was not created")
            return []
    
    finally:
        # Clean up temporary file
        try:
            os.remove(temp_filename)
        except Exception as e:
            logger.warning(f"Failed to remove temporary file: {str(e)}")

def display_results(results, keyword):
    """
    Display the search results in a readable format
    
    Args:
        results (list): List of product data dictionaries
        keyword (str): The keyword that was searched for
    """
    print("\n" + "=" * 80)
    print(f"SEARCH RESULTS FOR: '{keyword}'")
    print("=" * 80)
    
    if not results:
        print("No matching products found.")
        return
    
    # Display a price summary first
    print("\nPRICE SUMMARY:")
    print("-" * 60)
    print(f"{'PRODUCT':<40} | {'PRICE':<15}")
    print("-" * 60)
    
    for product in sorted(results, key=lambda x: float(x.get('price', '0') or '0')):
        name = product.get('product_name', 'Unknown')
        if len(name) > 37:
            name = name[:34] + '...'
            
        price = product.get('price')
        currency = product.get('currency', 'EUR')
        price_str = f"{currency} {price}" if price else "Not available"
        
        print(f"{name:<40} | {price_str:<15}")
    
    print("-" * 60)
    
    # Then display detailed information
    print("\nDETAILED PRODUCT INFORMATION:")
    for i, product in enumerate(results, 1):
        print(f"\n[{i}] Product: {product.get('product_name', 'Unknown')}")
        print(f"    URL: {product.get('product_url', 'N/A')}")
        if product.get('price'):
            currency = product.get('currency', 'EUR')
            print(f"    Price: {currency} {product.get('price')}")
        else:
            print("    Price: Not available")
    
    print("\n" + "=" * 80)

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(description='Search Direct Derma products by keyword')
    parser.add_argument('--keyword', required=True, help='Keyword to search for')
    parser.add_argument('--output', default='search_results.json', help='Output file (default: search_results.json)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
                       default='INFO', help='Set the logging level')
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    try:
        # Step 1: Search for products by keyword
        product_urls = search_products(args.keyword)
        
        if not product_urls:
            print(f"No products found matching the keyword: '{args.keyword}'")
            return
        
        # Step 2: Scrape prices for the found products
        results = scrape_product_prices(product_urls, args.output)
        
        # Step 3: Display the results
        display_results(results, args.keyword)
        
        logger.info(f"Search and scraping complete. Results saved to {args.output}")
        print(f"\nFull results have been saved to {args.output}")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
