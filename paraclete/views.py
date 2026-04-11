from django.core.cache import cache
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ParacleteDigestSerializer
from .service import build_digest


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@api_view(['GET'])
def health(request):
    return Response({'status': 'ok', 'app': 'paraclete'})


# ---------------------------------------------------------------------------
# Phase B — Digest (with cache)
# ---------------------------------------------------------------------------

class DigestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cache_key = f'paraclete_digest_{request.user.id}'
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)
        digest = build_digest(request.user)
        serializer = ParacleteDigestSerializer(digest)
        data = serializer.data
        cache.set(cache_key, data, 300)
        return Response(data)


# ---------------------------------------------------------------------------
# Phase C — Remaining endpoints
# ---------------------------------------------------------------------------

class RemindersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        digest = build_digest(request.user)
        from .serializers import ActivityCardSerializer
        return Response({
            'pending_reminders': ActivityCardSerializer(digest.pending_reminders, many=True).data
        })


class PromptView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        digest = build_digest(request.user)
        return Response({
            'discipline_prompt': digest.discipline_prompt,
            'prompt_pathway': digest.prompt_pathway,
        })


class SuggestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, record_id):
        return Response({'suggestions': [], 'method': 'deferred'})


class RespondView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({'status': 'ok'})
