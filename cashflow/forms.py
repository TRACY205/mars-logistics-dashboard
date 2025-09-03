# cashflow/forms.py
from django import forms
from .models import Expense

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = [
            'date',
            'charged_to',
            'description',
            'amount_deposited',
            'amount_withdrawn',
            'withdrawal_charges',
            'running_balance',

        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "charged_to": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.TextInput(attrs={"class": "form-control"}),
            "receipt_no": forms.TextInput(attrs={"class": "form-control"}),
            "amount_deposited": forms.NumberInput(attrs={"class": "form-control"}),
            "amount_withdrawn": forms.NumberInput(attrs={"class": "form-control"}),
            "withdrawal_charges": forms.NumberInput(attrs={"class": "form-control"}),
        }


