from django.contrib import admin
from .models import (
    Competition, Category, Team, Stage, FestDay,
    Program, ProgramSchedule, Contestant, Participation,
    GroupParticipation, PointsConfig, Announcement, CertificateConfig
)

@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'institution', 'type', 'year', 'is_active', 'created_at')
    list_filter = ('type', 'is_active', 'institution', 'year')
    search_fields = ('name', 'institution__name')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'competition', 'institution', 'is_common', 'start_chest_no')
    list_filter = ('is_common', 'institution', 'competition')
    search_fields = ('name', 'description')
    filter_horizontal = ('included_categories',)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'code_letter', 'competition', 'user', 'total_points', 'institution')
    list_filter = ('competition', 'institution')
    search_fields = ('name', 'code_letter', 'user__username')


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('name', 'stage_type', 'location_details', 'institution')
    list_filter = ('stage_type', 'institution')
    search_fields = ('name', 'location_details')


@admin.register(FestDay)
class FestDayAdmin(admin.ModelAdmin):
    list_display = ('day_number', 'name', 'competition', 'date', 'start_time', 'end_time', 'institution')
    list_filter = ('competition', 'institution')


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'competition', 'category', 'program_type', 'is_group', 'presentation_mode', 'duration_per_participant', 'is_announced', 'institution')
    list_filter = ('program_type', 'is_group', 'presentation_mode', 'is_announced', 'institution', 'competition', 'category')
    search_fields = ('name',)


@admin.register(ProgramSchedule)
class ProgramScheduleAdmin(admin.ModelAdmin):
    list_display = ('program', 'fest_day', 'stage', 'start_time', 'end_time', 'total_duration_minutes', 'institution')
    list_filter = ('fest_day', 'stage', 'institution')
    search_fields = ('program__name',)


@admin.register(Contestant)
class ContestantAdmin(admin.ModelAdmin):
    list_display = ('chest_no', 'name', 'team', 'category', 'competition', 'institution', 'total_points')
    list_filter = ('category', 'team', 'competition', 'institution')
    search_fields = ('name', 'chest_no')


@admin.register(Participation)
class ParticipationAdmin(admin.ModelAdmin):
    list_display = ('contestant', 'program', 'code_letter', 'marks', 'rank', 'grade', 'points_awarded', 'institution')
    list_filter = ('program', 'rank', 'grade', 'institution')
    search_fields = ('contestant__name', 'contestant__chest_no', 'program__name', 'code_letter')


@admin.register(GroupParticipation)
class GroupParticipationAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'program', 'team', 'captain', 'code_letter', 'marks', 'rank', 'grade', 'institution')
    list_filter = ('program', 'team', 'rank', 'grade', 'institution')
    search_fields = ('group_name', 'team__name', 'captain__name', 'program__name', 'code_letter')
    filter_horizontal = ('contestants',)


@admin.register(PointsConfig)
class PointsConfigAdmin(admin.ModelAdmin):
    list_display = ('institution', 'single_rank_1_points', 'single_rank_2_points', 'single_rank_3_points', 'group_rank_1_points', 'group_rank_2_points', 'group_rank_3_points')


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'is_public', 'created_at', 'institution')
    list_filter = ('priority', 'is_public', 'institution')
    search_fields = ('title', 'message')


@admin.register(CertificateConfig)
class CertificateConfigAdmin(admin.ModelAdmin):
    list_display = ('institution', 'mode', 'title', 'signatory_1_title', 'signatory_2_title', 'issue_date', 'created_at')
    list_filter = ('mode', 'institution')
    search_fields = ('title', 'subtitle', 'institution__name')

