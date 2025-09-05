# cashflow/forms.py
from django import forms
from .models import Expense


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = [
            "date",
            "charged_to",
            "description",
            "amount_deposited",
            "amount_withdrawn",
            "withdrawal_charges",
            "running_balance",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "charged_to": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "amount_deposited": forms.NumberInput(attrs={"class": "form-control"}),
            "amount_withdrawn": forms.NumberInput(attrs={"class": "form-control"}),
            "withdrawal_charges": forms.NumberInput(attrs={"class": "form-control"}),
            # If you want to edit receipt_no here, add it to fields above and then uncomment:
            # "receipt_no": forms.TextInput(attrs={"class": "form-control"}),
        }


from django import forms
from .models import Expense

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["received_by", "charged_to", "description"]

        widgets = {
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
        }


