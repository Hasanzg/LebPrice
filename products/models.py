from django.db import models
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Product(models.Model):
    STOCK_CHOICES = [
        ('in_stock', 'In Stock'),
        ('out_of_stock', 'Out of Stock'),
    ]
    
    STORE_TYPE_CHOICES = [
        ('tech', 'Technology'),
        ('fashion', 'Fashion'),
        ('grocery', 'Grocery'),
        ('general', 'General'),
        ('electronics', 'Electronics'),
        ('home', 'Home & Garden'),
        ('sports', 'Sports'),
        ('books', 'Books'),
        ('other', 'Other'),
    ]
    
    # Unique identifiers
    product_id = models.CharField(max_length=100, db_index=True)  # Store's product ID
    store_name = models.CharField(max_length=200, db_index=True)  # Store identifier
    store_type = models.CharField(max_length=50, choices=STORE_TYPE_CHOICES, default='general', db_index=True)  # Store category
    sku = models.CharField(max_length=100, blank=True, null=True)
    
    # Product information
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    product_name = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    
    # Pricing - UPDATED WITH TAX FIELDS
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
                               help_text='Original scraped price')
    price_before_tax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                          help_text='Price before tax is applied')
    final_price_after_tax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                                help_text='Final price including tax')
    currency = models.CharField(max_length=10, default='USD')
    
    # Availability
    stock_status = models.CharField(max_length=20, choices=STOCK_CHOICES, default='out_of_stock')
    
    # URLs
    product_url = models.URLField(max_length=1000)
    image_url = models.URLField(max_length=1000, blank=True, null=True)
    
    # Timestamps
    last_scraped = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        # Prevent duplicates: same product_id from same store
        unique_together = [['product_id', 'store_name']]
        ordering = ['-last_scraped']
        indexes = [
            models.Index(fields=['product_id', 'store_name']),
            models.Index(fields=['store_name']),
            models.Index(fields=['last_scraped']),
        ]
    
    def __str__(self):
        return f"{self.product_name} ({self.store_name})"


class PriceHistory(models.Model):
    STOCK_CHOICES = [
        ('in_stock', 'In Stock'),
        ('out_of_stock', 'Out of Stock'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='price_history')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    stock_status = models.CharField(max_length=20, choices=STOCK_CHOICES, default='out_of_stock')
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Price Histories"
        ordering = ['-recorded_at']
    
    def __str__(self):
        return f"{self.product.product_name} - {self.price} {self.currency} at {self.recorded_at}"