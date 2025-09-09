from django.contrib import admin
from .models import Expense

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        'date',
        'charged_to',
        'description',
        'amount_deposited',
        'amount_withdrawn',
        'withdrawal_charges',
        'running_balance',
    )
    list_filter = (
        'date',
        'charged_to',
    )
    search_fields = (
        'charged_to',
        'description',
    )
    ordering = ('-date',)  # show newest records first






