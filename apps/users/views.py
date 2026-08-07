from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.tenants.models import Institution
from apps.core.models import Team, Competition, Program, Category
from .models import User

def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_developer:
            return redirect('tenants:developer_dashboard')
        elif request.user.is_contestant and request.user.institution:
            return redirect('core:contestant_personal_dashboard', institution_slug=request.user.institution.slug)
        elif request.user.is_judge and request.user.institution:
            return redirect('core:judge_dashboard', institution_slug=request.user.institution.slug)
        elif request.user.institution:
            return redirect('core:dashboard', institution_slug=request.user.institution.slug)
        return redirect('landing_page')

    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            if not user.is_approved and not user.is_developer:
                messages.error(request, "Your account is currently deactivated or pending admin approval. Please contact administrator.")
                return render(request, 'users/login.html')

            if user.institution and user.institution.status != 'APPROVED' and not user.is_developer:
                messages.error(request, "Your institution subscription is currently inactive or pending approval.")
                return render(request, 'users/login.html')

            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            if user.is_developer:
                return redirect('tenants:developer_dashboard')
            elif user.is_contestant and user.institution:
                return redirect('core:contestant_personal_dashboard', institution_slug=user.institution.slug)
            elif user.is_judge and user.institution:
                return redirect('core:judge_dashboard', institution_slug=user.institution.slug)
            return redirect('core:dashboard', institution_slug=user.institution.slug)
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'users/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('landing_page')


@login_required
def user_list_view(request, institution_slug):
    institution = get_object_or_404(Institution, slug=institution_slug)
    users = User.objects.filter(institution=institution).prefetch_related('assigned_competitions', 'assigned_programs').order_by('role', 'username')
    
    q = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '').strip()

    if q:
        users = users.filter(Q(username__icontains=q) | Q(email__icontains=q) | Q(designation__icontains=q))
    if role_filter:
        users = users.filter(role=role_filter)

    return render(request, 'users/user_list.html', {
        'institution': institution, 
        'users': users,
        'q': q,
        'role_filter': role_filter,
        'role_choices': User.ROLE_CHOICES
    })


@login_required
def user_create_view(request, institution_slug):
    institution = get_object_or_404(Institution, slug=institution_slug)
    if not (request.user.is_developer or request.user.is_institution_admin):
        messages.error(request, "Permission Denied: Only Institution Admin can add sub-users.")
        return redirect('core:dashboard', institution_slug=institution.slug)

    teams = Team.objects.filter(institution=institution)
    competitions = Competition.objects.filter(institution=institution)
    programs = Program.objects.filter(institution=institution).select_related('category')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        designation = request.POST.get('designation', '')
        team_id = request.POST.get('team_id')
        comp_ids = request.POST.getlist('assigned_competition_ids[]')
        prog_ids = request.POST.getlist('assigned_program_ids[]')

        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' already exists.")
            return render(request, 'users/user_create.html', {
                'institution': institution, 'teams': teams, 'competitions': competitions, 'programs': programs
            })

        if role == 'TEAM_LEADER' and not team_id:
            messages.error(request, "A Team Leader must be connected to a specific team. Please select a team.")
            return render(request, 'users/user_create.html', {
                'institution': institution, 'teams': teams, 'competitions': competitions, 'programs': programs
            })

        new_user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            institution=institution,
            designation=designation,
            is_approved=True
        )

        if role == 'TEAM_LEADER' and team_id:
            team = get_object_or_404(Team, id=team_id, institution=institution)
            team.user = new_user
            team.save()

        if role == 'JUDGE':
            if comp_ids:
                new_user.assigned_competitions.set(Competition.objects.filter(id__in=comp_ids, institution=institution))
            if prog_ids:
                new_user.assigned_programs.set(Program.objects.filter(id__in=prog_ids, institution=institution))

        messages.success(request, f"User '{username}' ({new_user.get_role_display()}) created successfully!")
        return redirect('users:user_list', institution_slug=institution.slug)

    return render(request, 'users/user_create.html', {
        'institution': institution,
        'teams': teams,
        'competitions': competitions,
        'programs': programs
    })


@login_required
def user_edit_view(request, institution_slug, user_id):
    institution = get_object_or_404(Institution, slug=institution_slug)
    if not (request.user.is_developer or request.user.is_institution_admin):
        messages.error(request, "Permission Denied.")
        return redirect('core:dashboard', institution_slug=institution.slug)

    target_user = get_object_or_404(User, id=user_id, institution=institution)
    teams = Team.objects.filter(institution=institution)
    competitions = Competition.objects.filter(institution=institution)
    programs = Program.objects.filter(institution=institution).select_related('category')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        designation = request.POST.get('designation', '')
        team_id = request.POST.get('team_id')
        comp_ids = request.POST.getlist('assigned_competition_ids[]')
        prog_ids = request.POST.getlist('assigned_program_ids[]')
        is_approved = request.POST.get('is_approved') == 'on'

        target_user.email = email
        target_user.role = role
        target_user.designation = designation
        target_user.is_approved = is_approved

        if password and len(password.strip()) > 0:
            target_user.set_password(password.strip())

        target_user.save()

        if role == 'TEAM_LEADER' and team_id:
            team = get_object_or_404(Team, id=team_id, institution=institution)
            team.user = target_user
            team.save()

        if role == 'JUDGE':
            target_user.assigned_competitions.set(Competition.objects.filter(id__in=comp_ids, institution=institution))
            target_user.assigned_programs.set(Program.objects.filter(id__in=prog_ids, institution=institution))
        else:
            target_user.assigned_competitions.clear()
            target_user.assigned_programs.clear()

        messages.success(request, f"User '{target_user.username}' updated successfully!")
        return redirect('users:user_list', institution_slug=institution.slug)

    return render(request, 'users/user_edit.html', {
        'institution': institution,
        'target_user': target_user,
        'teams': teams,
        'competitions': competitions,
        'programs': programs
    })


@login_required
def toggle_user_status_view(request, institution_slug, user_id):
    institution = get_object_or_404(Institution, slug=institution_slug)
    if not (request.user.is_developer or request.user.is_institution_admin):
        messages.error(request, "Permission Denied.")
        return redirect('core:dashboard', institution_slug=institution.slug)

    target_user = get_object_or_404(User, id=user_id, institution=institution)
    target_user.is_approved = not target_user.is_approved
    target_user.save()

    status_str = "ACTIVATED" if target_user.is_approved else "DEACTIVATED"
    messages.success(request, f"User '{target_user.username}' has been {status_str}!")
    return redirect('users:user_list', institution_slug=institution.slug)


@login_required
def judge_program_assign_view(request, institution_slug, user_id):
    institution = get_object_or_404(Institution, slug=institution_slug)
    if not (request.user.is_developer or request.user.is_institution_admin):
        messages.error(request, "Permission Denied.")
        return redirect('core:dashboard', institution_slug=institution.slug)

    judge_user = get_object_or_404(User, id=user_id, institution=institution, role='JUDGE')
    categories = Category.objects.filter(institution=institution).prefetch_related('programs', 'programs__competition')
    existing_assigned_prog_ids = set(judge_user.assigned_programs.values_list('id', flat=True))

    if request.method == 'POST':
        selected_ids = request.POST.getlist('assigned_program_ids[]')
        selected_ids_set = set(int(x) for x in selected_ids if str(x).isdigit())

        assigned_progs = Program.objects.filter(id__in=selected_ids_set, institution=institution)
        judge_user.assigned_programs.set(assigned_progs)

        messages.success(request, f"Assigned {assigned_progs.count()} program(s) to Judge '{judge_user.username}' successfully!")
        return redirect('users:user_list', institution_slug=institution.slug)

    return render(request, 'users/judge_program_assign.html', {
        'institution': institution,
        'judge_user': judge_user,
        'categories': categories,
        'existing_assigned_prog_ids': existing_assigned_prog_ids,
    })
