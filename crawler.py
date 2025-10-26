"""
Standalone scraper that saves to Django database.
Class-driven architecture supporting multiple stores.
Can run independently: python crawler.py
"""

import os
import sys
import django
import requests
import time
from bs4 import BeautifulSoup
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from decimal import Decimal, InvalidOperation
from datetime import datetime

# Import store configurations
from store_config import PCAndPartsConfig, EzoneConfig

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    django.setup()
    from products.models import Product, Category, PriceHistory
    from django.utils import timezone
    from django.db import transaction, OperationalError
    USE_DJANGO = True
    print("Django database connection established")
except Exception as e:
    USE_DJANGO = False
    print(f"Django not available, will save to CSV only: {e}")


class StoreScraper:
    """Generic scraper that works with any StoreConfig."""
    
    def __init__(self, store_config):
        """
        Initialize scraper with a store configuration.
        
        Args:
            store_config: Instance of StoreConfig (e.g., PCAndPartsConfig)
        """
        self.config = store_config
        self.print_lock = Lock()
        self.stats = {
            'total_fetched': 0,
            'db_created': 0,
            'db_updated': 0,
            'db_errors': 0,
            'db_skipped': 0,
            'pages_retried': 0,
            'pages_failed': 0
        }
        
        # Ensure API endpoint is set or discovered
        if not self.config.base_api and hasattr(self.config, 'discover_api_endpoint'):
            self.config.discover_api_endpoint()
    
    def safe_print(self, message):
        """Thread-safe printing."""
        with self.print_lock:
            print(message)
    
    def clean_html(self, text):
        """Remove HTML tags and clean up text."""
        if not text:
            return None
        soup = BeautifulSoup(text, "html.parser")
        cleaned = soup.get_text(separator=" ", strip=True)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()
    
    def extract_price(self, price_html):
        """Extract numeric price from HTML price string."""
        if not price_html:
            return None
        clean = self.clean_html(price_html)
        match = re.search(r'[\d,]+\.?\d*', clean)
        if match:
            price_str = match.group(0).replace(',', '')
            try:
                return Decimal(price_str)
            except InvalidOperation:
                return None
        return None
    
    def save_to_django_db(self, product_data, category_name):
        """Save product to Django database with retry logic and duplicate prevention."""
        if not USE_DJANGO:
            return None, False
        
        max_retries = 5
        retry_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                with transaction.atomic():
                    # Get or create category
                    category, _ = Category.objects.get_or_create(
                        name=category_name,
                        defaults={'slug': category_name.lower().replace(' ', '-')}
                    )
                    
                    # Convert stock status
                    stock_status = 'in_stock' if product_data['stock_status'] == 'In Stock' else 'out_of_stock'
                    
                    # Check if product already exists
                    try:
                        existing_product = Product.objects.get(
                            product_id=product_data['product_id'],
                            store_name=self.config.store_name
                        )
                        old_price = existing_product.price
                        created = False
                    except Product.DoesNotExist:
                        old_price = None
                        created = True
                    
                    # Prepare base fields that always exist
                    defaults = {
                        'sku': product_data.get('sku'),
                        'category': category,
                        'product_name': product_data['product_name'],
                        'description': product_data.get('description'),
                        'price': product_data.get('price'),
                        'currency': product_data.get('currency', 'USD'),
                        'stock_status': stock_status,
                        'product_url': product_data['product_url'],
                        'image_url': product_data.get('image_url'),
                        'last_scraped': timezone.now()
                    }
                    
                    # Add store_type if available in model
                    try:
                        model_fields = [f.name for f in Product._meta.get_fields()]
                        
                        if 'store_type' in model_fields:
                            defaults['store_type'] = product_data.get('store_type', 'general')
                        
                        if 'price_before_tax' in model_fields:
                            defaults['price_before_tax'] = product_data.get('price_before_tax')
                        
                        if 'final_price_after_tax' in model_fields:
                            defaults['final_price_after_tax'] = product_data.get('final_price_after_tax')
                    except Exception:
                        # If we can't check fields, just skip optional fields
                        pass
                    
                    # Update or create product
                    product, was_created = Product.objects.update_or_create(
                        product_id=product_data['product_id'],
                        store_name=self.config.store_name,
                        defaults=defaults
                    )
                    
                    # Track price changes only if product was updated (not created)
                    if not created and old_price and product_data.get('price'):
                        if old_price != product_data['price']:
                            PriceHistory.objects.create(
                                product=product,
                                price=old_price,
                                currency=product.currency,
                                stock_status=product.stock_status
                            )
                    
                    # Update stats
                    with self.print_lock:
                        if was_created:
                            self.stats['db_created'] += 1
                        else:
                            self.stats['db_updated'] += 1
                    
                    return product, was_created
                
            except OperationalError as e:
                if 'database is locked' in str(e) and attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    with self.print_lock:
                        self.stats['db_errors'] += 1
                    self.safe_print(f"  [DB Error] {product_data.get('product_id')}: {e}")
                    return None, False
                    
            except Exception as e:
                with self.print_lock:
                    self.stats['db_errors'] += 1
                self.safe_print(f"  [DB Error] {product_data.get('product_id')}: {e}")
                return None, False
        
        # If all retries failed
        with self.print_lock:
            self.stats['db_errors'] += 1
        return None, False
    
    def fetch_page(self, category, page):
        """Fetch a single page of products with retry logic."""
        url = f"{self.config.base_api}?category={category}&page={page}"
        
        # Use retry logic from store config
        max_retries = getattr(self.config, 'max_retries', 3)
        retry_delay = getattr(self.config, 'retry_delay', 2)
        timeout = getattr(self.config, 'timeout', 15)
        
        response = None
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(url, headers=self.config.headers, timeout=timeout)
                
                if response.status_code != 200:
                    self.safe_print(f"[{category}] Page {page} returned status {response.status_code}")
                    return None
                
                # Success - break out of retry loop
                break
                
            except requests.exceptions.Timeout:
                with self.print_lock:
                    self.stats['pages_retried'] += 1
                self.safe_print(f"[{category}] Page {page}  Timeout (attempt {attempt}/{max_retries})")
                
                if attempt < max_retries:
                    wait_time = retry_delay * attempt  # Exponential backoff
                    self.safe_print(f"[{category}] Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    with self.print_lock:
                        self.stats['pages_failed'] += 1
                    self.safe_print(f"[{category}] Page {page} X Failed after {max_retries} attempts")
                    return None
                    
            except requests.exceptions.ConnectionError as e:
                with self.print_lock:
                    self.stats['pages_retried'] += 1
                self.safe_print(f"[{category}] Page {page}  Connection error (attempt {attempt}/{max_retries})")
                
                if attempt < max_retries:
                    wait_time = retry_delay * attempt
                    self.safe_print(f"[{category}] Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    with self.print_lock:
                        self.stats['pages_failed'] += 1
                    self.safe_print(f"[{category}] Page {page} X Failed after {max_retries} attempts")
                    return None
                    
            except requests.RequestException as e:
                self.safe_print(f"[{category}] Request error on page {page}: {e}")
                with self.print_lock:
                    self.stats['pages_failed'] += 1
                return None
        
        # If no response after retries
        if response is None:
            with self.print_lock:
                self.stats['pages_failed'] += 1
            return None
        
        # Process the successful response
        try:
            # Try to parse as JSON
            try:
                data = response.json()
            except ValueError:
                self.safe_print(f"[{category}] Page {page} did not return valid JSON")
                return None
            
            if not data or len(data) == 0:
                return None
            
            products = []
            for item in data:
                image_url = None
                if item.get('images') and len(item['images']) > 0:
                    image_url = item['images'][0].get('src')
                
                price_html = item.get('price_html', '')
                price = self.extract_price(price_html)
                description = self.clean_html(item.get('short_description', ''))
                stock_status = 'In Stock' if item.get('is_in_stock') else 'Out Of Stock'
                product_name = item.get('name')
                
                # Calculate tax prices using store configuration
                price_before_tax, final_price_after_tax = self.config.calculate_final_price(
                    price, product_name
                )
                
                product_data = {
                    "store_name": self.config.store_name,
                    "category": category,
                    "product_name": product_name,
                    "price": price,  # Original scraped price
                    "price_before_tax": price_before_tax,
                    "final_price_after_tax": final_price_after_tax,
                    "currency": "USD",
                    "stock_status": stock_status,
                    "product_url": item.get('permalink'),
                    "image_url": image_url,
                    "description": description,
                    "product_id": item.get('id'),
                    "sku": item.get('sku')
                }
                
                # Save to Django DB immediately
                if USE_DJANGO:
                    self.save_to_django_db(product_data, category)
                
                products.append(product_data)
            
            with self.print_lock:
                self.stats['total_fetched'] += len(products)
            
            return products
            
        except Exception as e:
            self.safe_print(f"[{category}] Error processing page {page}: {e}")
            return None
    
    def get_category_products(self, category, max_workers=1):
        """Fetch all products from a category using multithreading."""
        self.safe_print(f"Starting category: {category}")
        
        all_products = []
        page = 1
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            
            while True:
                future = executor.submit(self.fetch_page, category, page)
                futures.append((page, future))
                page += 1
                
                # Check first page to see if category exists
                if page == 2:
                    result = futures[0][1].result()
                    if result is None:
                        self.safe_print(f"[{category}] No products found")
                        return []
                
                # Fetch pages in batches
                if len(futures) >= max_workers * 2:
                    break
            
            # Continue fetching until no more results
            while futures or page < 500:
                # Submit new page requests
                while len(futures) < max_workers * 2 and page < 500:
                    future = executor.submit(self.fetch_page, category, page)
                    futures.append((page, future))
                    page += 1
                
                # Process completed futures
                completed = []
                for i, (page_num, future) in enumerate(futures):
                    if future.done():
                        result = future.result()
                        if result is None:
                            page = 500  # Stop pagination
                        else:
                            all_products.extend(result)
                            self.safe_print(f"[{category}] Page {page_num}: {len(result)} products")
                        completed.append(i)
                
                # Remove completed futures
                for i in sorted(completed, reverse=True):
                    page_num, future = futures.pop(i)
                    if future.result() is None:
                        page = 500
                
                if not futures:
                    break
                
                time.sleep(0.1)
        
        self.safe_print(f"[{category}] ✓ Total: {len(all_products)} products")
        return all_products
    
    def scrape_all_categories(self, max_workers=1):
        """Scrape all categories sequentially to avoid database locks."""
        all_products = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_category = {
                executor.submit(self.get_category_products, cat, max_workers=1): cat 
                for cat in self.config.categories
            }

            for future in as_completed(future_to_category):
                category = future_to_category[future]
                try:
                    products = future.result()
                    all_products.extend(products)
                except Exception as e:
                    self.safe_print(f"[{category}] Failed: {e}")
        
        return all_products
    
    def save_to_csv(self, products):
        """Save products to CSVs folder as backup."""
        if not products:
            return
        
        try:
            import pandas as pd
            import os

            # Create CSVs directory if it doesn't exist
            os.makedirs("CSVs", exist_ok=True)
            
            df = pd.DataFrame(products)
            
            column_order = [
                'product_id', 'store_name', 'sku', 'category', 'product_name',
                'price', 'price_before_tax', 'final_price_after_tax', 'currency',
                'stock_status', 'product_url', 'image_url', 'description'
            ]
            df = df[column_order]
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            store_slug = self.config.store_name.lower().replace(' ', '_')
            filename = os.path.join("CSVs", f"{store_slug}_products_{timestamp}.csv")
            latest_filename = os.path.join("CSVs", f"{store_slug}_products_latest.csv")
            
            df.to_csv(filename, index=False, encoding='utf-8')
            df.to_csv(latest_filename, index=False, encoding='utf-8')
            
            print(f"CSV saved: {filename}")
            
        except Exception as e:
            print(f"Error saving CSV: {e}")

    
    def run(self):
        """Main execution method."""
        start_time = time.time()
        
        print("="*60)
        print(f"{self.config.store_name} Scraper - Django Compatible")
        print("="*60)
        print(f"Store: {self.config.store_name}")
        print(f"Database: {'Django ✓' if USE_DJANGO else 'CSV only'}")
        print(f"Categories: {len(self.config.categories)}")
        print(f"Tax Settings: {'Included' if self.config.tax_included else 'Not Included'} ({self.config.tax_rate*100}%)")
        print(f"Retry Settings: {getattr(self.config, 'max_retries', 3)} attempts, {getattr(self.config, 'timeout', 15)}s timeout")
        print(f"Workers: 1 category at a time (SQLite safe)")
        print("="*60)
        print()
        
        # Scrape all products
        all_products = self.scrape_all_categories(max_workers=1)
        
        elapsed = time.time() - start_time
        
        print()
        print("="*60)
        print("Scraping Completed!")
        print("="*60)
        print(f"Products fetched: {self.stats['total_fetched']}")
        print(f"Pages retried: {self.stats['pages_retried']}")
        print(f"Pages failed: {self.stats['pages_failed']}")
        
        if USE_DJANGO:
            print(f"Database - Created: {self.stats['db_created']}")
            print(f"Database - Updated: {self.stats['db_updated']}")
            print(f"Database - Errors: {self.stats['db_errors']}")
            print(f"Total in DB: {self.stats['db_created'] + self.stats['db_updated']}")
        
        print(f"Time elapsed: {elapsed:.2f} seconds")
        print("="*60)
        
        # Save CSV as backup
        if all_products:
            self.save_to_csv(all_products)
        
        return all_products


def main():
    """Run the scraper with PC and Parts configuration."""
    # Create store configuration with auto-discovery
    # Set auto_discover=False to skip API discovery and use default
    config = EzoneConfig(auto_discover=True)
    config2 = PCAndPartsConfig(auto_discover=True)
    # Create and run scraper
    scraper = StoreScraper(config)
    scraper2 = StoreScraper(config2)
    scraper.run()
    scraper2.run()


if __name__ == "__main__":
    main()