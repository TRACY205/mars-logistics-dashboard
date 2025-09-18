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


# -------------------- Landing --------------------
def landing(request):
    return render(request, "cashflow/landing.html")

# -------------------- Register --------------------
def register_view(request):
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "✅ Account created successfully. Please log in.")
        return redirect("login")
    return render(request, "cashflow/register.html", {"form": form})

# -------------------- Login --------------------
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login

def login_view(request):
    role = request.GET.get('role', '')  # get role from URL query param

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        login_type = request.POST.get("login_type")  # 'admin' or 'user'

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Check if user is admin or regular user
            if login_type == "admin" and user.is_staff:
                login(request, user)
                return redirect("admin_dashboard")
            elif login_type == "user" and not user.is_staff:
                login(request, user)
                return redirect("user_dashboard")
            else:
                messages.error(request, "You don't have permission for this role.")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "cashflow/login.html", {"role": role})


# -------------------- Logout --------------------
@login_required
def logout_view(request):
    logout(request)
    return redirect("landing")

# -------------------- Dashboard Redirect --------------------
@login_required
def dashboard(request):
    return redirect("admin_dashboard") if request.user.is_staff else redirect("user_dashboard")

def admin_dashboard(request):
    # Only allow admins
    if not request.user.is_staff:
        return redirect('user_dashboard')  # redirect regular users

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

    # Calculate totals after filtering
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


@login_required
def user_dashboard(request):
    # Redirect staff/admins to admin dashboard
    if request.user.is_staff:
        return redirect('admin_dashboard')

    # Get all expenses uploaded by this user
    expenses = Expense.objects.filter(uploaded_by=request.user).order_by("-date")

    # Get status filter from GET params
    status = request.GET.get("status", "all")
    if status.lower() != "all":
        expenses = expenses.filter(status__iexact=status)

    # Totals for filtered expenses
    totals = {
        "total_deposited": expenses.aggregate(total=Sum("amount_deposited"))["total"] or 0,
        "total_withdrawn": expenses.aggregate(total=Sum("amount_withdrawn"))["total"] or 0,
        "total_charges": expenses.aggregate(total=Sum("withdrawal_charges"))["total"] or 0,
    }

    context = {
        "expenses": expenses,
        "totals": totals,
        "status": status,
    }

    return render(request, "cashflow/user_dashboard.html", context)

from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum
from .models import Expense

def add_expense(request, user_type="user"):
    today = timezone.now().date()

    # Get all expenses uploaded by this user, ordered by date
    expenses = Expense.objects.filter(uploaded_by=request.user).order_by('date', 'id')

    # Calculate totals
    total_deposited = expenses.aggregate(total=Sum('amount_deposited'))['total'] or Decimal('0')
    total_withdrawn = expenses.aggregate(total=Sum('amount_withdrawn'))['total'] or Decimal('0')
    total_charges = expenses.aggregate(total=Sum('withdrawal_charges'))['total'] or Decimal('0')

    running_balance = total_deposited - total_withdrawn - total_charges

    if request.method == "POST":
        amount_deposited = Decimal(request.POST.get('amount_deposited') or 0)
        amount_withdrawn = Decimal(request.POST.get('amount_withdrawn') or 0)
        withdrawal_charges = Decimal(request.POST.get('withdrawal_charges') or 0)

        new_balance = running_balance + amount_deposited - amount_withdrawn - withdrawal_charges

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
            status='Pending'
        )

        messages.success(request, "Expense added successfully!")

        # Redirect based on user_type
        if user_type == "admin":
            return redirect('add_expense_admin')
        else:
            return redirect('add_expense_user')

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


from django.shortcuts import render, get_object_or_404, redirect
from .models import Expense
from .forms import ExpenseForm

def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)

    if request.method == "POST":
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            # Redirect depending on user type
            if request.user.is_staff:  # Admin
                return redirect('admin_dashboard')
            else:  # Regular user
                return redirect('user_dashboard')
        else:
            print(form.errors)  # Debugging: shows why save fails
    else:
        form = ExpenseForm(instance=expense)

    return render(request, 'cashflow/edit_expense.html', {
        'form': form,
        'expense': expense,  # Pass expense to show read-only fields like running_balance
    })








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



from django.shortcuts import render
from .models import Expense
from django.db.models import Sum
from datetime import datetime

def pettycash_summary(request):
    day_str = request.GET.get('day')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    day = start_date = end_date = None

    # Convert strings to date objects
    try:
        if day_str:
            day = datetime.strptime(day_str, "%Y-%m-%d").date()
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        # invalid date format, ignore
        pass

    # Fetch expenses
    expenses = Expense.objects.all()

    if day:
        expenses = expenses.filter(date=day)
    elif start_date and end_date:
        expenses = expenses.filter(date__range=[start_date, end_date])

    # Totals
    totals = expenses.aggregate(
        deposited=Sum('amount_deposited') or 0,
        withdrawn=Sum('amount_withdrawn') or 0,
        withdrawal_charges=Sum('withdrawal_charges') or 0
    )
    
    last_balance = expenses.last().running_balance if expenses.exists() else 0

    context = {
        'expenses': expenses,
        'totals': totals,
        'last_balance': last_balance,
        'prepared_by': request.user.get_full_name() or request.user.username,
        'approved_by': None,
        'day': day,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'cashflow/pettycash_summary.html', context)

 
 



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

from django.shortcuts import render
from .models import Expense
from django.contrib.auth.decorators import login_required

@login_required
def print_selected_expenses(request):
    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_expenses")  # list of IDs
        expenses = Expense.objects.filter(id__in=selected_ids)
    else:
        expenses = []

    return render(request, "cashflow/print_expense.html", {
        "expenses": expenses
    })


@login_required
def select_print_approved(request):
    approved_expenses = Expense.objects.filter(status__iexact="Approved")

    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_expenses")
        expenses = approved_expenses.filter(id__in=selected_ids)
    else:
        expenses = approved_expenses

    return render(request, "cashflow/select_print_approved.html", {
        "expenses": expenses
    })



from django.shortcuts import redirect
from django.contrib import messages
from .models import Expense

def delete_selected_expenses(request):
    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_expenses")
        if selected_ids:
            Expense.objects.filter(id__in=selected_ids).delete()
            messages.success(request, f"{len(selected_ids)} expense(s) deleted successfully.")
        else:
            messages.warning(request, "No expenses selected.")
    return redirect("admin_dashboard")  # redirect back to your dashboard
