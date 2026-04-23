import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_push_notification(user, title, body, data=None):
    """
    Sends a push notification to a single user via FCM.
    Requires user.fcm_token to be set.
    """
    if not user.fcm_token:
        logger.info(f"User {user.id} has no FCM token. Push skipped.")
        return None

    # Initialize Firebase if not already initialized
    if not firebase_admin._apps:
        try:
            # Look for service account path in settings (env variable recommended)
            cred_path = getattr(settings, 'FIREBASE_SERVICE_ACCOUNT_PATH', None)
            if cred_path:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            else:
                # Fallback to default credentials
                firebase_admin.initialize_app()
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin: {e}")
            return None

    # Construct the message
    # 'data' must be a dict of strings for FCM
    fcm_data = {}
    if data:
        for k, v in data.items():
            fcm_data[k] = str(v)

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=fcm_data,
        token=user.fcm_token,
    )

    try:
        response = messaging.send(message)
        logger.info(f"Successfully sent FCM message to {user.id}: {response}")
        return response
    except Exception as e:
        logger.error(f"FCM send error for user {user.id}: {e}")
        # Optionally handle stale tokens here (e.g., user.fcm_token = None)
        return None
