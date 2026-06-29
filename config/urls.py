"""
URL Configuration for the AIImageExtractor project.

This module routes URLs to their respective applications.
- 'admin/' routes to the Django Admin panel.
- '' (root) delegates to the 'extractor' app for frontend template rendering.
- 'api/v1/' delegates to the 'api' app for RESTful JSON endpoints (DRF).
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ---------------------------------------------------------
    # Core Administration
    # ---------------------------------------------------------
    path('admin/', admin.site.urls),

    # ---------------------------------------------------------
    # Frontend Web Application (Templates, HTML, UI)
    # ---------------------------------------------------------
    path('', include('extractor.urls', namespace='extractor')),

    # ---------------------------------------------------------
    # API Endpoints (AJAX, DRF, File Processing)
    # ---------------------------------------------------------
    path('api/v1/', include('api.urls', namespace='api')),
]

# ---------------------------------------------------------
# Local Development: Serve Static & Media Files
# ---------------------------------------------------------
# Note: In production (e.g., PythonAnywhere), static and media files
# should be served by the web server (Nginx/Apache), not Django.
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )