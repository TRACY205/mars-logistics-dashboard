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
    # User add expense
    path("dashboard/add-expense/", views.add_expense_user, name="add_expense_user"),
    # Admin add expense
    path("dashboard/admin/add-expense/", views.add_expense_admin, name="add_expense_admin"),
    path("upload-expense/", views.import_expenses, name="upload_expense"),
    path("expenses/status/<str:status>/", views.expenses_list, name="expenses_list"),

    # -------------------- Expense Actions --------------------
    path("expenses/<int:expense_id>/<str:action>/", views.update_expense_status, name="update_expense_status"),
    path('expense/<int:expense_id>/edit/', views.edit_expense, name='edit_expense'),
    path('expense/print/<int:expense_id>/', views.print_expense, name='print_expense'),

    # -------------------- Expense Receipts --------------------
    path("expenses/<int:pk>/receipt/", views.expense_receipt, name="expense_receipt"),
    # Expense Actions
path('expense/<int:expense_id>/edit/', views.edit_expense, name='edit_expense'),

]



 


















 



















 

















 


















       