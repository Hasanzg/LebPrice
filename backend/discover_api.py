"""
Utility script to discover and test API endpoints for WooCommerce stores.
Run this once for any new store to find the correct API endpoint.

Usage:
    python discover_api.py
"""

import requests
import json
from store_config import PCAndPartsConfig

def test_endpoint_detailed(config, category, page=1):
    """Test an endpoint with detailed output."""
    url = f"{config.base_api}?category={category}&page={page}"
    
    print(f"\n{'='*70}")
    print(f"Testing: {url}")
    print(f"{'='*70}")
    
    try:
        r = requests.get(url, headers=config.headers, timeout=15)
        print(f"Status Code: {r.status_code}")
        print(f"Content-Type: {r.headers.get('Content-Type', 'Unknown')}")
        print(f"Response Size: {len(r.content)} bytes")
        
        if r.status_code == 200:
            try:
                data = r.json()
                print(f"Valid JSON Response")
                print(f"Items Count: {len(data) if isinstance(data, list) else 'N/A'}")
                
                if isinstance(data, list) and len(data) > 0:
                    print(f"\nSample Product (first item):")
                    print(f"{'─'*70}")
                    sample = data[0]
                    print(f"  ID: {sample.get('id')}")
                    print(f"  Name: {sample.get('name')}")
                    print(f"  Price: {sample.get('price_html', 'N/A')}")
                    print(f"  Stock: {sample.get('is_in_stock', 'N/A')}")
                    print(f"  URL: {sample.get('permalink', 'N/A')}")
                    print(f"  Available Keys: {', '.join(sample.keys())}")
                    return True
                elif isinstance(data, dict):
                    print(f"\nResponse Structure (dict):")
                    print(f"{'─'*70}")
                    print(f"  Keys: {', '.join(data.keys())}")
                    return False
                else:
                    print(f"Empty response")
                    return False
                    
            except json.JSONDecodeError as e:
                print(f"Invalid JSON: {e}")
                print(f"Response preview: {r.text[:200]}")
                return False
        else:
            print(f"Request failed")
            print(f"Response preview: {r.text[:200]}")
            return False
            
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def test_all_categories(config):
    """Test API endpoint with all categories."""
    print(f"\n{'='*70}")
    print(f"Testing All Categories for {config.store_name}")
    print(f"{'='*70}")
    
    working_categories = []
    failed_categories = []
    
    for category in config.categories:
        url = f"{config.base_api}?category={category}&page=1"
        try:
            r = requests.get(url, headers=config.headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data and len(data) > 0:
                    working_categories.append((category, len(data)))
                    print(f"{category:25s} - {len(data):3d} products")
                else:
                    failed_categories.append(category)
                    print(f"{category:25s} - Empty")
            else:
                failed_categories.append(category)
                print(f"{category:25s} - Status {r.status_code}")
        except Exception as e:
            failed_categories.append(category)
            print(f"{category:25s} - Error: {str(e)[:30]}")
    
    print(f"\n{'='*70}")
    print(f"Summary:")
    print(f"  Working categories: {len(working_categories)}")
    print(f"  Failed categories: {len(failed_categories)}")
    print(f"  Total products found: {sum(count for _, count in working_categories)}")
    print(f"{'='*70}")
    
    return working_categories, failed_categories

def main():
    print("="*70)
    print("API Endpoint Discovery Tool")
    print("="*70)
    
    # Initialize config with auto-discovery
    print("\nStep 1: Auto-discovering API endpoint...")
    config = PCAndPartsConfig(auto_discover=True)
    
    if not config.base_api:
        print("\nNo API endpoint found!")
        print("The store might not have a JSON API or uses a different structure.")
        return
    
    print(f"\nUsing API: {config.base_api}")
    
    # Test with first category
    print("\nStep 2: Testing with first category...")
    first_category = config.categories[0]
    success = test_endpoint_detailed(config, first_category)
    
    if success:
        # Test all categories
        print("\nStep 3: Testing all categories...")
        response = input("\nTest all categories? (y/n): ")
        if response.lower() == 'y':
            working, failed = test_all_categories(config)
            
            if failed:
                print(f"\nFailed categories: {', '.join(failed)}")
        
        print("\n" + "="*70)
        print("API Discovery Complete!")
        print("="*70)
        print(f"Add this to your store config:")
        print(f"\n  self.base_api = \"{config.base_api}\"")
        print("\nYou can now run crawler.py to scrape all products.")
    else:
        print("\nAPI endpoint test failed!")
        print("The endpoint exists but doesn't return expected data format.")

if __name__ == "__main__":
    main()