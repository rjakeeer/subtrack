from django.contrib import admin
from .models import Category, SubscriptionService, UserSubscription

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}  # Автоматически генерирует слаг из названия при вводе в админке


@admin.register(SubscriptionService)
class SubscriptionServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'default_price')
    list_filter = ('category',)
    search_fields = ('name',)


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'get_service_name', 'price', 'billing_period', 'next_billing_date', 'is_active')
    list_filter = ('billing_period', 'is_active', 'next_billing_date')
    search_fields = ('custom_name', 'service__name', 'user__username')
    date_hierarchy = 'next_billing_date'  # Удобная навигация по датам вверху админки

    def get_service_name(self, obj):
        return obj.service.name if obj.service else obj.custom_name
    get_service_name.short_description = "Название сервиса / подписки"
