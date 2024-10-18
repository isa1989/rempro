from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from buildings.models import Flat, Charge, Payment, Garage, Notification
from api.serializers import (
    FlatSerializer,
    ChargeSerializer,
    PaymentSerializer,
    GarageSerializer,
    NotificationSerializer,
)


class FlatListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        flats = Flat.objects.filter(resident=request.user)
        serializer = FlatSerializer(flats, many=True)
        return Response(serializer.data)


class ChargeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            flat = Flat.objects.get(id=id, resident=request.user)
            charges = Charge.objects.filter(flat=flat)
            serializer = ChargeSerializer(charges, many=True)
            return Response(serializer.data)
        except Flat.DoesNotExist:
            return Response(
                {"error": "Flat not found or you do not have access to it."}, status=404
            )


class AllChargesListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        charges = Charge.objects.filter(flat__resident=request.user)
        serializer = ChargeSerializer(charges, many=True)
        return Response(serializer.data)


class PaymentsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = Payment.objects.filter(flat__resident=request.user)
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)


class GaragesListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        garages = Garage.objects.filter(building__branch__owner=request.user)
        serializer = GarageSerializer(garages, many=True)
        return Response(serializer.data)


class NotificationsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)


class NotificationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            notification = Notification.objects.get(id=id, user=request.user)
            if request.query_params.get("read", "false").lower() == "true":
                notification.is_read = True
                notification.save()

            serializer = NotificationSerializer(notification)
            return Response(serializer.data)
        except Notification.DoesNotExist:
            return Response({"error": "Notification not found."}, status=404)


class UnreadNotificationsCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({"count": count})


class MarkAllNotificationsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True
        )
        return Response({"message": "All notifications marked as read"})
