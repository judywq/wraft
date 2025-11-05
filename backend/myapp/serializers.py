from rest_framework import serializers

from .models import EssayEvaluation


class BriefEssayEvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EssayEvaluation
        fields = ["id", "status", "error", "essay_text", "score", "created_at"]


class EssayEvaluationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EssayEvaluation
        fields = ["essay_prompt", "essay_text"]


class EssayEvaluationRetrieveSerializer(serializers.ModelSerializer):
    evaluation = serializers.SerializerMethodField()

    class Meta:
        model = EssayEvaluation
        fields = ["id", "status", "error", "created_at", "updated_at", "evaluation"]

    def get_evaluation(self, obj):
        return obj.formatted_data
