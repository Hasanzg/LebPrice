from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from products.models import Product, Category
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from allauth.socialaccount.models import SocialAccount
from .models import Profile
from .forms import ProfileForm
from .forms import UsernameUpdateForm, CurrencyUpdateForm

@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        user.delete()
        messages.success(request, "Your account has been deleted.")
        return redirect('account_logout')
    return render(request, 'account/delete_account.html')

@login_required
def home(request):
    """Home page view with product list and pagination"""
    products_list = Product.objects.select_related('category').all()
    categories = Category.objects.all()
    
    # Pagination - 32 products per page
    paginator = Paginator(products_list, 32)
    page = request.GET.get('page', 1)
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'account/home.html', context)

def root_view(request):
    if request.user.is_authenticated:
        return redirect('home/')
    return redirect('login/')


@login_required
def profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)

            # Update User model
            request.user.first_name = form.cleaned_data.get('first_name', '')
            request.user.last_name = form.cleaned_data.get('last_name', '')
            request.user.save()

            profile.save()
            return redirect('profile')
    else:
        # Populate initial values for first/last name
        form = ProfileForm(
            instance=profile,
            initial={
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
            }
        )

    context = {'form': form, 'profile': profile}
    return render(request, 'account/profile.html', context)


@login_required
def cart(request):
    return render(request, 'account/cart.html')


@login_required
def settings(request):
    user = request.user
    
    # Check if user signed up with Google
    social_accounts = SocialAccount.objects.filter(user=user)
    is_google_user = social_accounts.filter(provider='google').exists()
    
    # Debug: Print to console to check
    print(f"User: {user.username}")
    print(f"User Email: {user.email}")
    print(f"Is Google User: {is_google_user}")
    print(f"Social Accounts: {social_accounts}")
    
    # Ensure profile exists
    profile, created = Profile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        # Handle username update
        if 'update_username' in request.POST:
            username_form = UsernameUpdateForm(request.POST, instance=user, user=user)
            if username_form.is_valid():
                username_form.save()
                messages.success(request, 'Username updated successfully!')
                return redirect('settings')
            else:
                currency_form = CurrencyUpdateForm(instance=profile)
        
        # Handle currency update
        elif 'update_currency' in request.POST:
            currency_form = CurrencyUpdateForm(request.POST, instance=profile)
            if currency_form.is_valid():
                currency_form.save()
                messages.success(request, 'Currency preference updated successfully!')
                return redirect('settings')
            else:
                username_form = UsernameUpdateForm(instance=user, user=user)
        
        # Handle account deletion
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