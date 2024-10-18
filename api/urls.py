from django.urls import path
from api.views import (
    FlatListView,
    ChargeListView,
    AllChargesListView,
    PaymentsListView,
    GaragesListView,
    NotificationsListView,
    NotificationDetailView,
    UnreadNotificationsCountView,
    MarkAllNotificationsReadView,
)

urlpatterns = [
    # -----------------------------FLAT-----------------------------------------------
    path("flats", FlatListView.as_view(), name="flat-list"),
    path("flats/<int:id>/charges", ChargeListView.as_view(), name="flat-charges"),
    # -----------------------------CHARGE-----------------------------------------------
    path("charges/all", AllChargesListView.as_view(), name="all-charges"),
    # -----------------------------PAYMENT-----------------------------------------------
    path("payments", PaymentsListView.as_view(), name="payments-list"),
    # -----------------------------GARAGE-----------------------------------------------
    path("garages", GaragesListView.as_view(), name="garages-list"),
    # -----------------------------NOTİFİCATİON-----------------------------------------------
    path("notifications", NotificationsListView.as_view(), name="notifications-list"),
    path(
        "notifications/<int:id>",
        NotificationDetailView.as_view(),
        name="notification-detail",
    ),
    path(
        "notifications/<int:id>",
        NotificationDetailView.as_view(),
        name="notification-detail",
    ),
    path(
        "notifications/count",
        UnreadNotificationsCountView.as_view(),
        name="unread-notifications-count",
    ),
    path(
        "notifications/read",
        MarkAllNotificationsReadView.as_view(),
        name="mark-all-notifications-read",
    ),
]
