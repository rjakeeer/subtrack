import os
from django.conf import settings
import io
import base64
import matplotlib
matplotlib.use('Agg')  # Отключает всплывающие GUI-окна на бэкенде
import matplotlib.pyplot as plt
from .models import SubscriptionService, Category
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .forms import BaseSubscriptionForm, CustomSubscriptionForm
from .models import UserSubscription
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.db.models import Q
from datetime import datetime, timedelta  # Для точной работы с датами
from django.db.models.functions import Lower
from django.db.models import Sum



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


def dashboard(request):
    # === ЕСЛИ ПОЛЬЗОВАТЕЛЬ НЕ АВТОРИЗОВАН (ГОСТЬ) ===
    if not request.user.is_authenticated:
        tz_content = ""
        readme_content = ""
        
        tz_path = os.path.join(settings.BASE_DIR, 'TZ.md')
        readme_path = os.path.join(settings.BASE_DIR, 'README.md')
        
        # Читаем файл ТЗ
        if os.path.exists(tz_path):
            with open(tz_path, 'r', encoding='utf-8') as f:
                tz_content = f.read()
                
        # Читаем файл README
        if os.path.exists(readme_path):
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.read()
                
        context = {
            'tz_content': tz_content,
            'readme_content': readme_content
        }
        return render(request, 'subscriptions/welcome.html', context)

    #==============================================================
    
    today = datetime.now().date()
    # === БЛОК АВТОПРОДЛЕНИЯ ДАТ ===
    expired_subs = UserSubscription.objects.filter(user=request.user, is_active=True, next_billing_date__lt=today)
    for sub in expired_subs:
        while sub.next_billing_date < today:
            if sub.billing_period == 'monthly':
                sub.next_billing_date += relativedelta(months=1)
            elif sub.billing_period == 'yearly':
                sub.next_billing_date += relativedelta(years=1)
        sub.save()

    user_subs = UserSubscription.objects.filter(user=request.user, is_active=True)
    
    # Расчет общих сумм трат
    # База данных сама фильтрует подписки и мгновенно суммирует их стоимость
    monthly_sum = UserSubscription.objects.filter(
        user=request.user, is_active=True, billing_period='monthly'
    ).aggregate(total=Sum('price'))['total'] or 0

    yearly_sum = UserSubscription.objects.filter(
        user=request.user, is_active=True, billing_period='yearly'
    ).aggregate(total=Sum('price'))['total'] or 0

    # Финальный расчет средних затрат для передачи в шаблон (контекст не меняется!)
    total_monthly = float(monthly_sum) + (float(yearly_sum) / 12)
    total_yearly_forecast = (float(monthly_sum) * 12) + float(yearly_sum)


        # === ЛОГИКА ОПТИМИЗАЦИИ РАСХОДОВ (АЛЕРТЫ) ===
    optimization_alerts = []
    categories_seen = {}
    services_counts = {}
    
    for sub in user_subs:
        # Умное определение категории для алертов
        if sub.service:
            cat_name = sub.service.category.name
            display_name = sub.service.name
        elif sub.category:
            cat_name = sub.category.name
            display_name = sub.custom_name
        else:
            continue  # Пропускаем, если категории совсем нет
            
        # 1. Собираем ВСЕ названия сервисов внутри этой категории
        if cat_name in categories_seen:
            if display_name not in categories_seen[cat_name]:
                categories_seen[cat_name].append(display_name)
        else:
            categories_seen[cat_name] = [display_name]
            
        # 2. Считаем точные дубликаты по имени
        services_counts[display_name] = services_counts.get(display_name, 0) + 1

    # Формируем алерты по категориям (теперь сюда попадут и кастомные)
    for cat_name, services in categories_seen.items():
        if len(services) > 1 and not request.session.get(f'dismiss_cat_{cat_name}'):
            services_str = ", ".join(services)
            optimization_alerts.append({
                'id': f'cat_{cat_name}',
                'text': f"В категории '{cat_name}' у вас несколько активных сервисов ({services_str}). Рекомендуем отключить лишние для оптимизации бюджета."
            })

    # Формируем алерты по точным дубликатам имен
    for service_name, count in services_counts.items():
        if count > 1 and not request.session.get(f'dismiss_sub_{service_name}'):
            optimization_alerts.append({
                'id': f'sub_{service_name}',
                'text': f"Обнаружен дубликат: Сервис '{service_name}' добавлен вами {count} раз(а). Проверьте ваши подписки!"
            })
     # === ИНСТРУМЕНТ 1: БЛИЖАЙШИЕ СПИСАНИЯ (Учитываем множественные списания) ===
    days_limit = int(request.GET.get('days', 3))
    target_date = today + relativedelta(days=days_limit)
    upcoming_total = 0
    upcoming_by_categories = {}
    
    for sub in user_subs:
        # Запускаем виртуальный счетчик даты списания
        current_billing_date = sub.next_billing_date
        sub_total_price = 0
        
        # Пока виртуальная дата списания находится внутри выбранного периода
        while today <= current_billing_date <= target_date:
            sub_total_price += float(sub.price)
            # Сдвигаем дату на следующий цикл для проверки
            if sub.billing_period == 'monthly':
                current_billing_date += relativedelta(months=1)
            elif sub.billing_period == 'yearly':
                current_billing_date += relativedelta(years=1)
                
        # Если подписка спишется хотя бы раз в этом периоде
        if sub_total_price > 0:
            if sub.service:
                cat_name = sub.service.category.name
                display_name = sub.service.name
            elif sub.category:
                cat_name = sub.category.name
                display_name = sub.custom_name
            else:
                cat_name = "Кастомные"
                display_name = sub.custom_name or "Без названия"
                
            upcoming_total += sub_total_price
            
            if cat_name not in upcoming_by_categories:
                upcoming_by_categories[cat_name] = {'total': 0.0, 'services': []}
            upcoming_by_categories[cat_name]['total'] += sub_total_price
            if display_name not in upcoming_by_categories[cat_name]['services']:
                upcoming_by_categories[cat_name]['services'].append(display_name)

    # === ИНСТРУМЕНТ 2: КАСТОМНЫЙ ПРОГНОЗ (Учитываем множественные списания) ===
    forecast_days = int(request.GET.get('forecast_days', 30))
    forecast_target_date = today + relativedelta(days=forecast_days)
    forecast_total = 0
    forecast_by_categories = {}
    
    for sub in user_subs:
        current_billing_date = sub.next_billing_date
        sub_total_price = 0
        
        # Крутим циклы списаний до конца кастомного прогноза
        while today <= current_billing_date <= forecast_target_date:
            sub_total_price += float(sub.price)
            if sub.billing_period == 'monthly':
                current_billing_date += relativedelta(months=1)
            elif sub.billing_period == 'yearly':
                current_billing_date += relativedelta(years=1)
                
        if sub_total_price > 0:
            if sub.service:
                cat_name = sub.service.category.name
                display_name = sub.service.name
            elif sub.category:
                cat_name = sub.category.name
                display_name = sub.custom_name
            else:
                cat_name = "Кастомные"
                display_name = sub.custom_name or "Без названия"
                
            forecast_total += sub_total_price
            
            if cat_name not in forecast_by_categories:
                forecast_by_categories[cat_name] = {'total': 0.0, 'services': []}
            forecast_by_categories[cat_name]['total'] += sub_total_price
            if display_name not in forecast_by_categories[cat_name]['services']:
                forecast_by_categories[cat_name]['services'].append(display_name)

    # === ГРАФИК MATPLOTLIB (МЕСТО 2 — УНИВЕРСАЛЬНАЯ ПРОВЕРКА КАТЕГОРИЙ) ===
    chart_data = ""
    if user_subs.exists():
        category_costs = {}
        for sub in user_subs:
            # Повторяем ту же умную проверку для секторов диаграммы
            if sub.service:
                cat_name = sub.service.category.name
            elif sub.category:
                cat_name = sub.category.name
            else:
                cat_name = "Кастомные"
                
            cost = sub.price if sub.billing_period == 'monthly' else sub.price / 12
            category_costs[cat_name] = category_costs.get(cat_name, 0) + float(cost)

        # Рисуем график с текстовыми подписями прямо на секторах (labels)
        plt.figure(figsize=(5, 5))
        plt.pie(
            category_costs.values(), 
            labels=category_costs.keys(),  # Возвращаем названия категорий на круг
            autopct='%1.1f%%', 
            startangle=140
        )
        
        # Легенду полностью убираем, оставляем только чистый заголовок
        plt.title("Распределение общих расходов", pad=20)
        
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
        'upcoming_total': round(upcoming_total, 2),
        'upcoming_by_categories': upcoming_by_categories,
        'days_limit': days_limit,
        'forecast_total': round(forecast_total, 2),
        'forecast_by_categories': forecast_by_categories,
        'forecast_days': forecast_days,
    }
    return render(request, 'subscriptions/dashboard.html', context)

# ВЬЮХА ДЛЯ СКРЫТИЯ АЛЕРТА
@login_required
def dismiss_alert(request, alert_id):
    request.session[f'dismiss_{alert_id}'] = True
    return redirect('dashboard')

@login_required
def service_catalog(request):
    search_query = request.GET.get('search', '').strip()
    category_id = request.GET.get('category', '')

    # Начинаем строить ленивый и эффективный запрос к базе данных
    services = SubscriptionService.objects.all().select_related('category')

    # 1. Фильтруем по категории на уровне СУБД (если она выбрана)
    if category_id:
        services = services.filter(category_id=category_id)

    # 2. ИСПОЛЬЗУЕМ Q-ОБЪЕКТЫ: база данных сама выполнит поиск по тексту
    if search_query:
        services = services.filter(
            Q(name__icontains=search_query)
        )

    categories = Category.objects.all()

    context = {
        'services': services,  # Теперь передаем чистый QuerySet вместо списка list()
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
    }
    return render(request, 'subscriptions/service_catalog.html', context)

@login_required
def add_subscription_by_id(request, service_id):
    service = get_object_or_404(SubscriptionService, id=service_id)
    if request.method == 'POST':
        # Используем БАЗОВУЮ форму без поля категории
        form = BaseSubscriptionForm(request.POST)
        if form.is_valid():
            subscription = form.save(commit=False)
            subscription.user = request.user
            subscription.service = service
            subscription.price = form.cleaned_data['price'] or service.default_price
            subscription.save()
            return redirect('dashboard')
    else:
        form = BaseSubscriptionForm(initial={'price': service.default_price})
        
    return render(request, 'subscriptions/add_subscription.html', {'form': form, 'title': f"Добавление подписки: {service.name}"})


@login_required
def add_custom_subscription(request):
    if request.method == 'POST':
        form = CustomSubscriptionForm(request.POST)
        if form.is_valid():
            subscription = form.save(commit=False)
            subscription.user = request.user
            # Принудительно берем категорию из виртуального поля формы и пишем в БД:
            subscription.category = form.cleaned_data['category']
            subscription.save()
            return redirect('dashboard')
    else:
        form = CustomSubscriptionForm()
    return render(request, 'subscriptions/add_subscription.html', {'form': form, 'title': "Создание кастомной подписки"})
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
    subscription = get_object_or_404(UserSubscription, id=sub_id, user=request.user)
    
    if subscription.service:
        form_class = BaseSubscriptionForm
        initial_data = {}
    else:
        form_class = CustomSubscriptionForm
        # Подставляем сохраненную категорию в форму при открытии
        initial_data = {'category': subscription.category}

    if request.method == 'POST':
        form = form_class(request.POST, instance=subscription)
        if form.is_valid():
            edited_sub = form.save(commit=False)
            if not subscription.service:
                edited_sub.category = form.cleaned_data['category']
            edited_sub.save()
            return redirect('dashboard')
    else:
        form = form_class(instance=subscription, initial=initial_data)
        
    return render(request, 'subscriptions/edit_subscription.html', {'form': form, 'subscription': subscription})