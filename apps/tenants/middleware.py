from django.core.exceptions import PermissionDenied
from apps.tenants.models import Institution

class TenantMiddleware:
    """
    Middleware to resolve current tenant (Institution) for path-based multi-tenancy.
    Attaches request.tenant to every incoming request.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = None
        path_parts = [p for p in request.path.strip('/').split('/') if p]

        # 1. Resolve tenant slug from URL path if present (e.g. /portal/mueeniyya/... or /public/mueeniyya/...)
        url_tenant_slug = None
        if len(path_parts) >= 2 and path_parts[0] in ['portal', 'public', 'fest']:
            url_tenant_slug = path_parts[1]

        if url_tenant_slug:
            try:
                tenant = Institution.objects.get(slug=url_tenant_slug)
                request.tenant = tenant
            except Institution.DoesNotExist:
                request.tenant = None

        # 2. Scrape logged-in user's tenant scope
        if request.user.is_authenticated:
            # Developers have access to institution portals only if allowed by institution
            if request.user.is_developer:
                if request.tenant and path_parts and path_parts[0] == 'portal':
                    if not request.tenant.allow_developer_access:
                        from django.contrib import messages
                        from django.shortcuts import redirect
                        messages.warning(request, f"🔒 Developer Support Access is currently disabled by {request.tenant.name}. The institution admin must enable it in their Settings to permit access.")
                        return redirect('tenants:developer_dashboard')
            elif request.user.institution:
                user_tenant = request.user.institution
                
                # Check if institution status is approved
                if user_tenant.status != 'APPROVED':
                    # Allow access only to pending status page or logout
                    if not request.path.startswith('/auth/pending/'):
                        pass
                
                # If user tries to access another tenant's URL path, block it!
                if request.tenant and request.tenant.id != user_tenant.id and not request.user.is_developer:
                    raise PermissionDenied("Access Denied: You do not have permission to view another institution's portal.")
                
                # Default request.tenant to user's assigned institution if not resolved from URL
                if not request.tenant:
                    request.tenant = user_tenant

        response = self.get_response(request)
        return response
