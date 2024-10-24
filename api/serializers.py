from rest_framework import serializers
from buildings.models import Flat, Charge, Payment, Garage, Notification
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    phone_number = serializers.CharField(required=True)

    @classmethod
    def validate(cls, attrs):
        phone_number = attrs.get("phone_number")
        password = attrs.get("password")

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "Bu telefon numarası ile kullanıcı bulunamadı."
            )

        if not user.check_password(password):
            raise serializers.ValidationError("Geçersiz şifre.")

        attrs["user"] = user
        return attrs


class FlatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flat
        fields = ["id", "name", "building", "section", "square_metres", "balance"]


class ChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Charge
        fields = [
            "id",
            "flat",
            "service",
            "amount",
            "is_paid",
            "created_at",
            "is_paid_at",
        ]


class ChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Charge
        fields = [
            "id",
            "flat",
            "service",
            "amount",
            "is_paid",
            "created_at",
            "is_paid_at",
        ]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "flat", "charge", "amount", "date"]


class GarageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Garage
        fields = ["id", "number", "building"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "title", "message", "timestamp", "is_read", "user_id"]
