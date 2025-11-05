from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LLMModel
from .serializers import LLMModelSerializer


class ActiveModelsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active_models = LLMModel.get_active_models()
        serializer = LLMModelSerializer(
            active_models,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)
