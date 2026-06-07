import io
import base64
import matplotlib
matplotlib.use('Agg')  # Отключает всплывающие GUI-окна на бэкенде
import matplotlib.pyplot as plt

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

from .models import UserSubscription
from .forms import UserSubscriptionForm

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard(request):
    user_subs = UserSubscription.objects.filter(user=request.user, is_active=True)
    
    total_monthly = 0
    total_yearly_forecast = 0
    
    for sub in user_subs:
        if sub.billing_period == 'monthly':
            total_monthly += sub.price
            total_yearly_forecast += sub.price * 12
        elif sub.billing_period == 'yearly':
            total_monthly += sub.price / 12
            total_yearly_forecast += sub.price

    optimization_alerts = []
    categories_seen = {}
    
    for sub in user_subs:
        if sub.service:
            cat_name = sub.service.category.name
            if cat_name in categories_seen:
                categories_seen[cat_name].append(sub.service.name)
            else:
                categories_seen[cat_name] = [sub.service.name]
                
    for cat_name, services in categories_seen.items():
        if len(services) > 1:
            services_str = ", ".join(services)
            optimization_alerts.append(
                f"Внимание: В категории '{cat_name}' у вас несколько активных сервисов ({services_str}). "
                f"Рекомендуем отключить лишние для оптимизации бюджета."
            )

    chart_data = ""
    if user_subs.exists():
        category_costs = {}
        for sub in user_subs:
            cat_name = sub.service.category.name if sub.service else "Кастомные"
            cost = sub.price if sub.billing_period == 'monthly' else sub.price / 12
            category_costs[cat_name] = category_costs.get(cat_name, 0) + float(cost)

        plt.figure(figsize=(5, 5))
        plt.pie(category_costs.values(), labels=category_costs.keys(), autopct='%1.1f%%', startangle=140)
        plt.title("Распределение расходов по категориям")
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        string = base64.b64encode(buf.read())
        chart_data = string.decode('utf-8')
        plt.close()

    all_subscriptions = UserSubscription.objects.filter(user=request.user)

    context = {
        'subscriptions': all_subscriptions,
        'total_monthly': round(total_monthly, 2),
        'total_yearly_forecast': round(total_yearly_forecast, 2),
        'optimization_alerts': optimization_alerts,
        'chart_data': chart_data,
    }
    return render(request, 'subscriptions/dashboard.html', context)

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
        form = UserSubscriptionForm()
    return render(request, 'subscriptions/add_subscription.html', {'form': form})

@login_required
def delete_subscription(request, sub_id):
    # Метод удаления подписки с жесткой привязкой к владельцу
    subscription = get_object_or_404(UserSubscription, id=sub_id, user=request.user)
    if request.method == 'POST':
        subscription.delete()
        return redirect('dashboard')
    return render(request, 'subscriptions/delete_confirm.html', {'subscription': subscription})
