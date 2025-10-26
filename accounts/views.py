from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from products.models import Product, Category
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

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