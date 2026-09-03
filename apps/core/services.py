from django.db.models import Max
from apps.core.models import (
    Participation, GroupParticipation, PointsConfig, 
    Team, Contestant
)

def get_default_start_chest_no_for_category(category):
    """
    Computes default starting chest number sequence for a category spaced by 1000s
    if category.start_chest_no is not explicitly customized.
    """
    if category.start_chest_no and category.start_chest_no != 1001:
        return category.start_chest_no

    from apps.core.models import Category
    base_cats = list(Category.objects.filter(institution=category.institution, is_common=False).order_by('id'))
    try:
        idx = base_cats.index(category)
    except ValueError:
        idx = 0
    return (idx + 1) * 1000 + 1  # 1001, 2001, 3001, 4001...


def get_next_chest_number(category):
    """
    Computes next available chest number for a base category based on its configured or default start_chest_no,
    guaranteeing it does NOT collide with any existing contestant in the institution + competition.
    """
    start_no = get_default_start_chest_no_for_category(category)
    existing_max = Contestant.objects.filter(
        institution=category.institution,
        category=category,
        chest_no__isnull=False
    ).aggregate(Max('chest_no'))['chest_no__max']

    if existing_max and existing_max >= start_no:
        candidate = existing_max + 1
    else:
        candidate = start_no

    used_numbers = set(Contestant.objects.filter(
        institution=category.institution,
        competition=category.competition,
        chest_no__isnull=False
    ).values_list('chest_no', flat=True))

    while candidate in used_numbers:
        candidate += 1

    return candidate


def auto_generate_all_chest_numbers(institution, overwrite=False):
    """
    Sequentially generates/assigns chest numbers for all contestants category by category,
    starting from each category's start_chest_no or default range (1001, 2001, 3001...).
    Uses a 2-pass institution-wide update to eliminate database UNIQUE constraint collisions.
    """
    from apps.core.models import Category, Contestant

    categories = list(Category.objects.filter(institution=institution, is_common=False).order_by('id'))
    all_contestants = list(Contestant.objects.filter(institution=institution).order_by('id'))

    if not all_contestants:
        return 0

    # Step 1: Assign temporary unique offsets to ALL contestants across the institution
    for c in all_contestants:
        if overwrite or not c.chest_no:
            c.chest_no = 900000 + c.id
            c.save(update_fields=['chest_no'])

    # Step 2: Assign final sequential chest numbers category by category
    count = 0
    for cat in categories:
        cat_contestants = [c for c in all_contestants if c.category_id == cat.id]
        if not cat_contestants:
            continue

        start_no = get_default_start_chest_no_for_category(cat)
        current_no = start_no

        for c in cat_contestants:
            if c.chest_no >= 900000:
                c.chest_no = current_no
                c.save(update_fields=['chest_no'])
                count += 1
                current_no += 1
            else:
                current_no = max(current_no, c.chest_no + 1)

    return count

def calculate_program_results(program):
    """
    Auto-calculates Ranks, Grades, and Team Points for a given program.
    """
    institution = program.institution
    config = PointsConfig.objects.filter(institution=institution).first()
    if not config:
        config = PointsConfig.objects.create(institution=institution)

    if program.is_group:
        GroupParticipation.objects.filter(program=program, marks__isnull=True).update(rank=None, grade=None)
        participations = list(GroupParticipation.objects.filter(program=program, marks__isnull=False).order_by('-marks'))
    else:
        Participation.objects.filter(program=program, marks__isnull=True).update(rank=None, grade=None)
        participations = list(Participation.objects.filter(program=program, marks__isnull=False).order_by('-marks'))

    if not participations:
        recalculate_team_points(institution)
        return

    # Calculate Ranks & Grades
    for idx, part in enumerate(participations):
        if idx > 0 and part.marks == participations[idx-1].marks:
            part.rank = participations[idx-1].rank
        else:
            part.rank = idx + 1

        # Grade calculation with A+ support
        if part.marks >= config.grade_aplus_threshold:
            part.grade = 'A+'
        elif part.marks >= config.grade_a_threshold:
            part.grade = 'A'
        elif part.marks >= config.grade_b_threshold:
            part.grade = 'B'
        elif part.marks >= config.grade_c_threshold:
            part.grade = 'C'
        else:
            part.grade = None

    # Assign permanent sequential result number upon mark entry (1 for first entry, 2, 3...)
    from django.db.models import Max
    if not program.result_number:
        max_num = Program.objects.filter(
            institution=institution,
            competition=program.competition,
            result_number__isnull=False
        ).aggregate(Max('result_number'))['result_number__max'] or 0
        program.result_number = max_num + 1
        program.save(update_fields=['result_number'])

    recalculate_team_points(institution)


def get_team_standings(institution, announced_only=True, limit_n_results=None):
    """
    Computes exact team standings, total points, 1st/2nd/3rd win counts, and positions.
    Guarantees 100% mathematical consistency between Admin Portal and Public Leaderboard.
    Optionally limits calculation to the first N results announced or marked.
    """
    from django.db.models import Q
    from apps.core.models import Program
    teams = list(Team.objects.filter(institution=institution).order_by('name'))
    team_data = []

    allowed_program_ids = None
    if limit_n_results is not None:
        try:
            n_val = int(limit_n_results)
            if n_val > 0:
                prog_qs = Program.objects.filter(institution=institution)
                if announced_only:
                    prog_qs = prog_qs.filter(is_announced=True)
                else:
                    prog_qs = prog_qs.filter(
                        Q(single_participations__marks__isnull=False) | Q(group_participations__marks__isnull=False)
                    ).distinct()
                
                allowed_program_ids = set(
                    prog_qs.order_by('announced_at', 'id')
                    .values_list('id', flat=True)[:n_val]
                )
        except (ValueError, TypeError):
            allowed_program_ids = None

    for team in teams:
        calc_points = 0

        # Contestant individual points
        parts = Participation.objects.filter(
            institution=institution,
            contestant__team=team,
            marks__isnull=False
        )
        if announced_only:
            parts = parts.filter(program__is_announced=True)
        if allowed_program_ids is not None:
            parts = parts.filter(program_id__in=allowed_program_ids)

        for p in parts:
            if p.rank or p.grade:
                calc_points += p.total_points

        # Group program points
        gps = GroupParticipation.objects.filter(
            institution=institution,
            team=team,
            marks__isnull=False
        )
        if announced_only:
            gps = gps.filter(program__is_announced=True)
        if allowed_program_ids is not None:
            gps = gps.filter(program_id__in=allowed_program_ids)

        for gp in gps:
            if gp.rank or gp.grade:
                calc_points += gp.total_points

        # Win counts (1st, 2nd, 3rd)
        all_parts = Participation.objects.filter(
            institution=institution,
            contestant__team=team,
            marks__isnull=False
        )
        if announced_only:
            all_parts = all_parts.filter(program__is_announced=True)
        if allowed_program_ids is not None:
            all_parts = all_parts.filter(program_id__in=allowed_program_ids)

        first_count = all_parts.filter(rank=1).count()
        second_count = all_parts.filter(rank=2).count()
        third_count = all_parts.filter(rank=3).count()

        all_gps = GroupParticipation.objects.filter(
            institution=institution,
            team=team,
            marks__isnull=False
        )
        if announced_only:
            all_gps = all_gps.filter(program__is_announced=True)
        if allowed_program_ids is not None:
            all_gps = all_gps.filter(program_id__in=allowed_program_ids)

        first_count += all_gps.filter(rank=1).count()
        second_count += all_gps.filter(rank=2).count()
        third_count += all_gps.filter(rank=3).count()

        # Sync persistent team.total_points for announced results when computing full standings
        if announced_only and allowed_program_ids is None:
            if team.total_points != calc_points:
                team.total_points = calc_points
                team.save(update_fields=['total_points'])

        team_data.append({
            'team': team,
            'points': calc_points,
            'first_count': first_count,
            'second_count': second_count,
            'third_count': third_count,
            'total_wins': first_count + second_count + third_count
        })

    team_data.sort(key=lambda x: (x['points'], x['first_count'], x['second_count'], x['third_count']), reverse=True)

    current_rank = 1
    for i, data in enumerate(team_data):
        if i > 0 and data['points'] < team_data[i-1]['points']:
            current_rank = i + 1
        data['position'] = current_rank

    return team_data

    return team_data


def recalculate_team_points(institution):
    """
    Recalculates total points for all teams and contestants under an institution.
    """
    from apps.core.models import Contestant
    get_team_standings(institution, announced_only=True)
    
    # Sync persistent contestant.total_points
    for c in Contestant.objects.filter(institution=institution):
        c_pts = c.calculated_total_points
        if c.total_points != c_pts:
            c.total_points = c_pts
            c.save(update_fields=['total_points'])
