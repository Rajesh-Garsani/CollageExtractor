from django.urls import path
from .views import (
    UploadCollageView,
    AnalyzeCollageView,
    ChatExtractView
)

app_name = 'api'

urlpatterns = [
    path('upload/', UploadCollageView.as_view(), name='upload_collage'),
    path('analyze/<int:collage_id>/', AnalyzeCollageView.as_view(), name='analyze_collage'),
    path('chat/', ChatExtractView.as_view(), name='chat_extract'),
]