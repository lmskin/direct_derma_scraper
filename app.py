#!/usr/bin/env python
"""
Direct Derma Scraper Web App

A Streamlit web application that provides a user interface for the Direct Derma scraper.
Users can upload a file with keywords and export results
"""

import streamlit as st
import pandas as pd
import os
import sys
import json
import time
import tempfile
import subprocess
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("streamlit_app.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Direct Derma Scraper",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

def read_keywords_from_file(uploaded_file, is_excel=False, column_name=None):
    """Extract keywords from an uploaded file"""
    try:
        if is_excel:
            # Read Excel file
            df = pd.read_excel(uploaded_file)
            
            # Use specified column or default to first column
            if column_name and column_name in df.columns:
                keywords = df[column_name].astype(str).tolist()
            else:
                keywords = df.iloc[:, 0].astype(str).tolist()
                
            # Remove empty keywords and strip whitespace
            keywords = [k.strip() for k in keywords if k and str(k).strip() and str(k).lower() != 'nan']
        else:
            # Read text file
            content = uploaded_file.getvalue().decode('utf-8')
            keywords = [line.strip() for line in content.split('\n') if line.strip()]
        
        return keywords
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        logger.error(f"Error reading file: {str(e)}")
        return []

def run_batch_search(keywords, output_dir):
    """Run batch search for keywords and save results to output_dir"""
    # Create a temporary file with keywords
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp:
        for keyword in keywords:
            temp.write(f"{keyword}\n")
        temp_file = temp.name
    
    try:
        # Run the batch search script
        cmd = [sys.executable, "batch_search.py", "--input", temp_file, "--output-dir", output_dir]
        process = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if process.returncode == 0:
            st.success("Batch search completed successfully!")
            return True
        else:
            st.error(f"Batch search failed with return code {process.returncode}")
            st.code(process.stderr)
            return False
    except subprocess.CalledProcessError as e:
        st.error(f"Error running batch search: {str(e)}")
        st.code(e.stderr)
        return False
    finally:
        # Clean up the temporary file
        try:
            os.remove(temp_file)
        except:
            pass

def export_to_excel(input_dir, output_file):
    """Export search results to Excel file"""
    try:
        cmd = [sys.executable, "export_to_excel.py", "--input-dir", input_dir, "--output", output_file]
        process = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if process.returncode == 0:
            st.success("Results exported to Excel successfully!")
            return True
        else:
            st.error(f"Export failed with return code {process.returncode}")
            st.code(process.stderr)
            return False
    except subprocess.CalledProcessError as e:
        st.error(f"Error exporting to Excel: {str(e)}")
        st.code(e.stderr)
        return False

def display_search_summary(output_dir):
    """Display search summary from the output directory"""
    summary_file = os.path.join(output_dir, "search_summary.txt")
    if os.path.exists(summary_file):
        with open(summary_file, 'r') as f:
            st.text(f.read())
    else:
        st.warning("Summary file not found")

def display_search_results(output_dir):
    """Display search results from JSON files in the output directory"""
    # Find all JSON files in the output directory
    json_files = [f for f in os.listdir(output_dir) if f.endswith('_results.json')]
    
    if not json_files:
        st.warning("No result files found")
        return
    
    # Display tabs for each keyword
    tabs = st.tabs([f.replace('_results.json', '') for f in json_files])
    
    for i, (tab, json_file) in enumerate(zip(tabs, json_files)):
        with tab:
            try:
                with open(os.path.join(output_dir, json_file), 'r') as f:
                    data = json.load(f)
                
                if data:
                    # Convert to DataFrame for display
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)
                    st.write(f"Total products: {len(data)}")
                else:
                    st.info("No products found for this keyword")
            except Exception as e:
                st.error(f"Error loading results: {str(e)}")

def main():
    # Main App
    st.title("Direct Derma Scraper")
    st.write("Search for products on Direct Derma by keywords or direct URLs.")
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Keyword Search", "URL Scraper", "Results", "About"])
    
    with tab1:
        # File upload section for keywords
        st.header("Search by Keywords")
        
        # Add option to choose input method
        keyword_input_method = st.radio("Input method:", ["Upload file", "Enter keywords manually"], key="keyword_input_method")
        
        keywords = []
        
        if keyword_input_method == "Upload file":
            file_type = st.radio("File type:", ["Text file (.txt)", "Excel file (.xlsx)"], key="keyword_file_type")
            
            # Column name input for Excel
            column_name = None
            if file_type == "Excel file (.xlsx)":
                column_name = st.text_input("Column name (leave empty to use first column):")
            
            uploaded_file = st.file_uploader(
                "Upload a file with keywords:", 
                type=["txt", "xlsx"] if file_type == "Excel file (.xlsx)" else ["txt"],
                help="For text files, each line should contain one keyword. For Excel files, keywords should be in the first column or specified column.",
                key="keyword_uploader"
            )
            
            if uploaded_file is not None:
                st.write(f"File uploaded: {uploaded_file.name}")
                
                # Extract keywords from the file
                is_excel = file_type == "Excel file (.xlsx)"
                keywords = read_keywords_from_file(uploaded_file, is_excel, column_name)
        else:
            # Manual keyword entry
            keyword_text = st.text_area(
                "Enter keywords (one per line):",
                height=200,
                help="Enter one keyword per line."
            )
            
            if keyword_text:
                keywords = [keyword.strip() for keyword in keyword_text.split("\n") if keyword.strip()]
        
        # Directory for results
        output_dir = st.text_input("Output directory:", "keyword_results")
        
        # Search button
        if keywords:
            st.write(f"Found {len(keywords)} keywords:")
            st.write(", ".join(keywords[:10]) + ("..." if len(keywords) > 10 else ""))
            
            # Run search
            if st.button("Run Keyword Search"):
                # Create output directory if it doesn't exist
                os.makedirs(output_dir, exist_ok=True)
                
                # Show progress
                with st.spinner("Running search..."):
                    start_time = time.time()
                    success = run_batch_search(keywords, output_dir)
                    end_time = time.time()
                    
                    if success:
                        st.success(f"Search completed in {end_time - start_time:.2f} seconds!")
                        
                        # Create Excel file
                        excel_file = f"keyword_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                        with st.spinner("Exporting results to Excel..."):
                            export_success = export_to_excel(output_dir, excel_file)
                            
                            if export_success and os.path.exists(excel_file):
                                # Provide download link
                                with open(excel_file, "rb") as file:
                                    st.download_button(
                                        label="Download Excel Results",
                                        data=file,
                                        file_name=excel_file,
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                    )
                    else:
                        st.error("Search failed. Check the logs for details.")
        else:
            if keyword_input_method == "Upload file":
                st.warning("Please upload a file with keywords.")
            else:
                st.warning("Please enter at least one keyword.")
    
    with tab2:
        # URL scraper section
        st.header("Scrape Direct URLs")
        st.write("Enter specific product URLs to scrape directly, bypassing the search step.")
        
        url_input_method = st.radio(
            "URL input method:", 
            ["Enter URLs manually", "Upload URL file"],
            key="url_input_method"
        )
        
        urls_to_scrape = []
        
        if url_input_method == "Enter URLs manually":
            url_text = st.text_area(
                "Enter URLs (one per line):",
                height=200,
                help="Enter one URL per line. Each URL should be a direct product URL from Direct Derma."
            )
            
            if url_text:
                urls_to_scrape = [url.strip() for url in url_text.split("\n") if url.strip()]
                
        else:  # Upload URL file
            file_type = st.radio("File type:", ["Text file (.txt)", "Excel file (.xlsx)"], key="url_file_type")
            
            column_name = None
            if file_type == "Excel file (.xlsx)":
                column_name = st.text_input("Column name for URLs (leave empty to use first column):", 
                                          key="url_column_name")
            
            url_file = st.file_uploader(
                "Upload a file with URLs:", 
                type=["txt", "xlsx"] if file_type == "Excel file (.xlsx)" else ["txt"],
                help="For text files, each line should contain one URL. For Excel files, URLs should be in the first column or specified column.",
                key="url_uploader"
            )
            
            if url_file is not None:
                try:
                    st.write(f"File uploaded: {url_file.name}")
                    
                    if file_type == "Excel file (.xlsx)":
                        # Excel file processing
                        urls_to_scrape = read_keywords_from_file(url_file, is_excel=True, column_name=column_name)
                    else:
                        # Text file processing
                        content = url_file.getvalue().decode('utf-8')
                        urls_to_scrape = [url.strip() for url in content.split('\n') if url.strip()]
                        
                except Exception as e:
                    st.error(f"Error reading URL file: {str(e)}")
        
        # URL validation 
        valid_urls = []
        if urls_to_scrape:
            # Basic validation - ensure URLs contain the domain and product path
            valid_urls = [url for url in urls_to_scrape if "directdermasupplies.com/products/" in url]
            
            if len(valid_urls) != len(urls_to_scrape):
                st.warning(f"{len(urls_to_scrape) - len(valid_urls)} URLs were invalid and will be skipped.")
            
            st.write(f"Found {len(valid_urls)} valid URLs to scrape:")
            st.write("\n".join(valid_urls[:5]) + ("..." if len(valid_urls) > 5 else ""))
        
        # Output file
        url_output_file = st.text_input("Output file:", "url_scrape_results.json")
        
        # Run scraper
        if valid_urls and st.button("Run URL Scraper"):
            with st.spinner("Scraping URLs..."):
                # Create a temporary file with the URLs
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp:
                    for url in valid_urls:
                        temp.write(f"{url}\n")
                    temp_file = temp.name
                
                try:
                    # Run the scraper
                    cmd = [sys.executable, "run_scraper.py", "--input", temp_file, "--output", url_output_file]
                    process = subprocess.run(cmd, check=True, capture_output=True, text=True)
                    
                    if process.returncode == 0:
                        st.success(f"URL scraping completed successfully!")
                        
                        # Read and display results
                        if os.path.exists(url_output_file):
                            try:
                                with open(url_output_file, 'r') as f:
                                    data = json.load(f)
                                
                                st.write(f"Scraped {len(data)} products:")
                                df = pd.DataFrame(data)
                                st.dataframe(df, use_container_width=True)
                                
                                # Export to Excel option
                                excel_file = f"url_scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                                if st.button("Export to Excel"):
                                    # Convert to Excel
                                    df.to_excel(excel_file, index=False)
                                    
                                    # Provide download link
                                    with open(excel_file, "rb") as file:
                                        st.download_button(
                                            label="Download Excel Results",
                                            data=file,
                                            file_name=excel_file,
                                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                        )
                            except Exception as e:
                                st.error(f"Error processing results: {str(e)}")
                    else:
                        st.error(f"URL scraping failed with return code {process.returncode}")
                        st.code(process.stderr)
                except subprocess.CalledProcessError as e:
                    st.error(f"Error running URL scraper: {str(e)}")
                    st.code(e.stderr)
                finally:
                    # Clean up
                    try:
                        os.remove(temp_file)
                    except:
                        pass
    
    with tab3:
        # Results section
        st.header("View Search Results")
        
        # Input for results directory
        results_dir = st.text_input("Results directory:", "keyword_results", key="results_dir")
        
        # Refresh button
        if st.button("Refresh Results"):
            if os.path.exists(results_dir):
                # Show search summary
                st.subheader("Search Summary")
                display_search_summary(results_dir)
                
                # Show search results
                st.subheader("Search Results")
                display_search_results(results_dir)
                
                # Export to Excel
                if st.button("Export to New Excel File"):
                    excel_file = f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    with st.spinner("Exporting results to Excel..."):
                        export_success = export_to_excel(results_dir, excel_file)
                        
                        if export_success and os.path.exists(excel_file):
                            # Provide download link
                            with open(excel_file, "rb") as file:
                                st.download_button(
                                    label="Download Excel Results",
                                    data=file,
                                    file_name=excel_file,
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
            else:
                st.warning(f"Directory {results_dir} does not exist")
        
        # URL results section
        st.subheader("URL Scrape Results")
        
        url_result_file = st.text_input("URL result file:", "url_scrape_results.json", key="url_result_file")
        
        if os.path.exists(url_result_file) and st.button("Load URL Results"):
            try:
                with open(url_result_file, 'r') as f:
                    data = json.load(f)
                
                st.write(f"Loaded {len(data)} products from URL scrape:")
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)
                
                # Export to Excel option
                excel_file = f"url_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                if st.button("Export URL Results to Excel"):
                    # Convert to Excel
                    df.to_excel(excel_file, index=False)
                    
                    # Provide download link
                    with open(excel_file, "rb") as file:
                        st.download_button(
                            label="Download URL Excel Results",
                            data=file,
                            file_name=excel_file,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
            except Exception as e:
                st.error(f"Error loading URL results: {str(e)}")
    
    with tab4:
        # About section
        st.header("About This App")
        st.write("""
        This app allows you to search for products on Direct Derma based on keywords or directly scrape specific product URLs.
        
        ### Options:
        1. **Keyword Search**: Search products by keywords and scrape details for all matching products
        2. **URL Scraper**: Directly scrape specific product URLs, bypassing the search step
        
        ### How to use:
        
        #### Keyword Search:
        1. **Upload a file** with keywords (text file or Excel) or **enter keywords manually**
        2. **Run the search** to find and scrape matching products
        3. **View results** in the Results tab
        4. **Download results** as an Excel file
        
        #### URL Scraper:
        1. **Enter URLs** manually or upload a text/Excel file with URLs
        2. **Run the scraper** to directly scrape product information
        3. **View results** immediately
        4. **Export to Excel** if needed
        
        ### Output:
        The Excel files will contain the following columns:
        - Keyword used for search (for keyword search only)
        - Product name
        - Price
        - Currency
        - Product URL
        - Timestamp of when the data was scraped
        """)

if __name__ == "__main__":
    main() 