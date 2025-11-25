from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CategoryViewSet, product_detail

# Create router for API endpoints
router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')

app_name = 'products'

urlpatterns = [
    path('', include(router.urls)),
    path('detail/<int:pk>/', product_detail, name='product_detail'),
]