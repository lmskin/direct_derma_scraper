#!/usr/bin/env python
"""
Batch Product Search Tool

This script reads keywords from a file (text or Excel) and runs the search_products.py script
for each keyword, saving the results to separate JSON files.

Usage:
    python batch_search.py --input KEYWORDS_FILE [--output-dir OUTPUT_DIRECTORY]
    python batch_search.py --excel EXCEL_FILE [--column COLUMN_NAME] [--output-dir OUTPUT_DIRECTORY]
e.g. python batch_search.py --input keywords_to_scrape.txt --output-dir my_results
     python batch_search.py --excel keywords.xlsx --column Keywords --output-dir my_results
    """

import argparse
import os
import sys
import logging
import subprocess
import json
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

def read_keywords_from_txt(file_path):
    """Read keywords from a text file"""
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def read_keywords_from_excel(file_path, column_name=None):
    """Read keywords from an Excel file"""
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas is required for Excel support. Install with: pip install pandas openpyxl")
    
    try:
        # Read the Excel file
        df = pd.read_excel(file_path)
        
        # If column name is specified, use it, otherwise use the first column
        if column_name and column_name in df.columns:
            keywords = df[column_name].astype(str).tolist()
        else:
            # Use the first column
            keywords = df.iloc[:, 0].astype(str).tolist()
        
        # Remove empty keywords and strip whitespace
        keywords = [k.strip() for k in keywords if k and str(k).strip() and str(k).lower() != 'nan']
        
        return keywords
    except Exception as e:
        raise ValueError(f"Error reading Excel file: {str(e)}")

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(description='Batch search Direct Derma products by keywords from a file')
    
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--input', help='Text file containing keywords to search for (one keyword per line)')
    input_group.add_argument('--excel', help='Excel file containing keywords to search for')
    
    parser.add_argument('--column', help='Column name in Excel file to use for keywords (defaults to first column)')
    parser.add_argument('--output-dir', default='search_results', 
                        help='Directory to save results (default: search_results)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
                        default='INFO', help='Set the logging level')
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    try:
        # Read keywords based on input type
        if args.input:
            # Check if input file exists
            if not os.path.exists(args.input):
                logger.error(f"Error: Input file {args.input} not found")
                sys.exit(1)
            
            # Read keywords from text file
            keywords = read_keywords_from_txt(args.input)
            logger.info(f"Reading keywords from text file: {args.input}")
        else:  # args.excel
            # Check if Excel file exists
            if not os.path.exists(args.excel):
                logger.error(f"Error: Excel file {args.excel} not found")
                sys.exit(1)
            
            # Read keywords from Excel file
            try:
                keywords = read_keywords_from_excel(args.excel, args.column)
                logger.info(f"Reading keywords from Excel file: {args.excel}")
            except (ImportError, ValueError) as e:
                logger.error(str(e))
                sys.exit(1)
        
        # Create output directory if it doesn't exist
        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)
            logger.info(f"Created output directory: {args.output_dir}")
        
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
                
                # Run the search_products.py script for this keyword using the same Python interpreter as this script
                cmd = [sys.executable, "search_products.py", "--keyword", keyword, "--output", output_file]
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
                    
                    # Check if output file exists despite the error
                    if os.path.exists(output_file):
                        try:
                            with open(output_file, 'r') as f:
                                data = json.load(f)
                                result_count = len(data)
                                
                                # Write success to summary file if the output file exists and has valid JSON
                                logger.info(f"Despite error, found results for '{keyword}'. Found {result_count} products.")
                                summary.write(f"Keyword: {keyword}\n")
                                summary.write(f"Products found: {result_count}\n")
                                summary.write(f"Results file: {os.path.basename(output_file)}\n")
                                summary.write("-" * 50 + "\n\n")
                                continue
                        except (json.JSONDecodeError, Exception) as json_err:
                            logger.warning(f"Output file exists but contains invalid JSON: {str(json_err)}")
                    
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
