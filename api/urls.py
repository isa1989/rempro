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
    path("api/flats", FlatListView.as_view(), name="flat-list"),
    path("api/flats/<int:id>/charges", ChargeListView.as_view(), name="flat-charges"),
    # -----------------------------CHARGE-----------------------------------------------
    path("api/charges/all", AllChargesListView.as_view(), name="all-charges"),
    # -----------------------------PAYMENT-----------------------------------------------
    path("api/payments", PaymentsListView.as_view(), name="payments-list"),
    # -----------------------------GARAGE-----------------------------------------------
    path("api/garages", GaragesListView.as_view(), name="garages-list"),
    # -----------------------------NOTİFİCATİON-----------------------------------------------
    path(
        "api/notifications", NotificationsListView.as_view(), name="notifications-list"
    ),
    path(
        "api/notifications/<int:id>",
        NotificationDetailView.as_view(),
        name="notification-detail",
    ),
    path(
        "api/notifications/<int:id>",
        NotificationDetailView.as_view(),
        name="notification-detail",
    ),
    path(
        "api/notifications/count",
        UnreadNotificationsCountView.as_view(),
        name="unread-notifications-count",
    ),
    path(
        "api/notifications/read",
        MarkAllNotificationsReadView.as_view(),
        name="mark-all-notifications-read",
    ),
]
