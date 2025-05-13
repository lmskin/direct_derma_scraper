#!/usr/bin/env python
"""
Export Search Results to Excel

This script exports the JSON results from the batch search to an Excel file,
organizing data with product name, price, currency, URL, and timestamp columns.

Usage:
    python export_to_excel.py --input-dir INPUT_DIRECTORY --output OUTPUT_EXCEL_FILE
"""

import argparse
import os
import sys
import logging
import json
import glob
import pandas as pd
from datetime import datetime

def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler("export_excel.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_json_data(file_path):
    """Load data from a JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error reading {file_path}: {str(e)}")
        return []

def export_to_excel(input_dir, output_file):
    """
    Export all JSON files in input_dir to a single Excel file
    
    Args:
        input_dir: Directory containing JSON result files
        output_file: Path to save the Excel file
    """
    logger = logging.getLogger(__name__)
    
    # Check if input directory exists
    if not os.path.exists(input_dir):
        logger.error(f"Input directory {input_dir} does not exist")
        return False
    
    # Find all JSON files in the input directory
    json_files = glob.glob(os.path.join(input_dir, "*_results.json"))
    
    if not json_files:
        logger.warning(f"No JSON result files found in {input_dir}")
        return False
    
    logger.info(f"Found {len(json_files)} JSON files to process")
    
    # Collect all data
    all_data = []
    
    for json_file in json_files:
        keyword = os.path.basename(json_file).replace('_results.json', '')
        data = load_json_data(json_file)
        
        # Add keyword information to each product
        for product in data:
            product['keyword'] = keyword
            all_data.append(product)
    
    if not all_data:
        logger.warning("No product data found in the JSON files")
        return False
    
    # Convert to DataFrame
    df = pd.DataFrame(all_data)
    
    # Reorder and select columns
    columns = ['keyword', 'product_name', 'price', 'currency', 'product_url', 'timestamp']
    
    # Filter to only include columns that exist (in case some are missing)
    available_columns = [col for col in columns if col in df.columns]
    
    # If any required columns are missing, add them with empty values
    for col in columns:
        if col not in df.columns:
            df[col] = ''
    
    df = df[columns]
    
    # Save to Excel
    try:
        df.to_excel(output_file, index=False, sheet_name='Products')
        logger.info(f"Successfully exported {len(df)} products to {output_file}")
        return True
    except Exception as e:
        logger.error(f"Error exporting to Excel: {str(e)}")
        return False

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(description='Export search results to Excel')
    parser.add_argument('--input-dir', required=True, help='Directory containing search result JSON files')
    parser.add_argument('--output', default='search_results.xlsx', help='Output Excel file path')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
                       default='INFO', help='Set the logging level')
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    try:
        success = export_to_excel(args.input_dir, args.output)
        
        if success:
            logger.info(f"Export completed successfully. Results saved to {args.output}")
            print(f"\nExport completed successfully. Results saved to {args.output}")
        else:
            logger.error("Export failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
