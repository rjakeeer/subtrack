from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add/', views.add_subscription, name='add_subscription'),
    path('delete/<int:sub_id>/', views.delete_subscription, name='delete_subscription'),
]
