import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.common.by import By
import re
import os
import json
from datetime import datetime
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError, TimeoutError

class ProductPriceSpider(scrapy.Spider):
    name = "product_price"
    allowed_domains = ["directdermasupplies.com"]
    
    # Default URL if no input file is provided
    start_urls = [
        "https://www.directdermasupplies.com/products/thermage/thermage-eye-tip-0-25cm2-450-rep"
    ]
    
    # Custom settings for this spider
    custom_settings = {
        'DOWNLOAD_TIMEOUT': 180,
        'RETRY_TIMES': 3,
        'HTTPERROR_ALLOW_ALL': True,  # Allow processing non-200 responses
    }

    def __init__(self, input_file=None, *args, **kwargs):
        super(ProductPriceSpider, self).__init__(*args, **kwargs)
        
        # Allow loading URLs from a file
        if input_file and os.path.exists(input_file):
            with open(input_file, 'r') as f:
                self.start_urls = [line.strip() for line in f.readlines() if line.strip()]
                self.logger.info(f"Loaded {len(self.start_urls)} URLs from {input_file}")
                
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Add user agent to match the one in settings.py
        chrome_options.add_argument("user-agent=direct_derma_price_scraper (+http://www.yourdomain.com)")
        
        # Initialize the Chrome driver
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        # Create a debug directory if it doesn't exist
        self.debug_dir = "debug_output"
        if not os.path.exists(self.debug_dir):
            os.makedirs(self.debug_dir)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                errback=self.errback_handler,
                meta={'dont_redirect': True, 'handle_httpstatus_list': [404, 500, 503]}
            )

    def parse(self, response):
        # Check if response is an error
        if response.status >= 400:
            self.logger.error(f"Error {response.status} when accessing {response.url}")
            return {
                'product_url': response.url,
                'product_name': None,
                'price': None,
                'currency': None,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'error': f"HTTP Error: {response.status}"
            }
            
        # Use Selenium to get the page
        try:
            self.driver.get(response.url)
            
            # Wait for JavaScript to load
            time.sleep(5)
            
            # Save page source for debugging with timestamp and sanitized URL
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sanitized_url = re.sub(r'[^\w]', '_', response.url)[:50]  # Take first 50 chars to avoid filename too long
            debug_file = os.path.join(self.debug_dir, f"{timestamp}_{sanitized_url}.html")
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            
            self.logger.info("Page title: %s", self.driver.title)
            
            price = None
            product_name = None
            
            # Try to extract product name
            try:
                product_name_element = self.driver.find_element(By.CSS_SELECTOR, "h1")
                product_name = product_name_element.text.strip()
                self.logger.info(f"Found product name: {product_name}")
            except Exception as e:
                self.logger.error(f"Failed to extract product name: {str(e)}")
            
            # Try multiple methods to extract the price
            try:
                # Method 1: Look for the product price with class "price price--product-page"
                price_element = self.driver.find_element(By.CSS_SELECTOR, ".price.price--product-page")
                price_text = price_element.text.strip()
                if price_text:
                    price = price_text
                    self.logger.info("Found price with method 1: %s", price)
            except Exception as e:
                self.logger.error("Method 1 failed: %s", str(e))
                
                try:
                    # Method 2: Try a more generic XPath for price elements
                    price_element = self.driver.find_element(By.XPATH, "//*[contains(@class, 'price') and contains(@class, 'product')]")
                    price_text = price_element.text.strip()
                    if price_text:
                        price = price_text
                        self.logger.info("Found price with method 2: %s", price)
                except Exception as e:
                    self.logger.error("Method 2 failed: %s", str(e))
                    
                    try:
                        # Method 3: Try to find any element containing "EUR" followed by digits
                        elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'EUR')]")
                        for elem in elements:
                            text = elem.text.strip()
                            if 'EUR' in text:
                                price = text
                                self.logger.info("Found price with method 3: %s", price)
                                break
                    except Exception as e:
                        self.logger.error("Method 3 failed: %s", str(e))
            
            # If all direct methods failed, try using scrapy selectors on the page source
            if not price:
                page_source = self.driver.page_source
                selenium_response = scrapy.http.HtmlResponse(
                    url=response.url,
                    body=page_source.encode('utf-8'),
                    encoding='utf-8'
                )
                
                # Try multiple CSS selectors
                selectors = [
                    '.price.price--product-page::text',
                    '.product__price-wrap .price::text',
                    '.price--product-page::text',
                    'div.price::text',
                    '.product__price-wrap div.price::text'
                ]
                
                for selector in selectors:
                    price_text = selenium_response.css(selector).get()
                    if price_text:
                        price = price_text.strip()
                        self.logger.info("Found price with selector %s: %s", selector, price)
                        break
            
            # Clean up the price if found
            if price:
                # Extract number from price (e.g., "EUR 240,00" -> "240.00")
                number_match = re.search(r'(\d+[,.]\d+|\d+)', price)
                if number_match:
                    price_number = number_match.group(0)
                    # Convert comma to dot for decimal
                    price_number = price_number.replace(',', '.')
                    self.logger.info("Cleaned price: %s", price_number)
                    price = price_number
            
            # Extract currency if present
            currency = None
            if price and 'price_text' in locals():
                currency_match = re.search(r'([A-Z]{3})', price_text)
                if currency_match:
                    currency = currency_match.group(0)
            
            self.logger.info("Final price extracted: %s", price)
            
            # Create result item
            result = {
                'product_url': response.url,
                'product_name': product_name,
                'price': price,
                'currency': currency,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing {response.url}: {str(e)}")
            return {
                'product_url': response.url,
                'price': None,
                'error': str(e),
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def errback_handler(self, failure):
        """Handle request failures"""
        request = failure.request
        
        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error(f"HttpError {response.status} on {request.url}")
            return {
                'product_url': request.url,
                'price': None,
                'error': f"HTTP Error: {response.status}",
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        elif failure.check(DNSLookupError):
            self.logger.error(f"DNSLookupError on {request.url}")
            return {
                'product_url': request.url,
                'price': None,
                'error': "DNS Lookup Error",
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        elif failure.check(TimeoutError):
            self.logger.error(f"TimeoutError on {request.url}")
            return {
                'product_url': request.url,
                'price': None,
                'error': "Timeout Error",
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        else:
            self.logger.error(f"Unknown error on {request.url}: {repr(failure)}")
            return {
                'product_url': request.url,
                'price': None,
                'error': f"Unknown error: {repr(failure)}",
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
    def closed(self, reason):
        # Close the browser when spider is closed
        self.driver.quit()