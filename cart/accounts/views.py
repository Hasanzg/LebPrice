from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from allauth.socialaccount.models import SocialAccount
from .models import Profile
from .forms import ProfileForm, UsernameUpdateForm, CurrencyUpdateForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import os

# ----------------------------
# API ENDPOINTS FOR SERVICE-TO-SERVICE COMMUNICATION
# ----------------------------

@csrf_exempt
@require_http_methods(["POST"])
def verify_session(request):
    """
    Verify if session is valid - called by backend service
    Returns user info if authenticated
    """
    session_id = request.COOKIES.get('sessionid')
    
    if not session_id:
        return JsonResponse({'valid': False, 'error': 'No session'}, status=401)
    
    if request.user.is_authenticated:
        return JsonResponse({
            'valid': True,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
            }
        })
    
    return JsonResponse({'valid': False, 'error': 'Invalid session'}, status=401)


@csrf_exempt
@require_http_methods(["GET"])
def get_user_info(request):
    """Get current authenticated user info"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    return JsonResponse({
        'id': request.user.id,
        'username': request.user.username,
        'email': request.user.email,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'profile': {
            'currency': profile.currency,
            'phone_number': profile.phone_number,
        }
    })


# ----------------------------
# Account deletion
# ----------------------------
@login_required
def delete_account(request):
    """Delete user account after confirmation"""
    if request.method == 'POST':
        user = request.user
        user.delete()
        messages.success(request, "Your account has been deleted.")
        return redirect('account_logout')
    return render(request, 'account/delete_account.html')


# ----------------------------
# Home - SIMPLIFIED (no products here, products in backend service)
# ----------------------------
@login_required
def home(request):
    """Home page - fetches products from backend service"""
    import requests
    
    backend_url = os.environ.get("BACKEND_SERVICE_URL", "http://localhost:8000")
    session_cookie = request.COOKIES.get('sessionid')
    
    # Get parameters
    search_query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    page = request.GET.get('page', 1)
    
    try:
        # Build params dict - send category separately
        params = {
            'page': page,
            'ordering': request.GET.get('ordering', ''),
            'min_price': request.GET.get('min_price', ''),
            'max_price': request.GET.get('max_price', ''),
        }
        
        # Add search query if present
        if search_query:
            params['q'] = search_query
        
        # Add category if present
        if category:
            params['category'] = category
        
        # Remove empty params
        params = {k: v for k, v in params.items() if v}
        
        response = requests.get(
            f'{backend_url}/products/api/list/',
            cookies={'sessionid': session_cookie},
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            products_list = data.get('products', [])
            total_pages = data.get('total_pages', 1)
            current_page = data.get('page', 1)
            
            page_obj = {
                'number': current_page,
                'has_previous': current_page > 1,
                'has_next': current_page < total_pages,
                'previous_page_number': current_page - 1 if current_page > 1 else 1,
                'next_page_number': current_page + 1 if current_page < total_pages else total_pages,
                'num_pages': total_pages,
                'paginator': {'num_pages': total_pages}
            }
            
            qdict = request.GET.copy()
            qdict.pop('page', None)
            querystring = qdict.urlencode()
            
            context = {
                'products': products_list,
                'page_obj': page_obj,
                'categories': data.get('categories', []),
                'search': search_query,
                'ordering': request.GET.get('ordering', ''),
                'min_price': request.GET.get('min_price', ''),
                'max_price': request.GET.get('max_price', ''),
                'querystring': querystring,
            }
            return render(request, 'account/home.html', context)
        else:
            messages.error(request, f'Unable to load products')
            return render(request, 'account/home.html', {'products': [], 'categories': []})
            
    except requests.RequestException as e:
        messages.error(request, 'Backend service unavailable')
        return render(request, 'account/home.html', {'products': [], 'categories': []})
# ----------------------------
# Root redirect
# ----------------------------
def root_view(request):
    """Redirect to home if authenticated, otherwise to login"""
    if request.user.is_authenticated:
        return redirect('home')
    return redirect('account_login')  # Use allauth's login


# ----------------------------
# Profile
# ----------------------------
@login_required
def profile(request):
    """User profile view with first/last name and profile updates"""
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            request.user.first_name = form.cleaned_data.get('first_name', '')
            request.user.last_name = form.cleaned_data.get('last_name', '')
            request.user.save()
            profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileForm(
            instance=profile,
            initial={
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
            }
        )

    context = {
        'form': form,
        'profile': profile
    }
    
    return render(request, 'account/profile.html', context)


# ----------------------------
# Settings
# ----------------------------
@login_required
def settings(request):
    """Settings page for username, currency, and account management"""
    user = request.user
    social_accounts = SocialAccount.objects.filter(user=user)
    is_google_user = social_accounts.filter(provider='google').exists()
    profile, created = Profile.objects.get_or_create(user=user)

    if request.method == 'POST':
        if 'update_username' in request.POST:
            username_form = UsernameUpdateForm(request.POST, instance=user, user=user)
            if username_form.is_valid():
                username_form.save()
                messages.success(request, 'Username updated successfully!')
                return redirect('settings')
            else:
                currency_form = CurrencyUpdateForm(instance=profile)

        elif 'update_currency' in request.POST:
            currency_form = CurrencyUpdateForm(request.POST, instance=profile)
            if currency_form.is_valid():
                currency_form.save()
                messages.success(request, 'Currency preference updated successfully!')
                return redirect('settings')
            else:
                username_form = UsernameUpdateForm(instance=user, user=user)

        elif 'delete_account' in request.POST:
            return redirect('delete_account')

        else:
            username_form = UsernameUpdateForm(instance=user, user=user)
            currency_form = CurrencyUpdateForm(instance=profile)
    else:
        username_form = UsernameUpdateForm(instance=user, user=user)
        currency_form = CurrencyUpdateForm(instance=profile)

    context = {
        'username_form': username_form,
        'currency_form': currency_form,
        'is_google_user': is_google_user,
        'user': user,
    }

    return render(request, 'account/settings.html', context)