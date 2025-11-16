from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product, Category, PriceHistory
from .serializers import ProductSerializer, ProductDetailSerializer, CategorySerializer, PriceHistorySerializer
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.db.models import Avg, Min, Max, Count, Q

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

@method_decorator(cache_page(60 * 15), name='list')  # Cache list view for 15 minutes
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for products
    GET /api/products/ - List all products
    GET /api/products/{id}/ - Get single product with details
    GET /api/products/search/?q=keyword - Search products
    GET /api/products/?category=cpu - Filter by category
    GET /api/products/?store_name=PC and Parts - Filter by store
    GET /api/products/?price__gte=100&price__lte=500 - Price range filter
    """
    queryset = Product.objects.select_related('category').all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filter fields
    filterset_fields = {
        'category__name': ['exact', 'icontains'],
        'store_name': ['exact', 'icontains'],
        'store_type': ['exact'],
        'stock_status': ['exact'],
        'price': ['gte', 'lte', 'exact'],
        'price_before_tax': ['gte', 'lte', 'exact'],
        'final_price_after_tax': ['gte', 'lte', 'exact'],
    }
    
    # Search fields
    search_fields = ['product_name', 'description', 'sku', 'product_id']
    
    # Ordering fields
    ordering_fields = ['price', 'price_before_tax', 'final_price_after_tax', 
                      'product_name', 'last_scraped', 'created_at']
    ordering = ['-last_scraped']
    
    def get_serializer_class(self):
        """Use detailed serializer for single product view"""
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductSerializer
    
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
                    'category_slug': category.slug,
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
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def out_of_stock(self, request):
        """
        Get out-of-stock products
        GET /api/products/out_of_stock/
        """
        products = self.queryset.filter(stock_status='out_of_stock')
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
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
    
    @action(detail=False, methods=['get'])
    def by_store(self, request):
        """
        Get products grouped by store
        GET /api/products/by_store/
        """
        stores = Product.objects.values_list('store_name', flat=True).distinct()
        result = []
        
        for store in stores:
            products = Product.objects.filter(store_name=store)
            result.append({
                'store_name': store,
                'total_products': products.count(),
                'in_stock': products.filter(stock_status='in_stock').count(),
                'out_of_stock': products.filter(stock_status='out_of_stock').count(),
                'categories': products.values_list('category__name', flat=True).distinct().count(),
            })
        
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def price_range(self, request):
        """
        Get products within a price range
        GET /api/products/price_range/?min=100&max=500
        GET /api/products/price_range/?min=100&max=500&use_final=true
        """
        min_price = request.query_params.get('min', 0)
        max_price = request.query_params.get('max', 999999)
        use_final = request.query_params.get('use_final', 'false').lower() == 'true'
        
        try:
            min_price = float(min_price)
            max_price = float(max_price)
        except ValueError:
            return Response({'error': 'Invalid price values'}, status=400)
        
        if use_final:
            # Filter by final price after tax
            products = self.queryset.filter(
                final_price_after_tax__gte=min_price,
                final_price_after_tax__lte=max_price
            )
        else:
            # Filter by regular price
            products = self.queryset.filter(
                price__gte=min_price,
                price__lte=max_price
            )
        
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def autocomplete(self, request):
        """
        Autocomplete suggestions for search
        GET /api/products/autocomplete/?q=rtx
        """
        query = request.query_params.get('q', '')
        if len(query) < 2:
            return Response([])
        
        suggestions = Product.objects.filter(
            product_name__icontains=query
        ).values_list('product_name', flat=True).distinct()[:10]
        
        return Response(list(suggestions))
    
    @action(detail=False, methods=['get'])
    def compare(self, request):
        """
        Compare products across stores
        GET /api/products/compare/?ids=1,2,3
        """
        product_ids = request.query_params.get('ids', '').split(',')
        if not product_ids:
            return Response({'error': 'No product IDs provided'}, status=400)
        
        try:
            product_ids = [int(pid) for pid in product_ids if pid.strip()]
        except ValueError:
            return Response({'error': 'Invalid product IDs'}, status=400)
        
        products = Product.objects.filter(id__in=product_ids)
        
        if not products.exists():
            return Response({'error': 'No products found'}, status=404)
        
        comparison = {
            'products': ProductSerializer(products, many=True).data,
            'stats': {
                'count': products.count(),
                'lowest_price': products.aggregate(Min('final_price_after_tax'))['final_price_after_tax__min'],
                'highest_price': products.aggregate(Max('final_price_after_tax'))['final_price_after_tax__max'],
                'average_price': products.aggregate(Avg('final_price_after_tax'))['final_price_after_tax__avg'],
            }
        }
        
        return Response(comparison)
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """
        Get trending products (most price changes recently)
        GET /api/products/trending/
        """
        from django.db.models import Count
        
        # Products with most price history entries in last 30 days
        from django.utils import timezone
        from datetime import timedelta
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        trending = Product.objects.annotate(
           price_changes=Count('price_history', filter=Q(price_history__recorded_at__gte=thirty_days_ago))
        ).filter(price_changes__gt=0).order_by('-price_changes')[:20]
        
        serializer = self.get_serializer(trending, many=True)
        return Response(serializer.data)