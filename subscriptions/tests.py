from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Category, SubscriptionService, UserSubscription
from datetime import datetime

class SubTrackBonusTests(TestCase):
    def setUp(self):
        """Создание тестового окружения с учётными данными admin/admin."""
        self.client = Client()
        self.user = User.objects.create_user(username='admin', password='admin')
        self.category = Category.objects.create(name='Стриминг', slug='streaming')
        
        # 1. Создаем сам сервис-шаблон
        self.service = SubscriptionService.objects.create(
            name='Яндекс Плюс',
            category=self.category
        )
        
        # 2. Создаем подписку пользователя
        self.subscription = UserSubscription.objects.create(
            user=self.user,
            service=self.service,
            price=299.00,
            billing_period='monthly',
            next_billing_date=datetime.now().date(),
            is_active=True
        )

    def test_user_creation(self):
        """Тест 1: Проверка успешного создания пользователя в базе."""
        user_count = User.objects.count()
        self.assertEqual(user_count, 1)

    def test_category_slug_and_name(self):
        """Тест 2: Проверка корректности создания категории."""
        self.assertEqual(self.category.name, 'Стриминг')
        self.assertEqual(self.category.slug, 'streaming')

    def test_service_template_creation(self):
        """Тест 3: Проверка успешного создания шаблона сервиса."""
        self.assertEqual(self.service.name, 'Яндекс Плюс')
        self.assertEqual(self.service.category, self.category)

    def test_subscription_string_representation(self):
        """Тест 4: Проверка корректности строкового метода модели."""
        self.assertTrue(len(str(self.subscription)) > 0)

    def test_subscription_active_status(self):
        """Тест 5: Проверка логического флага активности подписки."""
        self.assertTrue(self.subscription.is_active)
