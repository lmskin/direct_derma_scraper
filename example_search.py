#!/usr/bin/env python
"""
Example script showing how to use the search_products.py tool

This script demonstrates how to use the search_products module programmatically
instead of through the command line.
"""

import sys
import os
import json
from search_products import search_products, scrape_product_prices, display_results

def main():
    # Define the keyword you want to search for
    keyword = "thermage"
    
    print(f"Searching for products matching keyword: '{keyword}'")
    
    # Step 1: Search for products by keyword
    product_urls = search_products(keyword)
    
    if not product_urls:
        print(f"No products found matching the keyword: '{keyword}'")
        return
    
    print(f"Found {len(product_urls)} matching products")
    
    # Step 2: Scrape prices for the found products
    output_file = "example_search_results.json"
    results = scrape_product_prices(product_urls, output_file)
    
    # Step 3: Display the results
    display_results(results, keyword)
    
    print(f"\nFull results have been saved to {output_file}")

if __name__ == "__main__":
    main()
