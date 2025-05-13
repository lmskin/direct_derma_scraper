#!/usr/bin/env python
"""
Cleanup Script

This script organizes the workspace by:
1. Moving log files to a logs directory
2. Moving temporary files to a temp directory
3. Removing duplicate or outdated files
4. Organizing result files
"""

import os
import shutil
import sys
import logging
from datetime import datetime

def setup_logging():
    """Set up logging configuration"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(f"{log_dir}/cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def create_directory(dir_path):
    """Create directory if it doesn't exist"""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        logging.info(f"Created directory: {dir_path}")
    return dir_path

def move_file(src, dst_dir):
    """Move file to destination directory"""
    if os.path.exists(src):
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        
        dst_file = os.path.join(dst_dir, os.path.basename(src))
        
        # If destination already exists, add timestamp to filename
        if os.path.exists(dst_file):
            filename, ext = os.path.splitext(os.path.basename(src))
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dst_file = os.path.join(dst_dir, f"{filename}_{timestamp}{ext}")
        
        shutil.move(src, dst_file)
        logging.info(f"Moved {src} to {dst_file}")
        return dst_file
    else:
        logging.warning(f"Source file not found: {src}")
        return None

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Create organization directories
        logs_dir = create_directory("logs")
        archive_dir = create_directory("archive")
        results_dir = create_directory("results")
        
        # 1. Move log files to logs directory
        log_files = [f for f in os.listdir() if f.endswith('.log')]
        for log_file in log_files:
            move_file(log_file, logs_dir)
        
        # 2. Archive older or duplicate scripts
        duplicate_scripts = ['batch_search_fixed.py']
        for script in duplicate_scripts:
            if os.path.exists(script):
                move_file(script, archive_dir)
        
        # 3. Organize result files
        json_files = [f for f in os.listdir() if f.endswith('.json') and f != 'price_data.json']
        for json_file in json_files:
            # Skip if already in the search_results or my_results directories
            if not os.path.dirname(json_file) in ['search_results', 'my_results']:
                move_file(json_file, results_dir)
        
        # 4. Clean up temporary files
        temp_files = ['temp_url.txt', 'page_source.html']
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                logging.info(f"Removed temporary file: {temp_file}")
        
        logger.info("Cleanup completed successfully")
        print("\nCleanup completed successfully. Your workspace is now organized.")
        
    except Exception as e:
        logger.error(f"An error occurred during cleanup: {str(e)}", exc_info=True)
        print(f"\nError during cleanup: {str(e)}")

if __name__ == "__main__":
    main()
