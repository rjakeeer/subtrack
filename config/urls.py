from django.contrib import admin
from django.urls import path, include
from subscriptions.views import register 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('django.contrib.auth.urls')),
    path('auth/register/', register, name='register'),
]
