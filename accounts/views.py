from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from products.models import Product, Category
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

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
    """Home page view with product list, search, price filter, and sorting"""

    # read query params
    q = request.GET.get('search') or request.GET.get('q') or ''
    ordering_param = request.GET.get('ordering') or request.GET.get('sort') or ''
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    qs = Product.objects.select_related('category').all()

    # text search
    if q:
        qs = qs.filter(
            Q(product_name__icontains=q) |
            Q(description__icontains=q) |
            Q(sku__icontains=q) |
            Q(product_id__icontains=q) |
            Q(store_name__icontains=q) |
            Q(category__name__icontains=q)
        )

    # numeric filters
    if min_price:
        qs = qs.filter(price__gte=min_price)
    if max_price:
        qs = qs.filter(price__lte=max_price)

    # sort map: UI → model field
    ordering_map = {
        'name': 'product_name',
        '-name': '-product_name',
        'price': 'price',
        '-price': '-price',
    }
    order_by = ordering_map.get(ordering_param)
    qs = qs.order_by(order_by) if order_by else qs.order_by('-last_scraped')

    categories = Category.objects.all()

    # paginate
    paginator = Paginator(qs, 32)
    page = request.GET.get('page', 1)
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    return render(request, 'account/home.html', {
        'products': products,
        'categories': categories,
        'search': q,
        'ordering': ordering_param,
        'min_price': min_price or '',
        'max_price': max_price or '',
    })

def root_view(request):
    if request.user.is_authenticated:
        return redirect('home/')
    return redirect('login/')