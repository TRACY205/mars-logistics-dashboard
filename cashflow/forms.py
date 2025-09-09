from django import forms
from .models import Expense

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        # Include all fields you want editable
        fields = [
            "date",
            "received_by",
            "charged_to",
            "description",
            "receipt_no",
            "amount_deposited",
            "amount_withdrawn",
            "withdrawal_charges",
            "running_balance",
        ]

        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "received_by": forms.TextInput(attrs={
                "class": "w-full p-2 border border-gray-300 rounded-lg",
                "placeholder": "Enter Received By",
            }),
            "charged_to": forms.TextInput(attrs={
                "class": "w-full p-2 border border-gray-300 rounded-lg",
                "placeholder": "Enter Charged To",
            }),
            "description": forms.Textarea(attrs={
                "class": "w-full p-2 border border-gray-300 rounded-lg",
                "placeholder": "Enter Description",
                "rows": 3,
            }),
            "receipt_no": forms.TextInput(attrs={"class": "form-control"}),
            "amount_deposited": forms.NumberInput(attrs={"class": "form-control"}),
            "amount_withdrawn": forms.NumberInput(attrs={"class": "form-control"}),
            "withdrawal_charges": forms.NumberInput(attrs={"class": "form-control"}),
            "running_balance": forms.NumberInput(attrs={"class": "form-control"}),
        }

