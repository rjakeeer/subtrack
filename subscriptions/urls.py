from django.urls import path
from . import views
from subscriptions.api_views import UserSubscriptionsAPIView

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    # Старый путь 'add/' теперь ведет сначала на каталог сервисов
    path('add/', views.service_catalog, name='add_subscription'),
    path('add/template/<int:service_id>/', views.add_subscription_by_id, name='add_subscription_by_id'),
    path('add/custom/', views.add_custom_subscription, name='add_custom_subscription'),
    path('edit/<int:sub_id>/', views.edit_subscription, name='edit_subscription'),
    path('delete/<int:sub_id>/', views.delete_subscription, name='delete_subscription'),
    path('dismiss-alert/<str:alert_id>/', views.dismiss_alert, name='dismiss_alert'),
    path('api/v1/my-subscriptions/', UserSubscriptionsAPIView.as_view(), name='api_my_subscriptions'),
]