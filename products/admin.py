from django.contrib import admin
from django.utils.html import format_html
from .models import Product, Category, PriceHistory


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'product_count', 'created_at']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'product_name', 
        'category', 
        'formatted_price', 
        'stock_status',
        'last_scraped'
    ]
    list_filter = [
        'category', 
        'stock_status', 
        'currency',
        'created_at',
        'last_scraped'
    ]
    search_fields = [
        'product_name', 
        'description', 
        'sku', 
        'product_id'
    ]
    readonly_fields = [
        'product_id',
        'created_at', 
        'updated_at', 
        'last_scraped'
    ]
    
    def formatted_price(self, obj):
        if obj.price:
            return f"{obj.currency} {obj.price:,.2f}"
        return "-"
    formatted_price.short_description = 'Price'


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'product', 
        'price', 
        'stock_status',
        'recorded_at'
    ]
    list_filter = ['stock_status', 'currency', 'recorded_at']
    search_fields = ['product__product_name']
    readonly_fields = ['product', 'price', 'currency', 'stock_status', 'recorded_at']