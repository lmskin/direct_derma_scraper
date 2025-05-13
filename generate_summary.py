#!/usr/bin/env python
"""
Generate Summary Tool

This script generates a summary file based on existing JSON result files.

Usage:
    python generate_summary.py --input-dir DIRECTORY [--output OUTPUT_FILE]
"""

import argparse
import os
import sys
import logging
import json
from datetime import datetime

def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler("generate_summary.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(description='Generate summary based on existing JSON result files')
    parser.add_argument('--input-dir', default='my_results', 
                        help='Directory containing JSON result files (default: my_results)')
    parser.add_argument('--output', default=None, 
                        help='Output summary file (default: <input-dir>/search_summary_updated.txt)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
                        default='INFO', help='Set the logging level')
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Set default output file if not specified
    if args.output is None:
        args.output = os.path.join(args.input_dir, "search_summary_updated.txt")
    
    # Check if input directory exists
    if not os.path.exists(args.input_dir):
        logger.error(f"Error: Input directory {args.input_dir} not found")
        sys.exit(1)
    
    try:
        # Find all JSON files in the input directory
        json_files = [f for f in os.listdir(args.input_dir) if f.endswith('_results.json')]
        
        if not json_files:
            logger.warning(f"No JSON result files found in {args.input_dir}")
            sys.exit(0)
        
        # Extract keywords from filenames (remove _results.json suffix)
        keywords = [os.path.splitext(f)[0].replace('_results', '') for f in json_files]
        
        logger.info(f"Found {len(json_files)} result files for keywords: {', '.join(keywords)}")
        
        # Create a summary file
        with open(args.output, 'w') as summary:
            summary.write(f"Direct Derma Search Summary (Updated) - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            summary.write("=" * 80 + "\n\n")
            
            # Process each JSON file
            for json_file in json_files:
                keyword = os.path.splitext(json_file)[0].replace('_results', '')
                file_path = os.path.join(args.input_dir, json_file)
                
                try:
                    # Read the JSON file
                    with open(file_path, 'r') as f:
                        try:
                            data = json.load(f)
                            result_count = len(data)
                            
                            # Write to summary file
                            summary.write(f"Keyword: {keyword}\n")
                            summary.write(f"Products found: {result_count}\n")
                            summary.write(f"Results file: {json_file}\n")
                            
                            # Add product names if available
                            if result_count > 0:
                                summary.write("Products:\n")
                                for i, product in enumerate(data[:5], 1):  # List first 5 products
                                    name = product.get('product_name', 'Unknown')
                                    price = product.get('price', 'N/A')
                                    currency = product.get('currency', '')
                                    summary.write(f"  {i}. {name} - {currency} {price}\n")
                                
                                if result_count > 5:
                                    summary.write(f"  ... and {result_count - 5} more products\n")
                            
                            summary.write("-" * 50 + "\n\n")
                            
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON in file: {file_path}")
                            summary.write(f"Keyword: {keyword}\n")
                            summary.write("Status: ERROR\n")
                            summary.write(f"Error: Invalid JSON format in file\n")
                            summary.write("-" * 50 + "\n\n")
                            
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {str(e)}")
                    summary.write(f"Keyword: {keyword}\n")
                    summary.write("Status: ERROR\n")
                    summary.write(f"Error: {str(e)}\n")
                    summary.write("-" * 50 + "\n\n")
        
        logger.info(f"Summary generated successfully: {args.output}")
        print(f"\nSummary generated successfully: {args.output}")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
