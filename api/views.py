from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.permissions import AllowAny
from buildings.models import Flat, Charge, Payment, Garage, Notification
from api.serializers import (
    FlatSerializer,
    ChargeSerializer,
    PaymentSerializer,
    GarageSerializer,
    NotificationSerializer,
    CustomTokenObtainPairSerializer,
)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshView(TokenRefreshView):
    pass


class LoginView(APIView):
    permission_classes = [AllowAny]

    @csrf_exempt
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
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
