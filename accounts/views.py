from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

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
    return render(request, 'account/home.html')

def root_view(request):
    if request.user.is_authenticated:
        return redirect('home/')
    return redirect('login/')