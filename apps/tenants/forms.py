from django import forms
from django.utils.text import slugify
from .models import SubscriptionPlan

class SubscriptionPlanForm(forms.ModelForm):
    class Meta:
        model = SubscriptionPlan
        fields = [
            'name', 'code', 'max_competitions', 'max_contestants',
            'original_price', 'price', 'description', 'description_ml', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Standard Plan'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. standard-plan (auto-generated if empty)'}),
            'max_competitions': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'max_contestants': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'original_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'English description and key features'}),
            'description_ml': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Malayalam description (optional)'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip()
        name = self.cleaned_data.get('name', '').strip()
        if not code and name:
            code = slugify(name)
        else:
            code = slugify(code)
        
        # Check uniqueness
        qs = SubscriptionPlan.objects.filter(code=code)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(f"A plan with code '{code}' already exists. Please choose a different code.")
        return code
