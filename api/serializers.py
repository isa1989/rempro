from rest_framework import serializers
from buildings.models import Flat, Charge, Payment, Garage, Notification


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
