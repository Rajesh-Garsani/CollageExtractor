import uuid
from django.db import models
from django.contrib.auth.models import User


class TimeStampedModel(models.Model):
    """Abstract base class ensuring consistent timestamping."""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Session(TimeStampedModel):
    """Tracks active user sessions to prevent re-uploads and maintain context."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Session {self.id}"


class Collage(TimeStampedModel):
    """Stores the original uploaded AI collage."""
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='collages')
    image = models.ImageField(upload_to='collages/%Y/%m/%d/')
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    status = models.CharField(
        max_length=20,
        choices=[('PENDING', 'Pending'), ('ANALYZING', 'Analyzing'), ('COMPLETED', 'Completed'), ('FAILED', 'Failed')],
        default='PENDING'
    )

    def __str__(self) -> str:
        return f"Collage {self.id} - {self.status}"


class Panel(TimeStampedModel):
    """Represents a single detected image panel within a collage."""
    collage = models.ForeignKey(Collage, on_delete=models.CASCADE, related_name='panels')
    panel_index = models.PositiveIntegerField(help_text="Sequential index of the panel")

    # Bounding Box Coordinates (x, y, w, h)
    x_coord = models.PositiveIntegerField()
    y_coord = models.PositiveIntegerField()
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()

    # Internal layout analysis
    header_height = models.PositiveIntegerField(default=0, help_text="Height of the text area")
    has_borders = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"Panel {self.panel_index} from Collage {self.collage_id}"


class OCRResult(TimeStampedModel):
    """Stores EasyOCR detections tied to a specific panel."""
    panel = models.OneToOneField(Panel, on_delete=models.CASCADE, related_name='ocr_data')
    image_number = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    caption = models.TextField(null=True, blank=True)
    raw_text = models.TextField(help_text="Full text dumped from OCR")
    confidence_score = models.FloatField(default=0.0)

    def __str__(self) -> str:
        return f"OCR for Panel {self.panel.panel_index}: {self.image_number}"


class PromptHistory(TimeStampedModel):
    """Stores the user's natural language chats/commands."""
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='prompts')
    raw_prompt = models.TextField()
    parsed_intent = models.JSONField(help_text="NLP extracted intent (target_image, actions)")
    status = models.CharField(
        max_length=20,
        choices=[('SUCCESS', 'Success'), ('ERROR', 'Error')],
        default='SUCCESS'
    )

    def __str__(self) -> str:
        return f"Prompt {self.id}: {self.raw_prompt[:30]}"


class GeneratedImage(TimeStampedModel):
    """Stores the final extracted and processed output images."""
    prompt = models.ForeignKey(PromptHistory, on_delete=models.CASCADE, related_name='generated_images')
    source_panel = models.ForeignKey(Panel, on_delete=models.SET_NULL, null=True)
    result_image = models.ImageField(upload_to='outputs/%Y/%m/%d/')
    processing_time_ms = models.PositiveIntegerField(default=0)
    applied_operations = models.JSONField(help_text="List of ops: crop, inpaint, upscale, etc.")

    def __str__(self) -> str:
        return f"Output {self.id} for Prompt {self.prompt_id}"