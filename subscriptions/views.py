from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .models import UserSubscription
from .forms import UserSubscriptionForm

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  
            return redirect('/')  
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard(request):
    # Показываем подписки ТОЛЬКО текущего авторизованного пользователя
    subscriptions = UserSubscription.objects.filter(user=request.user)
    return render(request, 'subscriptions/dashboard.html', {'subscriptions': subscriptions})

@login_required
def add_subscription(request):
    if request.method == 'POST':
        form = UserSubscriptionForm(request.POST)
        if form.is_valid():
            subscription = form.save(commit=False)
            subscription.user = request.user 
            subscription.save()
            return redirect('dashboard')
    else:
        form = UserCreationForm()  
        form = UserSubscriptionForm()
    return render(request, 'subscriptions/add_subscription.html', {'form': form})

