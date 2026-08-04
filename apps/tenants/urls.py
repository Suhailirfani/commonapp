from django.urls import path
from . import views

app_name = 'tenants'

urlpatterns = [
    # Application & Developer Admin routes
    path('apply/', views.subscription_apply_view, name='apply'),
    path('apply/payment/<int:app_id>/', views.subscription_payment_view, name='apply_payment'),
    path('developer/dashboard/', views.developer_dashboard_view, name='developer_dashboard'),
    path('developer/applications/<int:app_id>/approve/', views.approve_application_view, name='approve_application'),
    path('developer/applications/<int:app_id>/reject/', views.reject_application_view, name='reject_application'),

    # Subscription Plan Developer routes
    path('developer/plans/create/', views.plan_create_view, name='plan_create'),
    path('developer/plans/<int:plan_id>/edit/', views.plan_edit_view, name='plan_edit'),
    path('developer/plans/<int:plan_id>/toggle/', views.plan_toggle_status_view, name='plan_toggle_status'),
    path('developer/plans/<int:plan_id>/delete/', views.plan_delete_view, name='plan_delete'),
]
