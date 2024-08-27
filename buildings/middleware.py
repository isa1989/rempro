from django.utils.deprecation import MiddlewareMixin
from .models import Log

from django.utils import timezone


class LogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # For simplicity, log only authenticated user actions
        if request.user.is_authenticated:
            request._start_time = timezone.now()

    def process_response(self, request, response):
        if hasattr(request, "_start_time"):
            duration = timezone.now() - request._start_time
            action = "ACCESS"
            model_name = "N/A"
            object_id = None
            details = (
                f"Method: {request.method}, Path: {request.path}, Duration: {duration}"
            )

            # Log access
            Log.objects.create(
                user=request.user,
                action=action,
                model_name=model_name,
                object_id=object_id,
                details=details,
            )
        return response
