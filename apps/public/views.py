from django.shortcuts import render, get_object_or_404
from apps.tenants.models import Institution
from apps.core.models import (
    Competition, Team, Program, Contestant, 
    Participation, GroupParticipation, Announcement
)

from apps.core.services import get_team_standings

def check_public_access(institution, request):
    if institution.is_public_suspended:
        return render(request, 'public/suspended.html', {'institution': institution}, status=403)
    return None


def public_home_view(request, institution_slug):
    institution = get_object_or_404(Institution, slug=institution_slug, status='APPROVED')
    suspended_response = check_public_access(institution, request)
    if suspended_response:
        return suspended_response

    competition = Competition.objects.filter(institution=institution, is_active=True).first()
    
    standings = get_team_standings(institution, announced_only=True) if competition else []
    top_teams = standings[:5]

    announced_programs = Program.objects.filter(institution=institution, is_announced=True).order_by('-announced_at')[:8]
    announcements = Announcement.objects.filter(institution=institution, is_public=True)[:5]

    context = {
        'institution': institution,
        'competition': competition,
        'top_teams': top_teams,
        'announced_programs': announced_programs,
        'announcements': announcements,
    }
    return render(request, 'public/home.html', context)


def public_leaderboard_view(request, institution_slug):
    institution = get_object_or_404(Institution, slug=institution_slug, status='APPROVED')
    suspended_response = check_public_access(institution, request)
    if suspended_response:
        return suspended_response

    standings = get_team_standings(institution, announced_only=True)
    return render(request, 'public/leaderboard.html', {'institution': institution, 'teams': standings})


def public_results_view(request, institution_slug):
    institution = get_object_or_404(Institution, slug=institution_slug, status='APPROVED')
    suspended_response = check_public_access(institution, request)
    if suspended_response:
        return suspended_response

    announced_programs = Program.objects.filter(institution=institution, is_announced=True).select_related('category').order_by('result_number', 'announced_at', 'id')
    return render(request, 'public/results.html', {'institution': institution, 'programs': announced_programs})


def public_program_detail_view(request, institution_slug, program_id):
    institution = get_object_or_404(Institution, slug=institution_slug, status='APPROVED')
    suspended_response = check_public_access(institution, request)
    if suspended_response:
        return suspended_response

    program = get_object_or_404(Program, id=program_id, institution=institution, is_announced=True)
    
    if program.is_group:
        participations = GroupParticipation.objects.filter(
            program=program,
            rank__in=[1, 2, 3]
        ).select_related('team').order_by('rank', '-marks')
    else:
        participations = Participation.objects.filter(
            program=program,
            rank__in=[1, 2, 3]
        ).select_related('contestant', 'contestant__team').order_by('rank', '-marks')

    return render(request, 'public/program_detail.html', {
        'institution': institution,
        'program': program,
        'participations': participations
    })


def public_contestant_view(request, institution_slug, chest_no):
    institution = get_object_or_404(Institution, slug=institution_slug, status='APPROVED')
    suspended_response = check_public_access(institution, request)
    if suspended_response:
        return suspended_response

    contestant = get_object_or_404(Contestant, chest_no=chest_no, institution=institution)
    participations = Participation.objects.filter(contestant=contestant, program__is_announced=True).select_related('program')

    return render(request, 'public/contestant_detail.html', {
        'institution': institution,
        'contestant': contestant,
        'participations': participations
    })
