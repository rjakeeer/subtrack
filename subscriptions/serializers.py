from rest_framework import serializers
from .models import UserSubscription

class UserSubscriptionSerializer(serializers.ModelSerializer):
    # Чтобы в JSON выводилось понятное имя сервиса или кастомное название
    service_name = serializers.CharField(source='__str__', read_only=True)
    category_name = serializers.CharField(source='service.category.name', read_only=True)

    class Meta:
        model = UserSubscription
        fields = ['id', 'service_name', 'category_name', 'price', 'billing_period', 'next_billing_date', 'is_active']
