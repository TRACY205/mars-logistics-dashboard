from django.urls import path
from . import views

urlpatterns = [
    # -------------------- Landing & Auth --------------------
    path("", views.landing, name="landing"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),

    # -------------------- Dashboards --------------------
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),
    path("dashboard/user/", views.user_dashboard, name="user_dashboard"),

    # -------------------- Expense Management --------------------
    path(
        "dashboard/add-expense/",
        views.add_expense,
        name="add_expense_user"
    ),
    path(
        "dashboard/admin/add-expense/",
        lambda request: views.add_expense(request, user_type="admin"),
        name="add_expense_admin"
    ),
    path("upload-expense/", views.import_expenses, name="upload_expense"),
    path("expenses/", views.expenses_list, name="expenses_list"),

    # -------------------- Expense Actions --------------------
    path(
        "expenses/<int:expense_id>/<str:action>/",
        views.update_expense_status,
        name="update_expense_status"
    ),
    path("expense/<int:expense_id>/edit/", views.edit_expense, name="edit_expense"),
    path("expense/print/<int:expense_id>/", views.print_expense, name="print_expense"),

    # -------------------- Expense Receipts --------------------
    path("expenses/<int:pk>/receipt/", views.expense_receipt, name="expense_receipt"),
    path("pettycash/summary/", views.pettycash_summary, name="pettycash_summary"),
    path("pettycash/daily/", views.pettycash_summary, name="daily_expense_report"),

    # -------------------- Print All Approved --------------------
    path("expenses/print-all-approved/", views.print_all_approved, name="print_all_approved"),
]



 



















 

















 


















       