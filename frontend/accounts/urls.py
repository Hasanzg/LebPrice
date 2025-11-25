from django.urls import path
from .views import (
    delete_account, home, root_view, profile, settings,
    verify_session, get_user_info
)

urlpatterns = [
    # Regular user-facing pages
    path("delete/", delete_account, name="delete_account"),
    path("home/", home, name="home"),
    path("", root_view, name="root"),
    path("profile/", profile, name="profile"),
    path("settings/", settings, name="settings"),
    
    # REMOVED all cart URLs
    
    # API endpoints for backend service
    path("api/verify/", verify_session, name="verify_session"),
    path("api/me/", get_user_info, name="get_user_info"),
]