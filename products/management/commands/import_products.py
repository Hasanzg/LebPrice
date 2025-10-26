"""
Management command to import products from CSV
Place this file in: products/management/commands/import_products.py

Create the directory structure if it doesn't exist:
products/
  management/
    __init__.py
    commands/
      __init__.py
      import_products.py
"""

import csv
from django.core.management.base import BaseCommand
from products.models import Product, Category
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Import products from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            imported = 0
            skipped = 0
            
            for row in reader:
                # Skip empty rows
                if not row.get('product_id') or not row.get('product_name'):
                    skipped += 1
                    continue
                
                # Get or create category
                category = None
                if row.get('category'):
                    category, _ = Category.objects.get_or_create(
                        slug=slugify(row['category']),
                        defaults={'name': row['category'].replace('-', ' ').title()}
                    )
                
                # Prepare stock status
                stock_status = 'out_of_stock'
                if row.get('stock_status'):
                    if 'in stock' in row['stock_status'].lower():
                        stock_status = 'in_stock'
                
                # Parse price
                price = None
                if row.get('price'):
                    try:
                        price = float(row['price'].replace(',', ''))
                    except (ValueError, AttributeError):
                        pass
                
                # Create or update product
                product, created = Product.objects.update_or_create(
                    product_id=row['product_id'],
                    store_name=row.get('store_name', 'Unknown'),
                    defaults={
                        'sku': row.get('sku', ''),
                        'category': category,
                        'product_name': row['product_name'],
                        'description': row.get('description', ''),
                        'price': price,
                        'currency': row.get('currency', 'USD'),
                        'stock_status': stock_status,
                        'product_url': row.get('product_url', ''),
                        'image_url': row.get('image_url', ''),
                    }
                )
                
                if created:
                    imported += 1
                    self.stdout.write(f"Imported: {product.product_name}")
                else:
                    self.stdout.write(f"Updated: {product.product_name}")
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully imported {imported} products, skipped {skipped} rows'
            )
        )
