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
from datetime import datetime
from dateutil.relativedelta import relativedelta

from datetime import datetime, timedelta  # Для точной работы с датами




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
    today = datetime.now().date()
    expired_subs = UserSubscription.objects.filter(user=request.user, is_active=True, next_billing_date__lt=today)
    for sub in expired_subs:
        # Крутим дату вперед до тех пор, пока она не станет больше или равна сегодняшней
        # (это спасет, если пользователь не заходил в сервис несколько месяцев)
        while sub.next_billing_date < today:
            if sub.billing_period == 'monthly':
                sub.next_billing_date += relativedelta(months=1)
            elif sub.billing_period == 'yearly':
                sub.next_billing_date += relativedelta(years=1)
        sub.save()  # Сохраняем обновленную дату в базу данных
    # === КОНЕЦ БЛОКА АВТОПРОДЛЕНИЯ ДАТ ===

    user_subs = UserSubscription.objects.filter(user=request.user, is_active=True)
    
    # --- 1. Базовая агрегация расходов ---
    total_monthly = 0
    total_yearly_forecast = 0
    for sub in user_subs:
        if sub.billing_period == 'monthly':
            total_monthly += sub.price
            total_yearly_forecast += sub.price * 12
        elif sub.billing_period == 'yearly':
            total_monthly += sub.price / 12
            total_yearly_forecast += sub.price

    # --- 2. Логика оптимизации расходов (Дубликаты) ---
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

    # --- 3. НОВАЯ ФИЧА: Микро-расчет трат на ближайший срок ---
    # Получаем срок из GET-запроса (по умолчанию 3 дня)
    days_limit = int(request.GET.get('days', 3))
    today = datetime.now().date()
    target_date = today + timedelta(days=days_limit)
    
    upcoming_total = 0
    upcoming_by_categories = {}
    
    # Фильтруем подписки, списание по которым будет в этот промежуток
    upcoming_subs = user_subs.filter(next_billing_date__gte=today, next_billing_date__lte=target_date)
    
    for sub in upcoming_subs:
        cat_name = sub.service.category.name if sub.service else "Кастомные"
        price_float = float(sub.price)
        upcoming_total += price_float
        upcoming_by_categories[cat_name] = upcoming_by_categories.get(cat_name, 0) + price_float

    # --- 4. Визуализация: Круговая диаграмма (Matplotlib) ---
    chart_data = ""
    if user_subs.exists():
        category_costs = {}
        for sub in user_subs:
            cat_name = sub.service.category.name if sub.service else "Кастомные"
            cost = sub.price if sub.billing_period == 'monthly' else sub.price / 12
            category_costs[cat_name] = category_costs.get(cat_name, 0) + float(cost)

        plt.figure(figsize=(5, 5))
        plt.pie(category_costs.values(), labels=category_costs.keys(), autopct='%1.1f%%', startangle=140)
        plt.title("Распределение общих расходов")
        
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
        # Данные для новой фичи:
        'upcoming_total': round(upcoming_total, 2),
        'upcoming_by_categories': upcoming_by_categories,
        'days_limit': days_limit,
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
@login_required
def edit_subscription(request, sub_id):
    # Находим подписку текущего пользователя
    subscription = get_object_or_404(UserSubscription, id=sub_id, user=request.user)

    if request.method == 'POST':
        form = UserSubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = UserSubscriptionForm(instance=subscription)

    return render(request, 'subscriptions/edit_subscription.html', {'form': form, 'subscription': subscription})