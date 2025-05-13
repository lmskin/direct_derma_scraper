#!/usr/bin/env python
"""
Direct Derma Price Scraper Runner

This script provides a convenient way to run the Direct Derma price scraper.
It allows you to:
1. Scrape a single URL
2. Scrape multiple URLs from a file
3. Set the output file format and location

Usage:
    python run_scraper.py --url URL [--output OUTPUT_FILE]
    python run_scraper.py --input INPUT_FILE [--output OUTPUT_FILE]
"""

import argparse
import os
import sys
import logging
import json
import subprocess
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler("scraper.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(description='Run Direct Derma Price Scraper')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--url', help='URL to scrape')
    group.add_argument('--input', help='File containing URLs to scrape (one URL per line)')
    parser.add_argument('--output', default='price_data.json', help='Output file (default: price_data.json)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
                        default='INFO', help='Set the logging level')
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
      # Check if input file exists
    if args.input and not os.path.exists(args.input):
        logger.error(f"Error: Input file {args.input} not found")
        sys.exit(1)
      try:
        # Initialize the crawler process with project settings
        process = CrawlerProcess(get_project_settings())
        
        # Set up the input file parameter
        spider_kwargs = {}
        
        if args.input:
            if not os.path.exists(args.input):
                logger.error(f"Input file {args.input} not found")
                sys.exit(1)
            spider_kwargs['input_file'] = args.input
            logger.info(f"Using input file: {args.input}")
        elif args.url:
            # Create a temporary file with the URL
            temp_file = 'temp_url.txt'
            with open(temp_file, 'w') as f:
                f.write(args.url)
            spider_kwargs['input_file'] = temp_file
            logger.info(f"Scraping URL: {args.url}")
        
        # Run the spider
        logger.info(f"Starting scraper, output will be saved to {args.output}")
        
        # Configure output
        process.settings.set('FEEDS', {
            args.output: {
                'format': 'json',
                'encoding': 'utf8',
                'overwrite': True,
            },
        })
        
        process.crawl('product_price', **spider_kwargs)
        process.start()  # The script will block here until the crawling is finished
        
        # Clean up temporary file if needed
        if args.url and os.path.exists('temp_url.txt'):
            os.remove('temp_url.txt')
        
        # Verify the output file exists and has content
        if os.path.exists(args.output):
            try:
                with open(args.output, 'r') as f:
                    data = json.load(f)
                logger.info(f"Scraping complete. Found {len(data)} results.")
                if len(data) == 0:
                    logger.warning("No data was scraped. Check the URLs or spider configuration.")
            except json.JSONDecodeError:
                logger.error(f"Output file {args.output} does not contain valid JSON")
        else:
            logger.error(f"Output file {args.output} was not created")
        
        logger.info(f"Scraping complete. Results saved to {args.output}")
    
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 