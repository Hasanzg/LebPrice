from django.urls import path
from .views import delete_account, home, root_view, profile, settings
from . import views

urlpatterns = [
    path("delete/", delete_account, name="delete_account"),
    path("home/", home, name="home"),
    path("", root_view, name="root"),
    path("profile/", profile, name="profile"),
    path("settings/", settings, name="settings"),    
    path('cart/', views.view_cart, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path("clear-cart/", views.clear_cart, name="clear_cart"),
]