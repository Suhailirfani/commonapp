from django.urls import path
from . import views

app_name = 'tenants'

urlpatterns = [
    # Developer Admin & Subscription routes
    path('apply/', views.subscription_apply_view, name='apply'),
    path('apply/payment/<int:app_id>/', views.subscription_payment_view, name='apply_payment'),
    path('developer/dashboard/', views.developer_dashboard_view, name='developer_dashboard'),
    path('developer/applications/<int:app_id>/approve/', views.approve_application_view, name='approve_application'),
    path('developer/applications/<int:app_id>/reject/', views.reject_application_view, name='reject_application'),
]
