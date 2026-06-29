from django.urls import path
from django.views.generic import TemplateView

app_name = 'extractor'

urlpatterns = [
    # Main SPA Workspace Platform Dashboard
    path(
        '',
        TemplateView.as_view(template_name='extractor/dashboard.html'),
        name='dashboard'
    ),
]