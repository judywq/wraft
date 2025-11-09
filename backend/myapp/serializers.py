"""
Django REST Framework serializers for essay evaluation models.

This module provides serializers for converting essay evaluation instances
to/from JSON for API responses. Includes different serializers for different
use cases (list, create, retrieve).
"""

from rest_framework import serializers

from .models import EssayEvaluation


class BriefEssayEvaluationSerializer(serializers.ModelSerializer):
    """
    Brief serializer for essay evaluation list views.
    
    Includes only essential fields for displaying a list of evaluations:
    ID, status, error, essay text, score, and creation time.
    """
    class Meta:
        model = EssayEvaluation
        fields = ["id", "status", "error", "essay_text", "score", "created_at"]


class EssayEvaluationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new essay evaluations.
    
    Includes only the input fields required to create an evaluation:
    essay prompt and essay text.
    """
    class Meta:
        model = EssayEvaluation
        fields = ["essay_prompt", "essay_text"]


class EssayEvaluationRetrieveSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving full essay evaluation details.
    
    Includes status, error, timestamps, and the full evaluation data
    (prompt, text, corrections, score) via the formatted_data property.
    """
    # Custom field containing full evaluation data
    evaluation = serializers.SerializerMethodField()

    class Meta:
        model = EssayEvaluation
        fields = ["id", "status", "error", "created_at", "updated_at", "evaluation"]

    def get_evaluation(self, obj):
        """
        Get the formatted evaluation data.
        
        Returns the full evaluation data including essay text, corrections,
        and score in a structured format.
        
        Args:
            obj: The EssayEvaluation instance being serialized
            
        Returns:
            dict: Dictionary containing essay data, corrections, and score
        """
        return obj.formatted_data
