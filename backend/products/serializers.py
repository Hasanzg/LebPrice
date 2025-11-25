from rest_framework import serializers
from .models import Product, Category, PriceHistory


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'product_count', 'created_at']
    
    def get_product_count(self, obj):
        return obj.products.count()


class PriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceHistory
        fields = ['id', 'price', 'currency', 'stock_status', 'recorded_at']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    price_history_count = serializers.SerializerMethodField()
    store_type_display = serializers.CharField(source='get_store_type_display', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id',
            'product_id',
            'store_name',
            'store_type',
            'store_type_display',
            'sku',
            'category',
            'category_name',
            'category_slug',
            'product_name',
            'description',
            'price',
            'price_before_tax',
            'final_price_after_tax',
            'currency',
            'stock_status',
            'product_url',
            'image_url',
            'last_scraped',
            'created_at',
            'updated_at',
            'price_history_count',
        ]
    
    def get_price_history_count(self, obj):
        return obj.price_history.count()


class ProductDetailSerializer(ProductSerializer):
    """Extended serializer with price history"""
    price_history = PriceHistorySerializer(many=True, read_only=True)
    
    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ['price_history']