#!/usr/bin/env python
"""
Export Search Results to Excel

This script takes the JSON search results from the search_products.py script
and exports them to an Excel spreadsheet for easy viewing and analysis.

Usage:
    python export_to_excel.py --input-dir RESULTS_DIRECTORY [--output EXCEL_FILE]
"""

import argparse
import os
import sys
import logging
import json
import glob
try:
    import pandas as pd
except ImportError:
    print("pandas module is required. Install it with: pip install pandas openpyxl")
    sys.exit(1)

def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler("excel_export.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(description='Export search results to Excel')
    parser.add_argument('--input-dir', default='search_results', 
                        help='Directory containing JSON result files (default: search_results)')
    parser.add_argument('--output', default='direct_derma_prices.xlsx', 
                        help='Output Excel file name (default: direct_derma_prices.xlsx)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
                        default='INFO', help='Set the logging level')
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Check if input directory exists
    if not os.path.exists(args.input_dir):
        # If not, check if a single JSON file was specified
        if os.path.exists(args.input_dir) and args.input_dir.endswith('.json'):
            json_files = [args.input_dir]
        else:
            logger.error(f"Error: Input directory {args.input_dir} not found")
            sys.exit(1)
    else:
        # Find all JSON files in the input directory
        json_files = glob.glob(os.path.join(args.input_dir, "*.json"))
    
    if not json_files:
        logger.error(f"No JSON files found in {args.input_dir}")
        sys.exit(1)
    
    logger.info(f"Found {len(json_files)} JSON files to process")
    
    # Create a pandas DataFrame to hold all the data
    all_products = []
    
    try:
        # Process each JSON file
        for json_file in json_files:
            keyword = os.path.basename(json_file).replace('_results.json', '').replace('_', ' ')
            
            logger.info(f"Processing file: {json_file}")
            
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                # Add keyword as a field to each product
                for product in data:
                    product['search_keyword'] = keyword
                    all_products.append(product)
                
                logger.info(f"Added {len(data)} products from {keyword}")
                
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error processing {json_file}: {str(e)}")
        
        if not all_products:
            logger.error("No product data found in the JSON files")
            sys.exit(1)
        
        # Create DataFrame
        df = pd.DataFrame(all_products)
        
        # Reorder columns to put the most important ones first
        column_order = ['search_keyword', 'product_name', 'price', 'currency', 'product_url', 'timestamp']
        other_columns = [col for col in df.columns if col not in column_order]
        df = df[column_order + other_columns]
        
        # Sort by keyword and price
        df = df.sort_values(['search_keyword', 'price'], ascending=[True, True])
        
        # Save to Excel
        logger.info(f"Saving {len(df)} products to {args.output}")
        df.to_excel(args.output, index=False, sheet_name="Product Prices")
        
        # Format the Excel file
        with pd.ExcelWriter(args.output, engine='openpyxl', mode='a') if hasattr(pd, 'ExcelWriter') else None as writer:
            if writer:
                # Create summary sheet
                summary_data = df.groupby('search_keyword').agg(
                    count=('product_name', 'count'),
                    min_price=('price', lambda x: float(min(x)) if len(x) > 0 and all(x) else None),
                    max_price=('price', lambda x: float(max(x)) if len(x) > 0 and all(x) else None),
                    avg_price=('price', lambda x: sum(float(p) for p in x if p) / len([p for p in x if p]) if any(p for p in x) else None)
                ).reset_index()
                
                summary_data.to_excel(writer, index=False, sheet_name="Summary")
        
        logger.info(f"Export completed successfully. File saved to {args.output}")
        print(f"\nExport completed successfully. File saved to {args.output}")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
