from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Sum
from .models import Expense
import pandas as pd
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet
from django.http import HttpResponse
from datetime import datetime
from decimal import Decimal, InvalidOperation
from .forms import ExpenseForm
from .models import Expense
from django.shortcuts import render, get_object_or_404, redirect



# -------------------- Landing Page --------------------
def landing(request):
    return render(request, "cashflow/landing.html")

# -------------------- Authentication --------------------
def register_view(request):
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "✅ Account created successfully. Please log in.")
        return redirect("login")
    return render(request, "cashflow/register.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            if user.is_staff:
                return redirect("admin_dashboard")
            else:
                return redirect("user_dashboard")
        else:
            messages.error(request, "❌ Invalid username or password")

    return render(request, "cashflow/login.html")


@login_required
def logout_view(request):
    logout(request)
    return redirect("landing")

# -------------------- Dashboard Redirect --------------------
@login_required
def dashboard(request):
    return redirect("admin_dashboard") if request.user.is_staff else redirect("user_dashboard")

# -------------------- Dashboards --------------------
@login_required


def admin_dashboard(request):
    # Start with all expenses (newest first)
    expenses = Expense.objects.all().order_by("-date")

    # Get filter values from GET request
    charged_to = request.GET.get('charged_to')
    status = request.GET.get('status')

    # Apply filters if values exist
    if charged_to:
        expenses = expenses.filter(charged_to__icontains=charged_to)
    if status:
        expenses = expenses.filter(status__iexact=status)  # case-insensitive

    # Calculate totals after filtering (replace None with 0)
    totals = expenses.aggregate(
        total_deposited=Sum('amount_deposited'),
        total_withdrawn=Sum('amount_withdrawn'),
        total_charges=Sum('withdrawal_charges')
    )
    totals = {k: v or 0 for k, v in totals.items()}

    context = {
        'expenses': expenses,
        'totals': totals,
        'charged_to': charged_to or '',
        'status': status or '',
    }

    return render(request, 'cashflow/admin_dashboard.html', context)


@login_required
def user_dashboard(request):
    # Only show expenses uploaded by the logged-in user
    expenses = Expense.objects.filter(uploaded_by=request.user).order_by("-date")

    # Filter by status from dropdown
    status = request.GET.get("status", "all")
    if status and status.lower() != "all":
        expenses = expenses.filter(status__iexact=status)  # Show only selected status

    # Totals for the filtered expenses
    totals = {
        "total_deposited": expenses.aggregate(total=Sum("amount_deposited"))["total"] or 0,
        "total_withdrawn": expenses.aggregate(total=Sum("amount_withdrawn"))["total"] or 0,
        "total_charges": expenses.aggregate(total=Sum("withdrawal_charges"))["total"] or 0,
    }

    return render(request, "cashflow/user_dashboard.html", {
        "expenses": expenses,
        "totals": totals,
        "status": status,
    })


# -------------------- Expense Management --------------------
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from .models import Expense

def add_expense(request):
    today = timezone.now().date()

    # Get all expenses uploaded by this user, ordered by date
    expenses = Expense.objects.filter(uploaded_by=request.user).order_by('date', 'id')

    # Calculate totals
    total_deposited = expenses.aggregate(total=Sum('amount_deposited'))['total'] or Decimal('0')
    total_withdrawn = expenses.aggregate(total=Sum('amount_withdrawn'))['total'] or Decimal('0')
    total_charges = expenses.aggregate(total=Sum('withdrawal_charges'))['total'] or Decimal('0')

    # Current running balance
    running_balance = total_deposited - total_withdrawn - total_charges

    if request.method == "POST":
        # Convert all inputs to Decimal
        amount_deposited = Decimal(request.POST.get('amount_deposited') or 0)
        amount_withdrawn = Decimal(request.POST.get('amount_withdrawn') or 0)
        withdrawal_charges = Decimal(request.POST.get('withdrawal_charges') or 0)

        # Update running balance with new expense
        new_balance = running_balance + amount_deposited - amount_withdrawn - withdrawal_charges

        # Create new expense
        Expense.objects.create(
            uploaded_by=request.user,
            date=request.POST.get('date') or today,
            received_by=request.POST.get('received_by'),
            charged_to=request.POST.get('charged_to'),
            description=request.POST.get('description'),
            receipt_no=request.POST.get('receipt_no'),
            amount_deposited=amount_deposited,
            amount_withdrawn=amount_withdrawn,
            withdrawal_charges=withdrawal_charges,
            running_balance=new_balance,
            status='Pending'  # optional, adjust if needed
        )

        messages.success(request, "Expense added successfully!")
        return redirect('add_expense')  # or wherever you want to go

    # Render template with current running balance
    return render(request, 'cashflow/add_expense.html', {
        'today': today,
        'current_balance': running_balance
    })


from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from .models import Expense
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import Expense

def approve_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    expense.status = "Approved"                   # Capital A
    expense.received_by = request.user.username   # Track who received it
    expense.approved_by = request.user            # Track admin approving
    expense.approved_at = timezone.now()          # Track approval time
    expense.save()
    messages.success(request, f"Expense approved by {request.user.username}.")
    return redirect("admin_dashboard")

def reject_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    expense.status = "Rejected"                   # Capital R
    expense.received_by = request.user.username   # Track who rejected
    expense.approved_by = request.user            # Optional: track who rejected
    expense.approved_at = timezone.now()          # Optional: track time
    expense.save()
    messages.success(request, f"Expense rejected by {request.user.username}.")
    return redirect("admin_dashboard")


# -------------------- Import Expenses --------------------
@login_required
def import_expenses(request):
    if request.method == "POST":
        file = request.FILES.get("file")
        if not file:
            messages.error(request, "No file uploaded.")
            return redirect("upload_expense")

        try:
            df = pd.read_excel(file)

            # 🔹 Normalize column names
            df.columns = df.columns.str.strip()           # remove spaces around names
            df.columns = df.columns.str.replace("\n", " ") # remove line breaks
            df.columns = df.columns.str.title()           # standardize capitalization

            # 🔹 Required columns (based on your Excel file)
            required_columns = [
                "Date", "Received By", "Charged To", "Description",
                "Receipt No.", "Amount Deposited", "Amount Withdrawn",
                "Withdrawal Charges", "Running Balance"
            ]
            for col in required_columns:
                if col not in df.columns:
                    messages.error(request, f"Missing column: {col}")
                    return redirect("upload_expense")

            # 🔹 Handle missing text fields
            df["Charged To"].fillna("", inplace=True)
            df["Description"].fillna("", inplace=True)
            df["Received By"].fillna("", inplace=True)
            df["Receipt No."].fillna("", inplace=True)
            df.fillna(0, inplace=True)   # numeric fields safe to 0

            imported_count = 0
            skipped_count = 0

            for _, row in df.iterrows():
                date_value = pd.to_datetime(row["Date"], dayfirst=True, errors="coerce")
                if pd.isna(date_value):
                    skipped_count += 1
                    continue

                Expense.objects.create(
                    date=date_value.date(),
                    received_by=str(row["Received By"]).strip(),
                    charged_to=str(row["Charged To"]).strip(),
                    description=str(row["Description"]).strip(),
                    receipt_no=str(row["Receipt No."]).strip(),
                    amount_deposited=row["Amount Deposited"],
                    amount_withdrawn=row["Amount Withdrawn"],
                    withdrawal_charges=row["Withdrawal Charges"],
                    running_balance=row["Running Balance"],
                    status="Pending",
                    uploaded_by=request.user
                )
                imported_count += 1

            messages.success(
                request,
                f"✅ Imported {imported_count} expenses successfully. ❌ Skipped {skipped_count} rows (invalid dates)."
            )

            if request.user.is_staff:
                return redirect("admin_dashboard")
            else:
                return redirect("user_dashboard")

        except Exception as e:
            messages.error(request, f"❌ Error uploading file: {e}")
            return redirect("upload_expense")
        # ✅ Always return something for GET requests
    return render(request, "cashflow/upload.html")

from django.shortcuts import render
from .models import Expense

def expenses_list(request):
    # Start with all expenses
    expenses = Expense.objects.all()

    # Filter parameters
    status = request.GET.get('status')
    received_by = request.GET.get('received_by')
    charged_to = request.GET.get('charged_to')
    description = request.GET.get('description')
    date = request.GET.get('date')
    amount_deposited = request.GET.get('amount_deposited')
    amount_withdrawn = request.GET.get('amount_withdrawn')

    # Apply filters
    if status:
        expenses = expenses.filter(status__iexact=status)
    if received_by:
        expenses = expenses.filter(received_by__icontains=received_by)
    if charged_to:
        expenses = expenses.filter(charged_to__icontains=charged_to)
    if description:
        expenses = expenses.filter(description__icontains=description)
    if date:
        expenses = expenses.filter(date=date)
    if amount_deposited:
        expenses = expenses.filter(amount_deposited=amount_deposited)
    if amount_withdrawn:
        expenses = expenses.filter(amount_withdrawn=amount_withdrawn)

    # Totals for the filtered list
    totals = {
        'total_deposited': sum(e.amount_deposited for e in expenses),
        'total_withdrawn': sum(e.amount_withdrawn for e in expenses),
        'total_charges': sum(e.withdrawal_charges for e in expenses),
    }

    return render(request, 'cashflow/expenses_list.html', {
        'expenses': expenses,
        'totals': totals,
    })














from django.shortcuts import get_object_or_404, render
from .models import Expense

def expense_receipt(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    return render(request, "cashflow/expense_receipt.html", {"expense": expense})

# cashflow/views.py
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Expense

def update_expense_status(request, expense_id, action):
    expense = get_object_or_404(Expense, id=expense_id)

    action_lower = action.lower()  # lowercase for comparison

    if action_lower == "approve":
        expense.status = "Approved"
        messages.success(request, f"✅ Expense '{expense.description}' has been approved.")
    elif action_lower == "reject":
        expense.status = "Rejected"
        messages.warning(request, f"❌ Expense '{expense.description}' has been rejected.")

    expense.save()
    return redirect("admin_dashboard")



from django.shortcuts import render
from .models import Expense

def admin_view_expenses(request):
    status_filter = request.GET.get("status", "All")

    if status_filter == "All":
        expenses = Expense.objects.all()
    else:
        expenses = Expense.objects.filter(status=status_filter)

    return render(request, "cashflow/admin_dashboard.html", {
        "expenses": expenses,
        "status_filter": status_filter,
    })

@login_required
# views.py





def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)

    if request.method == "POST":
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            return redirect("user_dashboard")
    else:
        form = ExpenseForm(instance=expense)

    return render(request, "cashflow/edit_expense.html", {"form": form})







def voucher_view(request, voucher_id):
    # Hapa tunapata expenses zote za voucher hiyo
    expenses = Expense.objects.filter(voucher_no=voucher_id)

    # Hapa tunacalculate totals
    totals = expenses.aggregate(
        total_shs=Sum('amount_shs'),
        total_cts=Sum('amount_cts')
    )

    return render(request, "voucher.html", {
        "expenses": expenses,
        "total_shs": totals["total_shs"] or 0,
        "total_cts": totals["total_cts"] or 0,
    })



from django import forms
from .models import Expense

class ExpenseChargedToForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["charged_to"]  # only this field is editable




        from django.shortcuts import render
from django.utils import timezone
from .models import Expense
from django.db.models import Sum

def daily_expense_report(request):
    today = timezone.localdate()  # gets today's date
    expenses = Expense.objects.filter(date=today)

    # Calculate totals
    totals = expenses.aggregate(
        deposited=Sum('amount_deposited'),
        withdrawn=Sum('amount_withdrawn'),
        withdrawal_charges=Sum('withdrawal_charges'),
        running_balance=Sum('running_balance')
    )

    context = {
        'expenses': expenses,
        'totals': totals,
        'start_date': today,
        'end_date': today
    }
    return render(request, 'cashflow/daily_expense_report.html', context)




from django.shortcuts import render, get_object_or_404
from .models import Expense

def print_expense(request, expense_id):
    # Get the expense object
    expense = get_object_or_404(Expense, id=expense_id)

    # Calculate total outgoing (amount withdrawn + withdrawal charges)
    total_outgoing = 0
    if expense.amount_withdrawn:
        total_outgoing += expense.amount_withdrawn
    if expense.withdrawal_charges:
        total_outgoing += expense.withdrawal_charges

    # Pass all required context to the template
    context = {
        'expense': expense,
        'total_outgoing': total_outgoing,
    }

    return render(request, 'cashflow/print_expense.html', context)


from django.shortcuts import render
from .models import Expense

def print_all_approved(request):
    # Fetch all expenses where status contains 'approved', case-insensitive
    approved_expenses = Expense.objects.filter(status__iexact='approved')

    return render(request, 'cashflow/print_all_approved.html', {
        'expenses': approved_expenses,
    })
