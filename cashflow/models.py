from django.db import models
from django.contrib.auth.models import User

class Expense(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
        ("Locked", "Locked"),
    ]

    # Excel fields
    date = models.DateField()
    received_by = models.CharField(max_length=255, null=True, blank=True)
    charged_to = models.CharField(max_length=255)
    description = models.TextField()
    receipt_no = models.CharField(max_length=100, blank=True, null=True)
    amount_deposited = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_withdrawn = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    withdrawal_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    running_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")

    # System-only fields
    uploaded_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="uploaded_expenses"
    )
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="approved_expenses"
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.receipt_no or 'No Receipt'} - {self.description} ({self.status})"



