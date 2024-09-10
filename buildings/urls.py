from django.urls import path
from . import views

urlpatterns = [
    # --------------------------- HOME -----------------------------
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("login/", views.LoginView.as_view(), name="login"),
    # --------------------------- AUTH -----------------------------
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    # --------------------------- PROFILE -----------------------------
    path("user/<int:pk>/", views.UserProfileView.as_view(), name="user_profile"),
    # --------------------------- BRANCH -----------------------------
    path("branches/", views.BranchListView.as_view(), name="branches"),
    path("branch/<int:pk>/", views.BranchDetailView.as_view(), name="branch-detail"),
    path("branch/<int:pk>/edit/", views.BranchUpdateView.as_view(), name="branch-edit"),
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
    path("flats/<int:building_id>/", views.FlatListView.as_view(), name="flat-list"),
    path(
        "flat/add/<int:building_id>/",
        views.FlatCreateView.as_view(),
        name="flat-add",
    ),
    # --------------------------- BUILDINGS -----------------------------
    path("buildings/", views.BuildingListView.as_view(), name="buildings"),
    path(
        "branch/<int:branch_id>/buildings/",
        views.BuildingListView.as_view(),
        name="buildings-list",
    ),
    # path(
    #     "building/<int:branch_id>/",
    #     views.BranchDetailView.as_view(),
    #     name="building-detail",
    # ),
    path(
        "building/add/<int:branch_id>/",
        views.BuildingCreateView.as_view(),
        name="building-add",
    ),
    path("create-building/", views.create_building, name="create_building"),
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
    # ----------------------Services-------------------------------
    path("services/", views.ServicesListView.as_view(), name="services"),
    path(
        "service/<int:pk>/detail/",
        views.ServiceDetailView.as_view(),
        name="service-detail",
    ),
    path(
        "service/<int:pk>/edit/", views.ServiceEditView.as_view(), name="service-edit"
    ),
    path(
        "service/<int:pk>/delete/",
        views.ServiceDeleteView.as_view(),
        name="service_delete",
    ),
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
    path("residents/", views.ResidentListView.as_view(), name="all-residents"),
    path(
        "residents/add/<int:building_id>/",
        views.ResidentCreateView.as_view(),
        name="resident-add",
    ),
    path(
        "resident/<int:pk>/delete/",
        views.ResidentDeleteView.as_view(),
        name="resident-delete",
    ),
    path(
        "add-resident/",
        views.ResidentCustomCreateView.as_view(),
        name="add-custom-resident",
    ),
    # -------------------------- RESIDENTS -------------------------------
    path("flat-autocomplete/", views.flat_autocomplete, name="flat-autocomplete"),
    path(
        "autocomplete/buildings/",
        views.building_autocomplete,
        name="building_autocomplete",
    ),
    # -------------------------- LOGS -------------------------------
    path("logs/", views.LogListView.as_view(), name="log_list"),
    # -------------------------- NEWS -------------------------------
    path("news", views.NewsListView.as_view(), name="news-list"),
    path("news-create/", views.NewsCreateView.as_view(), name="news-create"),
    path("news/<int:pk>/", views.NewsDetailView.as_view(), name="news-detail"),
    path("news/<int:pk>/edit/", views.NewsUpdateView.as_view(), name="news-edit"),
    path("news/<int:pk>/delete/", views.NewsDeleteView.as_view(), name="news-delete"),
    # -------------------------- CAMERA -------------------------------
    path(
        "branch/<int:branch_id>/cameras/",
        views.CameraListView.as_view(),
        name="camera-list",
    ),
    path(
        "branch/<int:branch_id>/cameras/add/",
        views.CameraCreateView.as_view(),
        name="camera-add",
    ),
    path(
        "camera/<int:pk>/delete/",
        views.CameraDeleteView.as_view(),
        name="camera-delete",
    ),
    path(
        "branch/<int:branch_id>/camera/<int:pk>/edit/",
        views.CameraUpdateView.as_view(),
        name="camera-edit",
    ),
    # -------------------------- WEATHER -------------------------------
    path("weather/", views.get_weather, name="get_weather"),
]
