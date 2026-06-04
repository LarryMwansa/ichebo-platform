from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import WaitlistEntry
from .serializers import WaitlistEntrySerializer
from .tasks import send_waitlist_confirmation, send_waitlist_notification


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@api_view(['POST'])
@permission_classes([AllowAny])
def waitlist_register(request):
    email = request.data.get('email', '').lower().strip()
    if email and WaitlistEntry.objects.filter(email=email).exists():
        return Response(
            {'status': 'already_registered'},
            status=status.HTTP_200_OK
        )

    serializer = WaitlistEntrySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    entry = serializer.save(ip_address=get_client_ip(request))

    send_waitlist_confirmation.delay(str(entry.id))
    send_waitlist_notification.delay(str(entry.id))

    return Response({'status': 'registered'}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def waitlist_health(request):
    return Response({'status': 'ok', 'app': 'waitlist'})
