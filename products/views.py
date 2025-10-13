from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product, Category, PriceHistory
from .serializers import ProductSerializer, CategorySerializer, PriceHistorySerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for categories
    GET /api/categories/ - List all categories
    GET /api/categories/{id}/ - Get single category
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'slug']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for products
    GET /api/products/ - List all products
    GET /api/products/{id}/ - Get single product
    GET /api/products/search/?q=keyword - Search products
    GET /api/products/?category=cpu - Filter by category
    GET /api/products/?store_name=PC and Parts - Filter by store
    """
    queryset = Product.objects.select_related('category').all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filter fields
    filterset_fields = {
        'category__name': ['exact', 'icontains'],
        'store_name': ['exact', 'icontains'],
        'stock_status': ['exact'],
        'price': ['gte', 'lte', 'exact'],
    }
    
    # Search fields
    search_fields = ['product_name', 'description', 'sku', 'product_id']
    
    # Ordering fields
    ordering_fields = ['price', 'product_name', 'last_scraped', 'created_at']
    ordering = ['-last_scraped']
    
    @action(detail=True, methods=['get'])
    def price_history(self, request, pk=None):
        """
        Get price history for a specific product
        GET /api/products/{id}/price_history/
        """
        product = self.get_object()
        history = product.price_history.all()
        serializer = PriceHistorySerializer(history, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """
        Get products grouped by category
        GET /api/products/by_category/
        """
        categories = Category.objects.all()
        result = []
        
        for category in categories:
            products = Product.objects.filter(category=category)
            if products.exists():
                result.append({
                    'category': category.name,
                    'count': products.count(),
                    'products': ProductSerializer(products[:10], many=True).data
                })
        
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def in_stock(self, request):
        """
        Get only in-stock products
        GET /api/products/in_stock/
        """
        products = self.queryset.filter(stock_status='in_stock')
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """
        Get latest scraped products
        GET /api/products/latest/
        """
        products = self.queryset.order_by('-last_scraped')[:50]
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)