from rest_framework import serializers
from extractor.models import Session, Collage, Panel, OCRResult, PromptHistory, GeneratedImage


class OCRResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = OCRResult
        fields = ['image_number', 'caption', 'raw_text', 'confidence_score']


class PanelSerializer(serializers.ModelSerializer):
    ocr_data = OCRResultSerializer(read_only=True)

    class Meta:
        model = Panel
        fields = ['id', 'panel_index', 'x_coord', 'y_coord', 'width', 'height', 'has_borders', 'ocr_data']


class CollageSerializer(serializers.ModelSerializer):
    panels = PanelSerializer(many=True, read_only=True)

    class Meta:
        model = Collage
        fields = ['id', 'session', 'original_filename', 'file_size', 'status', 'created_at', 'image', 'panels']


class CollageUploadSerializer(serializers.ModelSerializer):
    """Handles strict validation for incoming image collage files."""

    class Meta:
        model = Collage
        fields = ['image']

    def validate_image(self, value):
        """Validate file extension and size (e.g., max 20MB)."""
        valid_extensions = ['jpg', 'jpeg', 'png', 'webp']
        ext = value.name.split('.')[-1].lower()
        if ext not in valid_extensions:
            raise serializers.ValidationError("Unsupported file format. Use JPG, PNG, or WEBP.")

        if value.size > 20 * 1024 * 1024:
            raise serializers.ValidationError("File size exceeds 20MB limit.")

        return value


class GeneratedImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedImage
        fields = ['id', 'result_image', 'processing_time_ms', 'applied_operations', 'created_at']


class ChatRequestSerializer(serializers.Serializer):
    """Validates incoming chat prompts from the user."""
    session_id = serializers.UUIDField(required=True)
    prompt = serializers.CharField(max_length=1000, required=True, trim_whitespace=True)