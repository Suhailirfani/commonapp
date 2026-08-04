from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('portal/<slug:institution_slug>/users/', views.user_list_view, name='user_list'),
    path('portal/<slug:institution_slug>/users/create/', views.user_create_view, name='user_create'),
    path('portal/<slug:institution_slug>/users/<int:user_id>/edit/', views.user_edit_view, name='user_edit'),
    path('portal/<slug:institution_slug>/users/<int:user_id>/toggle-status/', views.toggle_user_status_view, name='toggle_user_status'),
    path('portal/<slug:institution_slug>/users/<int:user_id>/assign-programs/', views.judge_program_assign_view, name='judge_program_assign'),
]
