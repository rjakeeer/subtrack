from django import forms
from .models import UserSubscription

from django import forms
from .models import UserSubscription

class UserSubscriptionForm(forms.ModelForm):
    # Делаем поле цены необязательным в форме, чтобы Django не ругался на пустоту
    price = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label="Стоимость подписки")

    class Meta:
        model = UserSubscription
        fields = ['service', 'custom_name', 'price', 'billing_period', 'next_billing_date', 'is_active']
        widgets = {
            'next_billing_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        service = cleaned_data.get('service')
        custom_name = cleaned_data.get('custom_name')
        price = cleaned_data.get('price')

        # 1. Валидация на заполнение имени
        if not service and not custom_name:
            raise forms.ValidationError("Выберите сервис из каталога или введите кастомное название!")
        
        # 2. Чистый Python-автозапуск цены: если цена не введена, но сервис выбран
        if price is None and service:
            cleaned_data['price'] = service.default_price
        elif price is None:
            # Если это кастомный сервис и цены нет, ставим 0.00 или просим ввести
            raise forms.ValidationError("Для кастомного сервиса необходимо указать стоимость!")

        return cleaned_data
