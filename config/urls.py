from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.tenants import views as tenant_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Public SaaS Landing page & Application
    path('', tenant_views.landing_page_view, name='landing_page'),
    
    # Apps routing
    path('auth/', include('apps.users.urls')),
    path('subscriptions/', include('apps.tenants.urls')),
    path('tenants/', include('apps.tenants.urls')),
    path('', include('apps.core.urls')),
    path('', include('apps.public.urls')),
]

handler403 = 'apps.core.views.custom_403_view'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
