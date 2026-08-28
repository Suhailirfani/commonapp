from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Dashboard & Competitions
    path('portal/<slug:institution_slug>/dashboard/', views.dashboard_view, name='dashboard'),
    path('portal/<slug:institution_slug>/judge-dashboard/', views.judge_dashboard_view, name='judge_dashboard'),
    path('portal/<slug:institution_slug>/help/', views.help_guide_view, name='help_guide'),
    path('portal/<slug:institution_slug>/competitions/', views.competition_list_view, name='competition_list'),
    path('portal/<slug:institution_slug>/competitions/create/', views.competition_create_view, name='competition_create'),
    path('portal/<slug:institution_slug>/competitions/<int:comp_id>/edit/', views.competition_edit_view, name='competition_edit'),
    path('portal/<slug:institution_slug>/competitions/<int:comp_id>/delete/', views.competition_delete_view, name='competition_delete'),
    
    # Categories & Programs
    path('portal/<slug:institution_slug>/categories/', views.category_list_view, name='category_list'),
    path('portal/<slug:institution_slug>/programs/', views.program_list_view, name='program_list'),
    path('portal/<slug:institution_slug>/programs/create/', views.program_create_view, name='program_create'),
    path('portal/<slug:institution_slug>/programs/batch-create/', views.program_batch_create_view, name='program_batch_create'),
    path('portal/<slug:institution_slug>/programs/bulk-upload/', views.program_bulk_upload_view, name='program_bulk_upload'),
    path('portal/<slug:institution_slug>/programs/download-template/', views.program_download_template_view, name='program_download_template'),
    path('portal/<slug:institution_slug>/programs/<int:program_id>/assign/', views.program_assign_contestants_view, name='program_assign_contestants'),
    
    # Teams & Contestants
    path('portal/<slug:institution_slug>/teams/', views.team_list_view, name='team_list'),
    path('portal/<slug:institution_slug>/contestants/', views.contestant_list_view, name='contestant_list'),
    path('portal/<slug:institution_slug>/contestants/create/', views.contestant_create_view, name='contestant_create'),
    path('portal/<slug:institution_slug>/api/next-chest-no/', views.api_get_next_chest_no_view, name='api_get_next_chest_no'),
    path('portal/<slug:institution_slug>/contestants/batch-create/', views.contestant_batch_create_view, name='contestant_batch_create'),
    path('portal/<slug:institution_slug>/contestants/bulk-upload/', views.contestant_bulk_upload_view, name='contestant_bulk_upload'),
    path('portal/<slug:institution_slug>/contestants/download-template/', views.contestant_download_template_view, name='contestant_download_template'),
    path('portal/<slug:institution_slug>/contestants/generate-credentials/', views.generate_contestant_credentials_view, name='generate_contestant_credentials'),
    path('portal/<slug:institution_slug>/contestant/dashboard/', views.contestant_personal_dashboard_view, name='contestant_personal_dashboard'),
    path('portal/<slug:institution_slug>/contestants/<int:contestant_id>/assign/', views.contestant_assign_programs_view, name='contestant_assign_programs'),
    path('portal/<slug:institution_slug>/assignments/', views.assignment_hub_view, name='assignment_hub'),
    path('portal/<slug:institution_slug>/group-assign/', views.group_assign_view, name='group_assign'),
    path('portal/<slug:institution_slug>/group-assign/<int:program_id>/', views.group_assign_view, name='group_assign_program'),
    path('portal/<slug:institution_slug>/group-assign/<int:group_part_id>/delete/', views.delete_group_participation_view, name='delete_group_participation'),
    path('portal/<slug:institution_slug>/assigned-programs/', views.assigned_programs_list_view, name='assigned_programs_list'),
    
    # PDF Reports
    path('portal/<slug:institution_slug>/reports/pdf/programs/', views.download_programs_pdf_view, name='download_programs_pdf'),
    path('portal/<slug:institution_slug>/reports/pdf/contestants-teamwise/', views.download_contestants_teamwise_pdf_view, name='download_contestants_teamwise_pdf'),
    path('portal/<slug:institution_slug>/reports/pdf/assigned-programs-teamwise/', views.download_assigned_programs_teamwise_pdf_view, name='download_assigned_programs_teamwise_pdf'),
    path('portal/<slug:institution_slug>/programs/<int:program_id>/pdf/green-room/', views.download_green_room_pdf_view, name='download_green_room_pdf'),
    path('portal/<slug:institution_slug>/programs/<int:program_id>/pdf/call-list/', views.download_call_list_pdf_view, name='download_call_list_pdf'),
    path('portal/<slug:institution_slug>/programs/<int:program_id>/pdf/valuation-form/', views.download_valuation_form_pdf_view, name='download_valuation_form_pdf'),
    path('portal/<slug:institution_slug>/programs/<int:program_id>/pdf/result/', views.download_single_result_pdf_view, name='download_single_result_pdf'),
    path('portal/<slug:institution_slug>/reports/pdf/bulk-green-room/', views.download_bulk_green_room_pdf_view, name='download_bulk_green_room_pdf'),
    path('portal/<slug:institution_slug>/reports/pdf/bulk-call-list/', views.download_bulk_call_list_pdf_view, name='download_bulk_call_list_pdf'),
    path('portal/<slug:institution_slug>/reports/pdf/bulk-valuation-form/', views.download_bulk_valuation_form_pdf_view, name='download_bulk_valuation_form_pdf'),
    path('portal/<slug:institution_slug>/reports/pdf/all-results/', views.download_all_results_pdf_view, name='download_all_results_pdf'),
    
    # Edit & Delete CRUD
    path('portal/<slug:institution_slug>/teams/<int:team_id>/edit/', views.team_edit_view, name='team_edit'),
    path('portal/<slug:institution_slug>/teams/<int:team_id>/delete/', views.team_delete_view, name='team_delete'),
    path('portal/<slug:institution_slug>/categories/<int:category_id>/edit/', views.category_edit_view, name='category_edit'),
    path('portal/<slug:institution_slug>/categories/<int:category_id>/delete/', views.category_delete_view, name='category_delete'),
    path('portal/<slug:institution_slug>/programs/<int:program_id>/edit/', views.program_edit_view, name='program_edit'),
    path('portal/<slug:institution_slug>/programs/<int:program_id>/delete/', views.program_delete_view, name='program_delete'),
    path('portal/<slug:institution_slug>/contestants/<int:contestant_id>/edit/', views.contestant_edit_view, name='contestant_edit'),
    path('portal/<slug:institution_slug>/contestants/<int:contestant_id>/delete/', views.contestant_delete_view, name='contestant_delete'),
    
    # Fast Mark Entry Matrix & Scoring
    path('portal/<slug:institution_slug>/manage-results/', views.manage_results_view, name='manage_results'),
    path('portal/<slug:institution_slug>/scoring/', views.scoring_program_list_view, name='scoring_program_list'),
    path('portal/<slug:institution_slug>/scoring/<int:program_id>/matrix/', views.mark_entry_matrix_view, name='mark_entry_matrix'),
    path('portal/<slug:institution_slug>/scoring/<int:program_id>/announce/', views.announce_results_view, name='announce_results'),
    path('portal/<slug:institution_slug>/judge-management/', views.judge_management_view, name='judge_management'),
    
    # Results & Leaderboards
    path('portal/<slug:institution_slug>/results/programs/', views.program_results_view, name='program_results'),
    path('portal/<slug:institution_slug>/results/team-standings/', views.team_standings_view, name='team_standings'),
    path('portal/<slug:institution_slug>/team-results/', views.team_results_view, name='team_results'),
    path('portal/<slug:institution_slug>/team-results/<int:team_id>/', views.team_results_view, name='team_results_detail'),
    path('portal/<slug:institution_slug>/team-results/pdf/', views.download_team_results_pdf_view, name='download_team_results_pdf'),
    path('portal/<slug:institution_slug>/team-results/<int:team_id>/pdf/', views.download_team_results_pdf_view, name='download_team_results_detail_pdf'),
    path('portal/<slug:institution_slug>/results/toppers/', views.toppers_list_view, name='toppers_list'),
    path('portal/<slug:institution_slug>/results/winner-cards/', views.shareable_results_view, name='shareable_results'),
    path('portal/<slug:institution_slug>/results/team-points-cards/', views.team_points_cards_view, name='team_points_cards'),
    
    # Public Announcement Control & Score Balancer AI
    path('portal/<slug:institution_slug>/announcements/', views.manage_announcements_view, name='manage_announcements'),
    path('portal/<slug:institution_slug>/announcements/<int:program_id>/toggle/', views.toggle_program_announcement_view, name='toggle_program_announcement'),
    path('portal/<slug:institution_slug>/announcements/balancer/', views.announcement_balancer_view, name='announcement_balancer'),
    
    # Scheduling, Settings & Points Configuration
    path('portal/<slug:institution_slug>/stages/', views.stage_list_view, name='stage_list'),
    path('portal/<slug:institution_slug>/stages/<int:stage_id>/edit/', views.stage_edit_view, name='stage_edit'),
    path('portal/<slug:institution_slug>/schedule/', views.manage_schedule_view, name='manage_schedule'),
    path('portal/<slug:institution_slug>/schedule/fest-day/add/', views.add_fest_day_view, name='add_fest_day'),
    path('portal/<slug:institution_slug>/schedule/fest-day/<int:day_id>/edit/', views.fest_day_edit_view, name='fest_day_edit'),
    path('portal/<slug:institution_slug>/schedule/fest-day/<int:day_id>/delete/', views.delete_fest_day_view, name='delete_fest_day'),
    path('portal/<slug:institution_slug>/schedule/stage/add/', views.add_stage_view, name='add_stage'),
    path('portal/<slug:institution_slug>/schedule/stage/<int:stage_id>/delete/', views.delete_stage_view, name='delete_stage'),
    path('portal/<slug:institution_slug>/schedule/save/', views.save_program_schedule_view, name='save_program_schedule'),
    path('portal/<slug:institution_slug>/schedule/program/<int:program_id>/duration/', views.update_program_duration_view, name='update_program_duration'),
    path('portal/<slug:institution_slug>/schedule/<int:schedule_id>/delete/', views.delete_program_schedule_view, name='delete_program_schedule'),
    path('portal/<slug:institution_slug>/schedule/auto-run/', views.run_auto_scheduler_view, name='run_auto_scheduler'),
    path('portal/<slug:institution_slug>/schedule/clear-all/', views.clear_all_schedules_view, name='clear_all_schedules'),
    path('portal/<slug:institution_slug>/points-config/', views.points_config_view, name='points_config'),
    path('portal/<slug:institution_slug>/settings/', views.settings_view, name='settings'),
    
    # PWA Manifest & ServiceWorker
    path('manifest.json', views.pwa_manifest_view, name='pwa_manifest'),
    path('portal/<slug:institution_slug>/manifest.json', views.pwa_manifest_view, name='pwa_manifest_institution'),
    path('serviceworker.js', views.pwa_serviceworker_view, name='pwa_serviceworker'),
]
