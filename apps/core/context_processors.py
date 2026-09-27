from apps.core.models import Competition

def active_fest_context(request):
    """
    Context processor to provide active fest and all institution fests
    globally to templates.
    """
    institution = getattr(request, 'institution', None)
    if not institution and request.user.is_authenticated:
        institution = getattr(request.user, 'institution', None)

    if not institution:
        rm = getattr(request, 'resolver_match', None)
        if rm and 'institution_slug' in rm.kwargs:
            from apps.tenants.models import Institution
            institution = Institution.objects.filter(slug=rm.kwargs['institution_slug']).first()

    if not institution:
        return {}

    from apps.core.views import get_active_fest
    active_fest = get_active_fest(request, institution)

    # Team leaders are tied strictly to their assigned team's fest
    if request.user.is_authenticated and getattr(request.user, 'is_team_leader', False) and not getattr(request.user, 'is_developer', False):
        all_fests = [active_fest] if active_fest else []
        return {
            'active_fest': active_fest,
            'active_competition': active_fest,
            'all_institution_fests': all_fests,
            'has_multiple_fests': False,
        }

    all_fests = list(Competition.objects.filter(institution=institution).order_by('-year', '-created_at', '-id'))

    return {
        'active_fest': active_fest,
        'active_competition': active_fest,
        'all_institution_fests': all_fests,
        'has_multiple_fests': len(all_fests) > 1,
    }
