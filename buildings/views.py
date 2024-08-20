import calendar
from django.utils import timezone
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseNotAllowed
from django.db.models import Sum
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.db.models import Count, Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DeleteView
from django.views.generic.edit import FormView
from django.contrib.auth.views import LoginView as BaseLoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .models import Building, Section, Flat, Service, Branch, User, Expense, Payment
from .forms import (
    BuildingForm,
    SectionForm,
    FlatForm,
    ServiceForm,
    AddServiceForm,
    BranchForm,
    CommandantForm,
    PaymentForm,
    ResidentForm,
)
from django.contrib.auth.decorators import login_required


class LoginView(BaseLoginView):
    template_name = "login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        # Check if the user is authenticated and is either a superuser or commandant
        if user.is_superuser or user.commandant:
            return super().form_valid(form)
        else:
            return HttpResponseForbidden("You are not authorized to access this page.")

    def get_success_url(self):
        user = self.request.user
        if user.is_superuser:
            return reverse_lazy("branches")
        else:
            return reverse_lazy("buildings")


class UserLogoutView(LogoutView):

    def get(self, request, *args, **kwargs):
        # Ensure GET request can handle logout if necessary
        return HttpResponseNotAllowed(["POST"])

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        # Redirect to a custom URL after logout
        return redirect("/")


class BranchListView(LoginRequiredMixin, ListView):
    login_url = "/login/"
    model = Branch
    template_name = "branch_list.html"  # Replace with your actual template
    context_object_name = "branches"

    def get_queryset(self):
        # Annotate each branch with the count of commandants
        return Branch.objects.annotate(
            commandant_count=Count("users", filter=Q(users__commandant=True))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add is_superuser status to context
        context["is_superuser"] = self.request.user.is_superuser
        context["user_name"] = self.request.user.username
        return context


class BranchCreateView(LoginRequiredMixin, CreateView):
    login_url = "/login/"
    model = Branch
    form_class = BranchForm
    template_name = "add_branch.html"  # Replace with your actual template
    success_url = reverse_lazy("branches")


class CommandantListView(LoginRequiredMixin, ListView):
    login_url = "/login/"
    model = User
    template_name = "commandant.html"
    context_object_name = "commandants"

    def get_queryset(self):
        branch_id = self.kwargs["branch_id"]
        return User.objects.filter(branch_id=branch_id, commandant=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        branch_id = self.kwargs["branch_id"]
        context["branch"] = Branch.objects.get(id=branch_id)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
        ]
        return context


class CommandantCreateView(LoginRequiredMixin, CreateView):
    login_url = "/login/"
    model = User
    form_class = CommandantForm
    template_name = "add_commandant.html"

    def get_form_kwargs(self):
        # Add the branch_id to the form kwargs if needed
        kwargs = super().get_form_kwargs()
        branch_id = self.kwargs.get("branch_id")
        kwargs["branch_id"] = branch_id
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        branch_id = self.kwargs.get("branch_id")
        branch = get_object_or_404(Branch, id=branch_id)
        context["branch"] = branch
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            {"title": "Filiallar", "url": reverse("branches")},
            {
                "title": "Yeni Komendant",
                "url": reverse("commandant-add", kwargs={"branch_id": branch_id}),
            },
        ]
        return context

    def form_valid(self, form):
        # Assign the branch to the new commandant and mark them as a commandant
        branch_id = self.kwargs.get("branch_id")
        branch = get_object_or_404(Branch, id=branch_id)
        form.instance.branch = branch
        form.instance.is_staff = True
        form.instance.commandant = True
        return super().form_valid(form)

    def get_success_url(self):
        # Redirect to a list view or another appropriate URL after successful creation
        branch_id = self.kwargs.get("branch_id")
        return reverse_lazy("commandant-list", kwargs={"branch_id": branch_id})


class ComendantDeleteView(LoginRequiredMixin, DeleteView):
    login_url = "/login/"
    model = User

    def get_success_url(self):
        branch_id = self.kwargs.get("branch_id")
        return reverse_lazy("commandant-list", kwargs={"branch_id": branch_id})


class BuildingListView(LoginRequiredMixin, ListView):
    login_url = "/login/"
    model = Building
    template_name = "buildings.html"
    context_object_name = "buildings"

    def get_queryset(self):
        return Building.objects.annotate(
            flat_count=Count("flat", distinct=True),
            section_count=Count("section", distinct=True),
            users_count=Count("flat__user", distinct=True),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        branch_id = self.request.user.branch_id
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            {"title": "Binalar", "url": reverse("buildings")},
        ]
        context["branch_id"] = branch_id
        context["user_name"] = self.request.user.username
        return context


class BuildingCreateView(LoginRequiredMixin, CreateView):
    login_url = "/login/"
    model = Building
    form_class = BuildingForm
    template_name = "add_building.html"
    success_url = reverse_lazy("buildings")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        branch_id = self.kwargs.get("branch_id")
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            {"title": "Binalar", "url": reverse("buildings")},
        ]
        context["branch_id"] = branch_id
        return context

    def form_valid(self, form):
        branch_id = self.kwargs.get("branch_id")
        if branch_id:
            form.instance.branch = get_object_or_404(Branch, pk=branch_id)
        return super().form_valid(form)


class SectionListView(LoginRequiredMixin, ListView):
    login_url = "/login/"
    model = Section
    template_name = "section.html"
    context_object_name = "sections"

    def get_queryset(self):
        building_id = self.kwargs["building_id"]
        return Section.objects.filter(building_id=building_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            {"title": "Binalar", "url": reverse("buildings")},
        ]
        return context


class SectionsCreateView(LoginRequiredMixin, CreateView):
    login_url = "/login/"
    model = Section
    form_class = SectionForm
    template_name = "add_section.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        building_id = self.kwargs["building_id"]
        kwargs["building_id"] = building_id
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        building_id = self.kwargs["building_id"]
        building = get_object_or_404(Building, id=building_id)
        context["building"] = building
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            {"title": "Binalar", "url": reverse("buildings")},
        ]
        return context

    def form_valid(self, form):
        building_id = self.kwargs["building_id"]
        building = get_object_or_404(Building, id=building_id)
        form.instance.building = building
        return super().form_valid(form)

    def get_success_url(self):
        building_id = self.kwargs["building_id"]
        return reverse_lazy("section-list", kwargs={"building_id": building_id})


class FlatListView(LoginRequiredMixin, ListView):
    login_url = "/login/"
    model = Flat
    template_name = "flat.html"
    context_object_name = "flats"

    def get_queryset(self):
        building_id = self.kwargs["building_id"]
        return Flat.objects.filter(building_id=building_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            {"title": "Binalar", "url": reverse("buildings")},
        ]
        return context


class FlatCreateView(LoginRequiredMixin, CreateView):
    login_url = "/login/"
    model = Flat
    form_class = FlatForm
    template_name = "add_flat.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        building_id = self.kwargs["building_id"]
        kwargs["building_id"] = building_id
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        building_id = self.kwargs["building_id"]
        building = get_object_or_404(Building, id=building_id)
        context["building"] = building
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            {"title": "Binalar", "url": reverse("buildings")},
        ]
        return context

    def form_valid(self, form):
        building_id = self.kwargs["building_id"]
        building = get_object_or_404(Building, id=building_id)
        form.instance.building = building
        return super().form_valid(form)

    def get_success_url(self):
        building_id = self.kwargs["building_id"]
        return reverse_lazy("flat-list", kwargs={"building_id": building_id})


class ServicesListView(LoginRequiredMixin, ListView):
    login_url = "/login/"
    model = Service
    template_name = "service.html"
    context_object_name = "services"

    # def get_queryset(self):
    #     return Service.objects.annotate(
    #         flat_count=Count("flat", distinct=True),
    #         section_count=Count("section", distinct=True),
    #     )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            {"title": "Xidmətlər", "url": reverse("services")},
        ]
        context["user_name"] = self.request.user.username
        return context


class ServiceCreateView(LoginRequiredMixin, CreateView):
    login_url = "/login/"
    model = Service
    form_class = ServiceForm
    template_name = "add_service.html"
    success_url = reverse_lazy("services")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            {"title": "Xidmətlər", "url": reverse("services")},
        ]
        return context


class FlatServiceListView(LoginRequiredMixin, ListView):
    login_url = "/login/"
    model = Service
    template_name = "flat_services.html"
    context_object_name = "services"

    def get_queryset(self):
        flat_id = self.kwargs.get("flat_id")
        flat = get_object_or_404(Flat, id=flat_id)
        return flat.services.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        flat_id = self.kwargs.get("flat_id")
        context["flat"] = get_object_or_404(Flat, id=flat_id)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            {"title": "Binalar", "url": reverse("buildings")},
            {
                "title": "Flat Services",
                "url": reverse("flat-services", kwargs={"flat_id": flat_id}),
            },
        ]
        return context


class FlatAddServiceListView(LoginRequiredMixin, FormView):
    login_url = "/login/"
    template_name = "add_services_to_flat.html"
    form_class = AddServiceForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = get_object_or_404(Flat, id=self.kwargs["flat_id"])
        return kwargs

    def form_valid(self, form):
        flat = form.instance

        flat.services.set(form.cleaned_data["services"])
        return redirect(reverse("flat-list", kwargs={"building_id": flat.building.id}))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("buildings")},
        ]
        flat = get_object_or_404(Flat, id=self.kwargs["flat_id"])
        context["flat"] = flat
        return context


from django.db.models.functions import ExtractMonth, ExtractYear


class ExpenseChartView(ListView):
    model = Expense
    template_name = "expense_chart.html"
    context_object_name = "expenses"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Aggregate expenses by year and month
        expense_data = (
            Expense.objects.annotate(month=ExtractMonth("outcome_date"))
            .annotate(year=ExtractYear("outcome_date"))
            .values("year", "month")
            .annotate(total=Sum("price"))
            .order_by("year", "month")
        )

        # Prepare data for the chart
        stepcount = []
        if expense_data:
            for data in expense_data:
                # Create a label for each month with the year included
                label = f"{data['month']:02d}/{data['year']}"
                stepcount.append({"y": float(data["total"]), "label": label})

            # Ensure the stepcount data covers all months in the year
            all_months = {
                f"{month:02d}/{year}": 0
                for month in range(1, 13)
                for year in range(
                    expense_data[0]["year"], expense_data.last()["year"] + 1
                )
            }
            for entry in stepcount:
                month_label = entry["label"]
                if month_label in all_months:
                    all_months[month_label] = entry["y"]

            # Reformat stepcount to ensure all months are represented
            start_year = expense_data[0]["year"]
            end_year = expense_data.last()["year"]
            stepcount = [
                {"y": all_months[f"{month:02d}/{year}"], "label": f"{month:02d}/{year}"}
                for month in range(1, 13)
                for year in range(start_year, end_year + 1)
            ]
        else:
            # Handle the case where expense_data is empty
            start_year = 2024  # Default or current year
            end_year = 2024
            stepcount = [
                {"y": 0, "label": f"{month:02d}/{year}"}
                for month in range(1, 13)
                for year in range(start_year, end_year + 1)
            ]

        context["is_superuser"] = self.request.user.is_superuser
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
        ]
        context["stepcount"] = stepcount
        context["user_name"] = self.request.user.username

        return context


class PaymentListView(ListView):
    model = Payment
    template_name = "payment_list.html"
    context_object_name = "payments"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_name"] = self.request.user.username

        return context


class PaymentCreateView(CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = "payment_form.html"
    success_url = "/payments/"  # Redirect after success

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["buildings"] = Building.objects.all()
        return context

    def get(self, request, *args, **kwargs):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            building_id = request.GET.get("building_id")
            if building_id:
                flats = Flat.objects.filter(building_id=building_id)
            else:
                flats = Flat.objects.none()
            return JsonResponse({"flats": list(flats.values("id", "name"))})
        return super().get(request, *args, **kwargs)


class PaymentChartView(ListView):
    model = Payment
    template_name = "payment_chart.html"
    context_object_name = "payments"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Aggregate payments by year and month
        payment_data = (
            Payment.objects.annotate(month=ExtractMonth("date"))
            .annotate(year=ExtractYear("date"))
            .values("year", "month")
            .annotate(total=Sum("amount"))
            .order_by("year", "month")
        )

        # Prepare data for the chart
        stepcount = []
        if payment_data:
            for data in payment_data:
                # Create a label for each month with the year included
                label = f"{data['month']:02d}/{data['year']}"
                stepcount.append({"y": float(data["total"]), "label": label})

            # Ensure the stepcount data covers all months in the year
            start_year = payment_data[0]["year"]
            end_year = payment_data.last()["year"]
            all_months = {
                f"{month:02d}/{year}": 0
                for month in range(1, 13)
                for year in range(start_year, end_year + 1)
            }
            for entry in stepcount:
                month_label = entry["label"]
                if month_label in all_months:
                    all_months[month_label] = entry["y"]

            # Reformat stepcount to ensure all months are represented
            stepcount = [
                {"y": all_months[f"{month:02d}/{year}"], "label": f"{month:02d}/{year}"}
                for month in range(1, 13)
                for year in range(start_year, end_year + 1)
            ]
        else:
            # Handle the case where payment_data is empty
            start_year = 2024  # Default or current year
            end_year = 2024
            stepcount = [
                {"y": 0, "label": f"{month:02d}/{year}"}
                for month in range(1, 13)
                for year in range(start_year, end_year + 1)
            ]

        context["is_superuser"] = self.request.user.is_superuser
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
        ]
        context["stepcount"] = stepcount
        context["user_name"] = self.request.user.username
        return context


class ResidentListView(ListView):
    model = User
    template_name = "residents.html"
    context_object_name = "residents"

    def get_queryset(self):
        building_id = self.kwargs["building_id"]
        building = get_object_or_404(Building, id=building_id)
        return User.objects.filter(branch=building.branch, resident=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["building"] = get_object_or_404(Building, id=self.kwargs["building_id"])
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
        ]
        return context


class ResidentCreateView(CreateView):
    form_class = ResidentForm
    template_name = "add_resident.html"
    success_url = reverse_lazy("resident-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        building_id = self.kwargs["building_id"]
        kwargs["building_id"] = building_id
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["buildings"] = Building.objects.all()
        building_id = self.kwargs["building_id"]
        context["branch"] = Building.objects.get(id=building_id)
        return context

    # def get(self, request, *args, **kwargs):
    #     if request.headers.get("x-requested-with") == "XMLHttpRequest":
    #         building_id = request.GET.get("building_id")
    #         if building_id:
    #             flats = Flat.objects.filter(building_id=building_id)
    #         else:
    #             flats = Flat.objects.none()
    #         return JsonResponse({"flats": list(flats.values("id", "name"))})
    #     return super().get(request, *args, **kwargs)
