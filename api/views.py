import cv2
import time
import logging
from django.db import transaction
from django.core.files.base import ContentFile
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

from extractor.models import Session, Collage, Panel, OCRResult, PromptHistory, GeneratedImage
from extractor.services.vision import VisionService
from extractor.services.ocr_engine import OCREngineService
from extractor.services.nlp_parser import NLPParserService

from image_processing.cropper import ImageCropper
from image_processing.inpainter import ImageInpainter
from image_processing.enhancer import ImageEnhancer
from image_processing.upscaler import ImageUpscaler

from .serializers import (CollageUploadSerializer, CollageSerializer, ChatRequestSerializer, GeneratedImageSerializer)

logger = logging.getLogger("api")


class UploadCollageView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = CollageUploadSerializer(data=request.data)
        if serializer.is_valid():
            image_file = serializer.validated_data['image']
            session = Session.objects.create()
            collage = Collage.objects.create(session=session, image=image_file, original_filename=image_file.name,
                                             file_size=image_file.size, status='PENDING')
            response_data = CollageSerializer(collage, context={'request': request}).data
            response_data['session_id'] = session.id
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AnalyzeCollageView(APIView):
    def post(self, request, collage_id):
        try:
            collage = Collage.objects.get(id=collage_id)
        except Collage.DoesNotExist:
            return Response({"error": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        collage.status = 'ANALYZING'
        collage.save()

        try:
            full_image_np = cv2.imread(collage.image.path)

            # STEP 1: Full-Page Semantic OCR Sweep
            ocr_service = OCREngineService()
            full_ocr_data = ocr_service.extract_all(full_image_np)

            # STEP 2: Mathematical Grid Inference
            vision = VisionService()
            detected_panels = vision.infer_panels(full_image_np, full_ocr_data)

            with transaction.atomic():
                for p_data in detected_panels:
                    panel = Panel.objects.create(
                        collage=collage, panel_index=p_data['panel_index'],
                        x_coord=p_data['x_coord'], y_coord=p_data['y_coord'],
                        width=p_data['width'], height=p_data['height'],
                        header_height=p_data['header_height'], has_borders=p_data['has_borders']
                    )
                    OCRResult.objects.create(
                        panel=panel, image_number=p_data['ocr_image_number'],
                        raw_text=p_data['ocr_raw_text'], confidence_score=p_data['ocr_confidence']
                    )

            collage.status = 'COMPLETED'
            collage.save()
            return Response(CollageSerializer(collage, context={'request': request}).data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}", exc_info=True)
            collage.status = 'FAILED';
            collage.save()
            return Response({"error": "Engine failure."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatExtractView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        session_id = serializer.validated_data['session_id']
        raw_prompt = serializer.validated_data['prompt']

        try:
            session = Session.objects.get(id=session_id, is_active=True)
            collage = session.collages.latest('created_at')
        except:
            return Response({"error": "Invalid session."}, status=status.HTTP_404_NOT_FOUND)

        start_time = time.time()
        nlp = NLPParserService()
        intent = nlp.parse_prompt(raw_prompt)
        prompt_history = PromptHistory.objects.create(session=session, raw_prompt=raw_prompt, parsed_intent=intent,
                                                      status='PENDING')

        target_number = intent.get("target_image_number")
        if not target_number:
            prompt_history.status = 'ERROR';
            prompt_history.save()
            return Response({"error": "No image number identified."}, status=status.HTTP_400_BAD_REQUEST)

        # Smart Search
        target_panel = Panel.objects.filter(collage=collage, ocr_data__image_number__contains=target_number).first()
        if not target_panel:
            target_panel = Panel.objects.filter(collage=collage, panel_index=int(target_number)).first()
            if not target_panel:
                prompt_history.status = 'ERROR';
                prompt_history.save()
                return Response({"error": f"Image '{target_number}' not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            full_img = cv2.imread(collage.image.path)
            applied_ops = []
            actions = intent.get("actions", {})

            # Step A: Precision Mathematical Crop
            panel_img = ImageCropper.crop_panel(
                full_img, target_panel.x_coord, target_panel.y_coord, target_panel.width, target_panel.height
            )
            applied_ops.append("precision_crop")

            # REORDERED: Auto-Remove borders BEFORE resizing so we don't shave pixels off the exact target size
            panel_img = ImageCropper.auto_remove_borders(panel_img)

            # Step B: Deep Text Removal
            exclusion_text = intent.get("raw_exclusion_text")
            remove_all = actions.get("remove_all_text")

            if remove_all or exclusion_text:
                ocr_service = OCREngineService()
                ocr_results = ocr_service.extract_all(panel_img)
                text_boxes = []

                import re
                ex_words = set(re.findall(r'\w+', exclusion_text.lower())) if exclusion_text else set()
                stop_words = {'a', 'an', 'the', 'of', 'in', 'and', 'by'}
                ex_words = ex_words - stop_words

                for item in ocr_results:
                    text = item['text'].lower()
                    if exclusion_text:
                        item_words = set(re.findall(r'\w+', text)) - stop_words
                        if ex_words.intersection(
                                item_words) or exclusion_text.lower() in text or text in exclusion_text.lower():
                            text_boxes.append((item['x'], item['y'], item['w'], item['h']))
                    elif remove_all:
                        text_boxes.append((item['x'], item['y'], item['w'], item['h']))

                if text_boxes:
                    panel_img = ImageInpainter.inpaint_exact_regions(panel_img, text_boxes)
                    applied_ops.append("selective_text_removal" if exclusion_text else "deep_text_removal")

            # Step C: Pro-Fidelity Upscale & Sizing
            target_w = actions.get("target_width")
            target_h = actions.get("target_height")
            scale_factor = actions.get("upscale_factor", 1)

            upscaler = ImageUpscaler()
            if target_w and target_h:
                # FIXED: Call resize_to_target on the upscaler directly, not on _strategy
                panel_img = upscaler.resize_to_target(panel_img, target_w, target_h)
                applied_ops.append(f"resized_{target_w}x{target_h}")
            elif scale_factor > 1:
                panel_img = upscaler.process(panel_img, scale_factor)
                applied_ops.append(f"pro_upscale_{scale_factor}x")

            # Step D: Final Studio Enhancement
            panel_img = ImageEnhancer.enhance_quality(panel_img)
            applied_ops.append("studio_enhancement")

            # Output File
            output_format = actions.get("output_format", "png")
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 100] if output_format == "jpeg" else []
            _, buffer = cv2.imencode(f'.{output_format}', panel_img, encode_param)

            file_name = f"extracted_{target_number}_{int(time.time())}.{output_format}"
            generated_image = GeneratedImage.objects.create(
                prompt=prompt_history, source_panel=target_panel,
                result_image=ContentFile(buffer.tobytes(), name=file_name),
                processing_time_ms=int((time.time() - start_time) * 1000),
                applied_operations=applied_ops
            )

            prompt_history.status = 'SUCCESS'
            prompt_history.save()
            from .serializers import GeneratedImageSerializer
            return Response(GeneratedImageSerializer(generated_image, context={'request': request}).data,
                            status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Pipeline failure: {str(e)}", exc_info=True)
            prompt_history.status = 'ERROR'
            prompt_history.save()
            return Response({"error": "Pipeline failure."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)