from django import forms
from .models import Expense
class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = [
            'date', 'received_by', 'charged_to', 'description',
            'receipt_no', 'amount_deposited', 'amount_withdrawn', 'withdrawal_charges'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full p-2 border rounded-lg'}),
            'description': forms.Textarea(attrs={'class': 'w-full p-2 border rounded-lg', 'rows': 3}),
            'received_by': forms.TextInput(attrs={'class': 'w-full p-2 border rounded-lg'}),
            'charged_to': forms.TextInput(attrs={'class': 'w-full p-2 border rounded-lg'}),
            'receipt_no': forms.TextInput(attrs={'class': 'w-full p-2 border rounded-lg'}),
            'amount_deposited': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded-lg', 'step': '0.01'}),
            'amount_withdrawn': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded-lg', 'step': '0.01'}),
            'withdrawal_charges': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded-lg', 'step': '0.01'}),
        }

