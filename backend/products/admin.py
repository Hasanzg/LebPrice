from django.contrib import admin
from .models import Category, Product, PriceHistory


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'product_count', 'created_at']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'product_name', 
        'store_name',
        'store_type',
        'category',
        'price',
        'price_before_tax',
        'final_price_after_tax',
        'stock_status',
        'last_scraped'
    ]
    list_filter = ['store_name', 'store_type', 'category', 'stock_status', 'last_scraped']
    search_fields = ['product_name', 'product_id', 'sku', 'description']
    readonly_fields = ['created_at', 'updated_at', 'last_scraped']
    
    fieldsets = (
        ('Identification', {
            'fields': ('product_id', 'store_name', 'store_type', 'sku')
        }),
        ('Product Information', {
            'fields': ('product_name', 'category', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'price_before_tax', 'final_price_after_tax', 'currency'),
            'description': 'Price: original scraped price | Before Tax: base price | After Tax: final price with tax'
        }),
        ('Availability', {
            'fields': ('stock_status',)
        }),
        ('URLs', {
            'fields': ('product_url', 'image_url')
        }),
        ('Timestamps', {
            'fields': ('last_scraped', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ['product', 'price', 'currency', 'stock_status', 'recorded_at']
    list_filter = ['stock_status', 'currency', 'recorded_at']
    search_fields = ['product__product_name', 'product__product_id']
    readonly_fields = ['recorded_at']
    date_hierarchy = 'recorded_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')