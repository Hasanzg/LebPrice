"""
Store configuration classes for web scrapers.
Each store has its own configuration class with categories and tax settings.
"""

import requests
import json
import re
from bs4 import BeautifulSoup
from decimal import Decimal


class StoreConfig:
    """Base class for store configurations."""
    
    def __init__(self):
        self.store_name = ""
        self.base_url = ""  # Base URL of the store (e.g., https://pcandparts.com)
        self.base_api = ""  # Will be discovered or set manually
        self.api_discovered = False  # Whether API endpoint was auto-discovered
        self.categories = []
        self.store_type = "general"  # Type of store: tech, fashion, grocery, etc.
        self.headers = {}
        self.tax_included = False  # Default: prices do NOT include tax
        self.tax_rate = Decimal('0.11')  # 11% tax rate as Decimal
        self.tax_exempt_phrases = []  # Product name phrases that are tax-exempt
    
    def calculate_final_price(self, price, product_name):
        """
        Calculate final price based on tax settings.
        
        Args:
            price: Original price (Decimal)
            product_name: Product name to check for exemptions
            
        Returns:
            tuple: (price_before_tax, final_price_after_tax)
        """
        if not price:
            return None, None
        
        # Ensure price is Decimal
        if not isinstance(price, Decimal):
            price = Decimal(str(price))
        
        # Ensure tax_rate is Decimal
        if not isinstance(self.tax_rate, Decimal):
            self.tax_rate = Decimal(str(self.tax_rate))
        
        # Check if product is tax-exempt
        is_exempt = False
        if product_name and self.tax_exempt_phrases:
            product_name_lower = product_name.lower()
            for phrase in self.tax_exempt_phrases:
                if phrase.lower() in product_name_lower:
                    is_exempt = True
                    break
        
        if self.tax_included:
            # Price already includes tax
            price_before_tax = price
            final_price = price
        else:
            # Price does not include tax, need to add it
            price_before_tax = price
            if is_exempt:
                final_price = price
            else:
                final_price = price * (Decimal('1') + self.tax_rate)
        
        return price_before_tax, final_price
    
    def discover_api_endpoint(self, test_category=None):
        """
        Automatically discover the JSON API endpoint for WooCommerce stores.
        
        Args:
            test_category: Category to test with (uses first category if None)
            
        Returns:
            str: Discovered API endpoint or None
        """
        if not self.base_url or not self.categories:
            return None
        
        test_cat = test_category or self.categories[0]
        
        # Common WooCommerce API endpoint patterns
        endpoints_to_test = [
            f"{self.base_url}/wp-json/wc/store/products?category={test_cat}&page=1",
            f"{self.base_url}/wp-json/wc/v3/products?category={test_cat}&page=1",
            f"{self.base_url}/wp-json/wc/v2/products?category={test_cat}&page=1",
            f"{self.base_url}/?wc-ajax=get_products&category={test_cat}&page=1",
        ]
        
        print(f"Discovering API endpoint for {self.store_name}...")
        
        for endpoint in endpoints_to_test:
            try:
                r = requests.get(endpoint, headers=self.headers, timeout=10)
                if r.status_code == 200:
                    try:
                        data = r.json()
                        if data and len(data) > 0:
                            # Extract the base pattern without query params
                            if "/wp-json/wc/store/products" in endpoint:
                                self.base_api = f"{self.base_url}/wp-json/wc/store/products"
                            elif "/wp-json/wc/v3/products" in endpoint:
                                self.base_api = f"{self.base_url}/wp-json/wc/v3/products"
                            elif "/wp-json/wc/v2/products" in endpoint:
                                self.base_api = f"{self.base_url}/wp-json/wc/v2/products"
                            elif "wc-ajax=get_products" in endpoint:
                                self.base_api = f"{self.base_url}/?wc-ajax=get_products"
                            
                            self.api_discovered = True
                            print(f"Found working API: {self.base_api}")
                            return self.base_api
                    except json.JSONDecodeError:
                        continue
            except Exception as e:
                continue
        
        print(f"No JSON API found. Will attempt HTML scraping fallback.")
        return None
    
    def extract_json_from_html(self, soup):
        """
        Extract JSON data embedded in HTML (common WooCommerce pattern).
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            list: Product data or None
        """
        # Look for JSON in script tags
        scripts = soup.find_all('script', type='application/json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and 'products' in data:
                    return data['products']
                if isinstance(data, list) and len(data) > 0:
                    return data
            except:
                continue
        
        # Look for inline JavaScript with product data
        all_scripts = soup.find_all('script')
        for script in all_scripts:
            if script.string:
                # Look for common patterns like var products = {...}
                matches = re.findall(r'var\s+products\s*=\s*(\[.*?\]);', script.string, re.DOTALL)
                for match in matches:
                    try:
                        return json.loads(match)
                    except:
                        continue
        return None


class PCAndPartsConfig(StoreConfig):
    """Configuration for PC and Parts store."""
    
    def __init__(self, auto_discover=True):
        super().__init__()
        
        self.store_name = "PC and Parts"
        self.base_url = "https://pcandparts.com"
        self.base_api = "https://pcandparts.com/wp-json/wc/store/products"  # Default, can be discovered
        
        self.categories = [
            "computer-cases", "cooling", "cpu", "ram", "motherboard",
            "power-supplies", "storage", "video-card", "home-tv-monitor",
            "camera", "ipad", "ipod", "mobile-phone", "tablet", "watch",
            "barcode-reader", "flash-memory", "keyboard-mouse", "monitor",
            "keyboard", "Headset", "speaker", "access-point", "desktops",
            "laptops", "accessories", "software"
        ]
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/130.0 Safari/537.36"
        }
        
        # Tax settings for PC and Parts - MUST use Decimal for tax_rate
        self.tax_included = False  # Prices do NOT include tax
        self.tax_rate = Decimal('0.11')  # 11% tax as Decimal
        
        # Example: Products with these phrases in their name are tax-exempt
        # Add phrases as needed, e.g., ["gift card", "warranty", "service"]
        self.tax_exempt_phrases = []
        
        # Auto-discover API endpoint if requested
        if auto_discover:
            discovered = self.discover_api_endpoint()
            if not discovered:
                print(f"Using default API endpoint: {self.base_api}")


# Example of another store configuration
class EzoneConfig(StoreConfig):
    """Configuration for another store (example)."""
    
    def __init__(self, auto_discover=True):
        super().__init__()
        
        self.store_name = "Expert Zone"
        self.base_url = "https://ezonelb.com/"
        self.base_api = "https://ezonelb.com//wp-json/wc/store/products"  # Default
        self.categories = [
            "accessories","desktop-laptop-vr","screens","computer-parts","external-hdd","converters","cables","power-charging","network","printers","ups","security-softwares",
            "office-pos","surveillance-camera","openbox-products","rgb-lighting-acc","gaming-furniture","laptop-parts",
        ]
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/130.0 Safari/537.36"
        }
        
        # This store includes tax in prices
        self.tax_included = True
        self.tax_rate = Decimal('0.11')
        self.tax_exempt_phrases = ["gift card"]
        
        # Auto-discover API endpoint if requested
        if auto_discover:
            discovered = self.discover_api_endpoint()
            if not discovered:
                print(f"Using default API endpoint: {self.base_api}")