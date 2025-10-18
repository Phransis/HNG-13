import logging
import requests
from datetime import datetime
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

CATFACT_URL = "https://catfact.ninja/fact"
CATFACT_TIMEOUT = float(getattr(settings, "CATFACT_TIMEOUT", 2.5))

def _utc_iso8601_z():
    # Return UTC ISO 8601 with millisecond precision and 'Z' suffix
    now = datetime.utcnow()
    ts = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    return ts

class MeView(APIView):
    """
    GET /me
    Returns the profile object and a cat fact fetched from an external API.
    """

    def get(self, request):
        # Load user config from environment (via Django settings)
        email = getattr(settings, "PROFILE_EMAIL", None) or "duofrancis11@gmail.com"
        name = getattr(settings, "PROFILE_FULL_NAME", None) or "Francis Duo"
        stack = getattr(settings, "PROFILE_STACK", None) or "Python/Django"

        # Fetch cat fact
        fact_text = None
        try:
            resp = requests.get(CATFACT_URL, timeout=CATFACT_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            fact_text = data.get("fact") if isinstance(data, dict) else None
            if not fact_text:
                raise ValueError("No 'fact' in response")
        except Exception as e:
            logger.warning("Failed to fetch cat fact: %s", e)
            fact_text = "Could not fetch a cat fact at the moment."

        payload = {
            "status": "success",
            "user": {
                "email": email,
                "name": name,
                "stack": stack,
            },
            "timestamp": _utc_iso8601_z(),
            "fact": fact_text,
        }

        return Response(payload, status=status.HTTP_200_OK)
