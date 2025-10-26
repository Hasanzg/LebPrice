from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from products.models import Product, Category
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from decimal import Decimal
from django.db.models import Q, F, Value, DecimalField
from django.db.models.functions import Lower, Coalesce

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
    """Home page with search, price filter, robust sorting, and pagination."""
    q = request.GET.get('search') or request.GET.get('q') or ''
    ordering_param = request.GET.get('ordering') or request.GET.get('sort') or ''
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    qs = Product.objects.select_related('category').all()

    # text search across common fields
    if q:
        qs = qs.filter(
            Q(product_name__icontains=q) |
            Q(description__icontains=q) |
            Q(sku__icontains=q) |
            Q(product_id__icontains=q) |
            Q(store_name__icontains=q) |
            Q(category__name__icontains=q)
        )

    # numeric price filters
    if min_price:
        qs = qs.filter(price__gte=min_price)
    if max_price:
        qs = qs.filter(price__lte=max_price)

    # sorting
    if ordering_param in ('price', '-price'):
        # Prefer NULLS LAST if supported (Django >=3.1 + Postgres)
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
        # default newest first
        qs = qs.order_by('-last_scraped')

    categories = Category.objects.all()

    # pagination
    paginator = Paginator(qs, 32)
    page = request.GET.get('page', 1)
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    # keep filters/sort when moving between pages
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

def root_view(request):
    if request.user.is_authenticated:
        return redirect('home/')
    return redirect('login/')