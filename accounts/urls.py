from django.urls import path
from .views import delete_account, home, root_view

urlpatterns = [
    path("delete/", delete_account, name="account_delete"),
    path("home/", home, name="home"),
    path("", root_view, name="root"),  
]