from django.urls import path
from . import views

urlpatterns = [
    # --------------------------- AUTH -----------------------------
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    # --------------------------- BRANCH -----------------------------
    path("", views.BranchListView.as_view(), name="branches"),
    path("branch/add/", views.BranchCreateView.as_view(), name="branch-add"),
    path(
        "branch/<int:branch_id>/commandants/",
        views.CommandantListView.as_view(),
        name="commandant-list",
    ),
    path(
        "commandant/add/<int:branch_id>/",
        views.CommandantCreateView.as_view(),
        name="commandant-add",
    ),
    path(
        "branch/<int:branch_id>/commandant/<int:pk>/delete/",
        views.ComendantDeleteView.as_view(),
        name="commandant-delete",
    ),
    # --------------------------- FLAT -----------------------------
    path(
        "flat/<int:flat_id>/services/",
        views.FlatServiceListView.as_view(),
        name="flat-services",
    ),
    # --------------------------- BUILDING -----------------------------
    path("buildings", views.BuildingListView.as_view(), name="buildings"),
    path(
        "building/add/<int:branch_id>/",
        views.BuildingCreateView.as_view(),
        name="building-add",
    ),
    path(
        "sections/<int:building_id>/",
        views.SectionListView.as_view(),
        name="section-list",
    ),
    path(
        "section/add/<int:building_id>/",
        views.SectionsCreateView.as_view(),
        name="section-add",
    ),
    path("flats/<int:building_id>/", views.FlatListView.as_view(), name="flat-list"),
    path(
        "flat/add/<int:building_id>/",
        views.FlatCreateView.as_view(),
        name="flat-add",
    ),
    # ----------------------Services-------------------------------
    path("services", views.ServicesListView.as_view(), name="services"),
    path("service/add/", views.ServiceCreateView.as_view(), name="service-add"),
    path(
        "flat/<int:flat_id>/services/",
        views.FlatServiceListView.as_view(),
        name="flat-services",
    ),
    path(
        "flat/<int:flat_id>/add-services/",
        views.FlatAddServiceListView.as_view(),
        name="flat-add-services",
    ),
    # -------------------------- Expense -------------------------------
    path("expenses/chart/", views.ExpenseChartView.as_view(), name="expense-chart"),
    # --------------------------- Payment -------------------------------
    path("payments/", views.PaymentListView.as_view(), name="payment-list"),
    path("payments/add/", views.PaymentCreateView.as_view(), name="payment-add"),
    path("payment-chart/", views.PaymentChartView.as_view(), name="payment-chart"),
    # -------------------------- RESIDENTS -------------------------------
    path(
        "building/<int:building_id>/residents/",
        views.ResidentListView.as_view(),
        name="resident-list",
    ),
    path(
        "residents/add/<int:flat_id>/",
        views.ResidentCreateView.as_view(),
        name="resident-add",
    ),
]
