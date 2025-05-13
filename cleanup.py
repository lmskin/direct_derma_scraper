#!/usr/bin/env python
"""
Cleanup Script for Direct Derma Scraper

This script removes temporary files, log files, and cached data
to clean up the project directory while preserving important data.
"""

import os
import shutil
import glob
import logging
import sys
import argparse
from datetime import datetime

def setup_logging():
    """Set up logging configuration"""
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(f"logs/cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def cleanup_files(dry_run=False, preserve_latest=False):
    """
    Clean up the project directory by removing temporary, log, and cache files
    
    Args:
        dry_run (bool): If True, only print what would be deleted without actually deleting
        preserve_latest (bool): If True, preserve the most recent Excel file and results
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting cleanup process (dry run: {dry_run}, preserve latest: {preserve_latest})")
    
    # List of extensions to clean
    log_extensions = ['.log']
    temp_extensions = ['.tmp', '.temp', '.pyc']
    
    # List of directories to clean completely
    dirs_to_clean = [
        'debug_output',
        '__pycache__',
        '.scrapy'
    ]
    
    # Dictionary to track operations
    stats = {
        'files_deleted': 0,
        'directories_cleaned': 0,
        'bytes_freed': 0
    }
    
    # Get the most recent Excel file if preserving latest
    latest_excel = None
    if preserve_latest:
        excel_files = glob.glob('*.xlsx')
        if excel_files:
            latest_excel = max(excel_files, key=os.path.getmtime)
            logger.info(f"Preserving latest Excel file: {latest_excel}")
    
    # 1. Clean log files
    for ext in log_extensions:
        for log_file in glob.glob(f'*{ext}'):
            if handle_file(log_file, dry_run, stats):
                logger.info(f"Removed log file: {log_file}")
    
    # 2. Clean temporary files
    for ext in temp_extensions:
        for temp_file in glob.glob(f'*{ext}'):
            if handle_file(temp_file, dry_run, stats):
                logger.info(f"Removed temporary file: {temp_file}")
    
    # 3. Clean directories
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name) and os.path.isdir(dir_name):
            dir_size = get_dir_size(dir_name)
            if dry_run:
                logger.info(f"Would remove directory: {dir_name} ({format_size(dir_size)})")
            else:
                try:
                    shutil.rmtree(dir_name)
                    stats['directories_cleaned'] += 1
                    stats['bytes_freed'] += dir_size
                    logger.info(f"Removed directory: {dir_name} ({format_size(dir_size)})")
                except Exception as e:
                    logger.error(f"Error removing directory {dir_name}: {str(e)}")
    
    # 4. Clean old JSON files that aren't in result directories
    for json_file in glob.glob('*.json'):
        # Skip important configuration files
        if json_file in ['scrapy.cfg', 'package.json', 'package-lock.json']:
            continue
        
        # Keep main results files
        if json_file == 'url_scrape_results.json':
            continue
            
        if handle_file(json_file, dry_run, stats):
            logger.info(f"Removed JSON file: {json_file}")
    
    # 5. Clean temporary HTML files
    for html_file in glob.glob('*.html'):
        if handle_file(html_file, dry_run, stats):
            logger.info(f"Removed HTML file: {html_file}")
    
    # 6. Clean old Excel files if preserving_latest
    if preserve_latest and latest_excel:
        for excel_file in glob.glob('*.xlsx'):
            if excel_file != latest_excel:
                if handle_file(excel_file, dry_run, stats):
                    logger.info(f"Removed old Excel file: {excel_file}")
    
    # Report results
    logger.info(f"Cleanup completed:")
    logger.info(f"  - Files deleted: {stats['files_deleted']}")
    logger.info(f"  - Directories cleaned: {stats['directories_cleaned']}")
    logger.info(f"  - Space freed: {format_size(stats['bytes_freed'])}")
    
    return stats

def handle_file(file_path, dry_run, stats):
    """
    Handle a single file (delete or report)
    
    Args:
        file_path (str): Path to the file
        dry_run (bool): If True, only print information without deleting
        stats (dict): Statistics dictionary to update
        
    Returns:
        bool: True if file was deleted or would be deleted, False otherwise
    """
    try:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            if dry_run:
                print(f"Would delete: {file_path} ({format_size(file_size)})")
                return True
            else:
                os.remove(file_path)
                stats['files_deleted'] += 1
                stats['bytes_freed'] += file_size
                return True
    except Exception as e:
        logging.error(f"Error handling file {file_path}: {str(e)}")
    return False

def get_dir_size(path):
    """
    Calculate the total size of a directory in bytes
    
    Args:
        path (str): Directory path
        
    Returns:
        int: Total size in bytes
    """
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size

def format_size(size_bytes):
    """
    Format a byte size into a human-readable string
    
    Args:
        size_bytes (int): Size in bytes
        
    Returns:
        str: Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(description='Clean up temporary and log files')
    parser.add_argument('--dry-run', action='store_true', help='Only print what would be deleted without actually deleting')
    parser.add_argument('--preserve-latest', action='store_true', help='Preserve the most recent Excel and result files')
    
    args = parser.parse_args()
    
    try:
        cleanup_files(args.dry_run, args.preserve_latest)
        print("\nCleanup completed successfully!")
        
        if args.dry_run:
            print("\nThis was a dry run. No files were actually deleted.")
            print("Run without --dry-run to actually delete the files.")
            
    except Exception as e:
        logger.error(f"An error occurred during cleanup: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
