#!/usr/bin/env python
"""
Batch Product Search Tool

This script reads keywords from a file and runs the search_products.py script
for each keyword, saving the results to separate JSON files.

Usage:
    python batch_search.py --input KEYWORDS_FILE [--output-dir OUTPUT_DIRECTORY]
"""

import argparse
import os
import sys
import logging
import subprocess
from datetime import datetime

def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler("batch_search.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(description='Batch search Direct Derma products by keywords from a file')
    parser.add_argument('--input', default='keywords_to_scrape.txt', 
                        help='File containing keywords to search for (one keyword per line)')
    parser.add_argument('--output-dir', default='search_results', 
                        help='Directory to save results (default: search_results)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
                        default='INFO', help='Set the logging level')
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Check if input file exists
    if not os.path.exists(args.input):
        logger.error(f"Error: Input file {args.input} not found")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        logger.info(f"Created output directory: {args.output_dir}")
    
    try:
        # Read keywords from the file
        with open(args.input, 'r') as f:
            keywords = [line.strip() for line in f if line.strip()]
        
        logger.info(f"Found {len(keywords)} keywords to search")
        
        # Create a summary file
        summary_file = os.path.join(args.output_dir, "search_summary.txt")
        with open(summary_file, 'w') as summary:
            summary.write(f"Direct Derma Search Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            summary.write("=" * 80 + "\n\n")
            
            # Process each keyword
            for i, keyword in enumerate(keywords, 1):
                logger.info(f"Processing keyword {i}/{len(keywords)}: {keyword}")
                
                # Define output file for this keyword
                output_file = os.path.join(args.output_dir, f"{keyword.replace(' ', '_')}_results.json")
                
                # Run the search_products.py script for this keyword
                cmd = ["python", "search_products.py", "--keyword", keyword, "--output", output_file]
                logger.info(f"Running command: {' '.join(cmd)}")
                
                try:
                    process = subprocess.run(cmd, check=True, capture_output=True, text=True)
                    
                    # Check if the process was successful
                    if process.returncode == 0:
                        # Extract the number of results from the output
                        output_lines = process.stdout.split('\n')
                        result_count = 0
                        
                        for line in output_lines:
                            if "Found" in line and "matching products" in line:
                                try:
                                    result_count = int(line.split("Found")[1].split("matching")[0].strip())
                                    break
                                except (ValueError, IndexError):
                                    pass
                        
                        logger.info(f"Completed search for '{keyword}'. Found {result_count} products.")
                        
                        # Write to summary file
                        summary.write(f"Keyword: {keyword}\n")
                        summary.write(f"Products found: {result_count}\n")
                        summary.write(f"Results file: {os.path.basename(output_file)}\n")
                        summary.write("-" * 50 + "\n\n")
                        
                    else:
                        logger.error(f"Search for '{keyword}' failed with return code {process.returncode}")
                        summary.write(f"Keyword: {keyword}\n")
                        summary.write("Status: FAILED\n")
                        summary.write(f"Error: Process returned code {process.returncode}\n")
                        summary.write("-" * 50 + "\n\n")
                    
                except subprocess.CalledProcessError as e:
                    logger.error(f"Error processing keyword '{keyword}': {str(e)}")
                    logger.error(f"Stderr: {e.stderr}")
                    
                    # Write error to summary file
                    summary.write(f"Keyword: {keyword}\n")
                    summary.write("Status: ERROR\n")
                    summary.write(f"Error message: {str(e)}\n")
                    summary.write("-" * 50 + "\n\n")
        
        logger.info(f"Batch search completed. Summary saved to {summary_file}")
        print(f"\nBatch search completed. Results saved to {args.output_dir} directory.")
        print(f"Summary saved to {summary_file}")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
