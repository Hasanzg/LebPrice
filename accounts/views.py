from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, F, Value, DecimalField
from django.db.models.functions import Lower, Coalesce
from django.shortcuts import render, redirect

from allauth.socialaccount.models import SocialAccount

from products.models import Product, Category

from .models import Profile
from .forms import ProfileForm, UsernameUpdateForm, CurrencyUpdateForm


# ----------------------------
# Account deletion
# ----------------------------
@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        user.delete()
        messages.success(request, "Your account has been deleted.")
        return redirect('account_logout')
    return render(request, 'account/delete_account.html')


# ----------------------------
# Home (with search, filters, robust sorting, pagination)
# ----------------------------
@login_required
def home(request):
    """Home page with search, price filter, robust sorting, and pagination."""
    q = request.GET.get('search') or request.GET.get('q') or ''
    ordering_param = request.GET.get('ordering') or request.GET.get('sort') or ''
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    qs = Product.objects.select_related('category').all()

    # Text search across common fields
    if q:
        qs = qs.filter(
            Q(product_name__icontains=q) |
            Q(description__icontains=q) |
            Q(sku__icontains=q) |
            Q(product_id__icontains=q) |
            Q(store_name__icontains=q) |
            Q(category__name__icontains=q)
        )

    # Numeric price filters
    if min_price:
        qs = qs.filter(price__gte=min_price)
    if max_price:
        qs = qs.filter(price__lte=max_price)

    # Sorting
    if ordering_param in ('price', '-price'):
        # Prefer NULLS LAST if supported (Postgres)
        try:
            qs = qs.order_by(
                F('price').asc(nulls_last=True) if ordering_param == 'price'
                else F('price').desc(nulls_last=True)
            )
        except TypeError:
            # Fallback (e.g., SQLite): coalesce NULLs to a sentinel so they go last/first
            sentinel = Decimal('9999999999.99') if ordering_param == 'price' else Decimal('-1')
            qs = qs.annotate(
                price_for_sort=Coalesce('price', Value(sentinel), output_field=DecimalField())
            ).order_by('price_for_sort' if ordering_param == 'price' else '-price_for_sort')

    elif ordering_param in ('name', '-name'):
        # Case-insensitive alphabetical order on product_name
        qs = qs.order_by(
            Lower('product_name').asc() if ordering_param == 'name'
            else Lower('product_name').desc()
        )
    else:
        # Default newest first
        qs = qs.order_by('-last_scraped')

    categories = Category.objects.all()

    # Pagination
    paginator = Paginator(qs, 32)
    page = request.GET.get('page', 1)
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    # Keep filters/sort when moving between pages
    qdict = request.GET.copy()
    qdict.pop('page', None)
    base_qs = qdict.urlencode()

    return render(request, 'account/home.html', {
        'products': products,
        'categories': categories,
        'search': q,
        'ordering': ordering_param,
        'min_price': min_price or '',
        'max_price': max_price or '',
        'base_qs': base_qs,
    })


# ----------------------------
# Root redirect
# ----------------------------
def root_view(request):
    if request.user.is_authenticated:
        return redirect('home/')
    return redirect('login/')


# ----------------------------
# Profile
# ----------------------------
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


# ----------------------------
# Cart
# ----------------------------
@login_required
def cart(request):
    return render(request, 'account/cart.html')


# ----------------------------
# Settings (username & currency updates, Google link indicator)
# ----------------------------
@login_required
def settings(request):
    user = request.user

    # Check if user signed up with Google
    social_accounts = SocialAccount.objects.filter(user=user)
    is_google_user = social_accounts.filter(provider='google').exists()

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
