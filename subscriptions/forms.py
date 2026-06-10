from django import forms
from .models import UserSubscription, Category

# 1. Форма для добавления ГОТОВЫХ сервисов из каталога
class BaseSubscriptionForm(forms.ModelForm):
    price = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label="Стоимость подписки")

    class Meta:
        model = UserSubscription
        fields = ['price', 'billing_period', 'next_billing_date', 'is_active']
        widgets = {
            'next_billing_date': forms.DateInput(attrs={'type': 'date'}),
        }


# 2. Форма для добавления ПОЛНОСТЬЮ КАСТОМНЫХ сервисов (наследует базу и добавляет нужные поля)
class CustomSubscriptionForm(forms.ModelForm):
    price = forms.DecimalField(max_digits=10, decimal_places=2, required=True, label="Стоимость подписки")
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=True, label="Категория подписки")

    class Meta:
        model = UserSubscription
        fields = ['category', 'custom_name', 'price', 'billing_period', 'next_billing_date', 'is_active']
        widgets = {
            'next_billing_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        custom_name = cleaned_data.get('custom_name')
        if not custom_name:
            raise forms.ValidationError("Для кастомной подписки необходимо ввести название!")
        return cleaned_data

