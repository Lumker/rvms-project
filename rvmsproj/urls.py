from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect

def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('governance:dashboard')
    return redirect('users:login')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication URLs (Django's built-in auth views without namespace)
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Your custom user URLs
    path('users/', include('users.urls')),
    
    # Governance app
    path('governance/', include('governance.urls')),
    
    path('households/', include('households.urls')),
    path('documents/', include('documents.urls')),
    path('infrastructure/', include('infrastructure.urls')),
    
    # Root URL
    path('', home_redirect, name='home'),
    path('search/', include('search.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)