from django.urls import path
from . import views

app_name = 'public'

urlpatterns = [
    path('public/<slug:institution_slug>/', views.public_home_view, name='home'),
    path('public/<slug:institution_slug>/leaderboard/', views.public_leaderboard_view, name='leaderboard'),
    path('public/<slug:institution_slug>/results/', views.public_results_view, name='results'),
    path('public/<slug:institution_slug>/results/<int:program_id>/', views.public_program_detail_view, name='program_detail'),
    path('public/<slug:institution_slug>/contestant/<int:chest_no>/', views.public_contestant_view, name='contestant_detail'),
]
