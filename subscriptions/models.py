from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название категории")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="URL-слаг")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class SubscriptionService(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название сервиса")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='services', verbose_name="Категория")
    default_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Базовая стоимость")

    class Meta:
        verbose_name = "Шаблон сервиса"
        verbose_name_plural = "Шаблоны сервисов"

    def __str__(self):
        return self.name


class UserSubscription(models.Model):
    BILLING_CHOICES = [
        ('monthly', 'Раз в месяц'),
        ('yearly', 'Раз в год'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions', verbose_name="Пользователь")
    service = models.ForeignKey(SubscriptionService, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Сервис из каталога")
    custom_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Кастомное название")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Стоимость подписки")
    billing_period = models.CharField(max_length=10, choices=BILLING_CHOICES, default='monthly', verbose_name="Периодичность списания")
    next_billing_date = models.DateField(verbose_name="Дата следующего списания")
    is_active = models.BooleanField(default=True, verbose_name="Статус (активна)")

    class Meta:
        verbose_name = "Подписка пользователя"
        verbose_name_plural = "Подписки пользователей"
        ordering = ['next_billing_date']

    def __str__(self):
        # Если привязан сервис из каталога, берем его имя, иначе кастомное
        return self.service.name if self.service else self.custom_name

