from rest_framework import serializers

from .models import APIRequest
from .models import LLMModel


class LLMModelSerializer(serializers.ModelSerializer):
    used_quota = serializers.SerializerMethodField()
    daily_limit = serializers.IntegerField(source="quota_config.daily_limit")

    class Meta:
        model = LLMModel
        fields = [
            "id",
            "order",
            "is_default",
            "display_name",
            "used_quota",
            "daily_limit",
        ]

    def get_used_quota(self, obj):
        try:
            user = self.context["request"].user
        except (KeyError, AttributeError):
            return 0

        return obj.get_used_quota(user)


class APIRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIRequest
        fields = "__all__"
        read_only_fields = [
            "status",
            "created_at",
        ]
