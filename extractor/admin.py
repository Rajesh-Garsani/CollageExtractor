"""
Django Admin configuration for the extractor app.

This module registers the database models with the Django admin interface,
providing optimized list displays, filters, search capabilities, and inline
editing to ensure a professional and efficient back-office experience.
"""

from django.contrib import admin
from .models import (
    Session,
    Collage,
    Panel,
    OCRResult,
    PromptHistory,
    GeneratedImage
)

# ---------------------------------------------------------
# Admin Site Customization
# ---------------------------------------------------------
admin.site.site_header = "Collage Extractor Administration"
admin.site.site_title = "Collage Extractor Admin Portal"
admin.site.index_title = "Welcome to the AI Image Extractor Portal"


# ---------------------------------------------------------
# Inline Configurations
# ---------------------------------------------------------
class PanelInline(admin.TabularInline):
    """Allows viewing and editing Panels directly from the Collage admin page."""
    model = Panel
    extra = 0
    fields = ('panel_index', 'x_coord', 'y_coord', 'width', 'height', 'has_borders')
    readonly_fields = ('panel_index', 'x_coord', 'y_coord', 'width', 'height')
    can_delete = False


class OCRResultInline(admin.StackedInline):
    """Allows viewing OCR results directly within the Panel admin page."""
    model = OCRResult
    extra = 0
    readonly_fields = ('raw_text', 'confidence_score', 'created_at')
    can_delete = False


class GeneratedImageInline(admin.TabularInline):
    """Allows viewing generated images directly from the Prompt History."""
    model = GeneratedImage
    extra = 0
    readonly_fields = ('result_image', 'processing_time_ms', 'applied_operations')
    can_delete = False


# ---------------------------------------------------------
# Model Admin Configurations
# ---------------------------------------------------------
@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    """Admin interface for user sessions."""
    list_display = ('id', 'user', 'is_active', 'created_at', 'expires_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('id', 'user__username', 'user__email')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_select_related = ('user',)
    list_per_page = 50


@admin.register(Collage)
class CollageAdmin(admin.ModelAdmin):
    """Admin interface for uploaded collages."""
    list_display = ('id', 'session', 'status', 'original_filename', 'file_size', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('original_filename', 'session__id')
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('session',)
    inlines = [PanelInline]
    list_per_page = 50


@admin.register(Panel)
class PanelAdmin(admin.ModelAdmin):
    """Admin interface for individual detected panels."""
    list_display = ('id', 'collage', 'panel_index', 'has_borders', 'created_at')
    list_filter = ('has_borders', 'created_at')
    search_fields = ('collage__id', 'collage__original_filename')
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('collage',)
    inlines = [OCRResultInline]
    list_per_page = 50


@admin.register(OCRResult)
class OCRResultAdmin(admin.ModelAdmin):
    """Admin interface for extracted text from panels."""
    list_display = ('id', 'panel', 'image_number', 'confidence_score', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('image_number', 'caption', 'raw_text', 'panel__id')
    readonly_fields = ('created_at', 'updated_at', 'raw_text', 'confidence_score')
    list_select_related = ('panel',)
    list_per_page = 50


@admin.register(PromptHistory)
class PromptHistoryAdmin(admin.ModelAdmin):
    """Admin interface for user chat prompts and their NLP parsing status."""
    list_display = ('id', 'session', 'short_prompt', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('raw_prompt', 'session__id')
    readonly_fields = ('created_at', 'updated_at', 'parsed_intent')
    list_select_related = ('session',)
    inlines = [GeneratedImageInline]
    list_per_page = 50

    def short_prompt(self, obj: PromptHistory) -> str:
        """Returns a truncated version of the raw prompt for cleaner list views."""
        return obj.raw_prompt[:50] + "..." if len(obj.raw_prompt) > 50 else obj.raw_prompt
    short_prompt.short_description = "Prompt"


@admin.register(GeneratedImage)
class GeneratedImageAdmin(admin.ModelAdmin):
    """Admin interface for final output images."""
    list_display = ('id', 'prompt', 'source_panel', 'processing_time_ms', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('prompt__raw_prompt', 'source_panel__id')
    readonly_fields = ('created_at', 'updated_at', 'processing_time_ms', 'applied_operations')
    list_select_related = ('prompt', 'source_panel')
    list_per_page = 50