from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from accounts import views
urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),
    
    # Authentication via allauth
    path('accounts/', include('allauth.urls')),
    
    # Custom login page (if you have a custom template)
    path('login/', TemplateView.as_view(template_name="mylogin.html"), name="mylogin"),
    
    # Root and accounts views (homepage, delete account, etc.)
    path('', include('accounts.urls')),
    
    # API endpoints under /api/
    path('api/', include('products.urls')),
    # ... other patterns
    path('account/delete/', views.delete_account, name='account_delete'),
    # Website Icon
    path('favicon.ico', RedirectView.as_view(url='/static/images/logo2.ico', permanent=True)),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)