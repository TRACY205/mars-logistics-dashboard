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
@login_required
def add_expense(request):
    if request.method == "POST":
        # Get data from the form
        date_str = request.POST.get("date")  # must match HTML input name
        charged_to = request.POST.get("charged_to")
        description = request.POST.get("description")        # separate field
        receipt_no = request.POST.get("receipt_no")          # separate field
        amount_deposited = request.POST.get("amount_deposited") or 0
        amount_withdrawn = request.POST.get("amount_withdrawn") or 0
        withdrawal_charges = request.POST.get("withdrawal_charges") or 0
        running_balance = request.POST.get("running_balance") or 0

        # Validate and convert date
        if not date_str:
            messages.error(request, "⚠️ Date is required.")
            return redirect("add_expense")
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "⚠️ Invalid date format. Use YYYY-MM-DD.")
            return redirect("add_expense")

        # Create the expense record and link to current user
        Expense.objects.create(
            date=date_obj,
            charged_to=charged_to,
            description=description,      # store description
            receipt_no=receipt_no,        # store receipt number
            amount_deposited=amount_deposited,
            amount_withdrawn=amount_withdrawn,
            withdrawal_charges=withdrawal_charges,
            running_balance=running_balance,
            uploaded_by=request.user
        )

        messages.success(request, "✅ Expense added successfully.")
        return redirect("user_dashboard")

    return render(request, "cashflow/add_expense.html")

# views.py
from django.shortcuts import render, redirect
from .forms import ExpenseForm
from .models import Expense

def add_expense_user(request):
    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.uploaded_by = request.user  # must match field name in your model
            expense.status = "Pending"
            expense.save()
            return redirect('user_dashboard')
    else:
        form = ExpenseForm()
    return render(request, 'cashflow/add_expense.html', {'form': form})


def add_expense_admin(request):
    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.status = "Pending"
            expense.user = request.user
            expense.save()
            return redirect("admin_dashboard")  
    else:
        form = ExpenseForm()

    return render(request, "cashflow/add_expense.html", {"form": form})



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


def expenses_list(request, status):
    expenses = Expense.objects.filter(status=status.capitalize())
    total_amount = expenses.aggregate(total=Sum("amount_withdrawn"))["total"] or 0
    return render(request, "cashflow/view_expenses.html", {
        "expenses": expenses,
        "status": status.capitalize(),
        "total_amount": total_amount,
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
def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, uploaded_by=request.user)

    if request.method == "POST":
        form = ExpenseChargedToForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            return redirect("user_dashboard")  # or wherever you want
    else:
        form = ExpenseChargedToForm(instance=expense)

    return render(request, "cashflow/edit_expense.html", {"form": form})


from django.shortcuts import get_object_or_404, render
from .models import Expense
def print_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)

    total_outgoing = (expense.amount_withdrawn or 0) + (expense.withdrawal_charges or 0)

    context = {
        'expense': expense,
        'total_outgoing': total_outgoing,
    }
    return render(request, "cashflow/print_expense.html", context)



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



