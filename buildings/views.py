import re
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseNotAllowed
from django.db.models import Sum
from django.utils import timezone
from django.forms import formset_factory
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.db.models import Count, Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DeleteView, UpdateView
from django.views.generic.edit import FormView
from django.contrib.auth.views import LoginView as BaseLoginView, LogoutView
from django.views.generic.detail import DetailView
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .models import (
    Building,
    Section,
    Flat,
    Service,
    Branch,
    User,
    Expense,
    Payment,
    Log,
    News,
    Camera,
)
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
    NewsForm,
    CameraForm,
    BuildingCreationForm,
)
from django.contrib.auth.decorators import login_required


def flat_autocomplete(request):
    q = request.GET.get("q", "")
    building_id = request.GET.get("building_id")
    # Filter flats by name or user's phone number, and match the building
    flats = Flat.objects.filter(
        Q(name__icontains=q) | Q(user__phone_number__icontains=q),
        building_id=building_id,
    )
    results = [{"id": flat.id, "text": flat.name} for flat in flats]
    return JsonResponse({"results": results})


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


class UserProfileView(DetailView):
    model = User
    template_name = "user_profile.html"
    context_object_name = "user"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            {"title": "Sakinlər", "url": reverse("all-residents")},
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context


class BranchListView(LoginRequiredMixin, ListView):
    login_url = "/login/"
    model = Branch
    template_name = "branch_list.html"  # Replace with your actual template
    context_object_name = "branches"

    def get_queryset(self):
        # branch_id = self.request.user.branch_id
        return Branch.objects.annotate(
            commandant_count=Count(
                "users", filter=Q(users__commandant=True), distinct=True
            ),
            building_count=Count("buildings", distinct=True),
            camera_count=Count("cameras", distinct=True),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add is_superuser status to context
        context["is_superuser"] = self.request.user.is_superuser
        context["user_name"] = self.request.user.username
        return context


class BranchDetailView(DetailView):
    model = Branch
    template_name = "branch_detail.html"
    context_object_name = "branch"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = BranchForm(instance=self.object)
        context["is_superuser"] = self.request.user.is_superuser
        context["user_name"] = self.request.user.username
        return context


class BranchUpdateView(UpdateView):
    model = Branch
    form_class = BranchForm
    template_name = "branch_edit.html"
    context_object_name = "branch"

    def get_success_url(self):
        return reverse_lazy("branch-detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_superuser"] = self.request.user.is_superuser
        context["user_name"] = self.request.user.username
        return context


class BranchCreateView(CreateView):
    model = Branch
    form_class = BranchForm
    template_name = "add_branch.html"
    success_url = reverse_lazy("branches")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        CameraFormSet = formset_factory(
            CameraForm, extra=1
        )  # Set the initial number of forms
        context["cameras_formset"] = CameraFormSet()
        context["is_superuser"] = self.request.user.is_superuser
        context["user_name"] = self.request.user.username
        return context

    def post(self, request, *args, **kwargs):
        form = BranchForm(request.POST)
        CameraFormSet = formset_factory(
            CameraForm, extra=1
        )  # Set the initial number of forms
        formset = CameraFormSet(request.POST, request.FILES)

        if form.is_valid() and formset.is_valid():
            branch = form.save()
            for camera_form in formset:
                if camera_form.cleaned_data:
                    Camera.objects.create(
                        url=camera_form.cleaned_data.get("url"),
                        description=camera_form.cleaned_data.get("description"),
                        branch=branch,
                    )
            return redirect(self.success_url)
        return self.render_to_response(
            self.get_context_data(form=form, cameras_formset=formset)
        )


class CommandantListView(LoginRequiredMixin, ListView):
    login_url = "/login/"
    model = User
    template_name = "commandant.html"
    context_object_name = "commandants"

    def get_queryset(self):
        branch_id = self.kwargs["branch_id"]
        return User.objects.filter(branch__in=[branch_id], commandant=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        branch_id = self.kwargs["branch_id"]
        context["branch"] = Branch.objects.get(id=branch_id)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
        ]
        context["is_superuser"] = self.request.user.is_superuser
        context["user_name"] = self.request.user.username
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
        context["is_superuser"] = self.request.user.is_superuser
        context["user_name"] = self.request.user.username
        return context

    def form_valid(self, form):
        # Save the instance first to get an ID assigned
        response = super().form_valid(form)
        # Retrieve the branch using branch_id from URL
        branch_id = self.kwargs.get("branch_id")
        branch = get_object_or_404(Branch, id=branch_id)
        # Add the branch to the instance's many-to-many field
        self.object.branch.add(branch)
        # Set other fields
        self.object.is_staff = True
        self.object.commandant = True
        self.object.save()  # Save the changes to the instance
        return response

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
        branch_id = self.kwargs.get("branch_id")
        if not branch_id:
            branch_id = self.request.user.branch.values_list("id", flat=True).last()
        return Building.objects.filter(branch_id=branch_id).annotate(
            flat_count=Count("flat", distinct=True),
            section_count=Count("section", distinct=True),
            users_count=Count("flat__user", distinct=True),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        branch_id = self.kwargs.get("branch_id")
        if not branch_id:
            branch_id = self.request.user.branch.values_list("id", flat=True).last()

        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            # {"title": "Binalar", "url": reverse("buildings")},
        ]
        context["branch_id"] = branch_id
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context


# class BranchDetailView(DetailView):
#     model = Branch
#     template_name = "branch_detail.html"
#     context_object_name = "branch"


class BuildingCreateView(LoginRequiredMixin, CreateView):
    login_url = "/login/"
    model = Building
    form_class = BuildingForm
    template_name = "add_building.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        branch_id = self.kwargs.get("branch_id")
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            {"title": "Binalar", "url": reverse("buildings")},
        ]
        context["branch_id"] = branch_id
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context

    def form_valid(self, form):
        branch_id = self.kwargs.get("branch_id")
        if branch_id:
            form.instance.branch = get_object_or_404(Branch, pk=branch_id)

        # Call the parent form_valid method to save the object
        response = super().form_valid(form)

        # Log the creation of the new building
        Log.objects.create(
            action="CREATE",
            model_name="Building",
            object_id=self.object.id,
            user=self.request.user,
            details=f"Bina yaradıldı: {self.object.name}",
            timestamp=timezone.now(),
        )

        return response

    def get_success_url(self):
        branch_id = self.kwargs.get("branch_id")
        return reverse_lazy("buildings-list", kwargs={"branch_id": branch_id})


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
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
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
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context

    def form_valid(self, form):
        building_id = self.kwargs["building_id"]
        building = get_object_or_404(Building, id=building_id)
        form.instance.building = building
        response = super().form_valid(form)
        Log.objects.create(
            action="CREATE",
            model_name="Section",
            object_id=self.object.id,
            user=self.request.user,
            details=f"Blok yaradıldı: {self.object.name}",
            timestamp=timezone.now(),
        )
        return response

    def get_success_url(self):
        building_id = self.kwargs["building_id"]
        return reverse_lazy("section-list", kwargs={"building_id": building_id})


class FlatListView(LoginRequiredMixin, ListView):
    login_url = "/login/"
    model = Flat
    template_name = "flat.html"
    context_object_name = "flats"
    paginate_by = 50

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        building_id = self.kwargs["building_id"]
        kwargs["building_id"] = building_id
        return kwargs

    def get_queryset(self):
        queryset = super().get_queryset()
        building_id = self.kwargs.get("building_id")
        if building_id is not None:
            queryset = queryset.filter(building_id=building_id)

        # Filtering based on GET parameters
        section_id = self.request.GET.get("section")
        min_square_metres = self.request.GET.get("min_square_metres")
        max_square_metres = self.request.GET.get("max_square_metres")
        name = self.request.GET.get("name")

        if section_id:
            queryset = queryset.filter(section_id=section_id)
        if min_square_metres and max_square_metres:
            queryset = queryset.filter(
                square_metres__gte=min_square_metres,
                square_metres__lte=max_square_metres,
            )
        elif min_square_metres:
            queryset = queryset.filter(square_metres__gte=min_square_metres)
        elif max_square_metres:
            queryset = queryset.filter(square_metres__lte=max_square_metres)
        if name:
            queryset = queryset.filter(name=name)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            # {"title": "Binalar", "url": reverse("buildings")},
        ]
        building_id = self.kwargs["building_id"]
        building = get_object_or_404(Building, id=building_id)
        context["building_id"] = building.id
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        context["sections"] = Section.objects.filter(building_id=building_id)
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
            # {"title": "Binalar", "url": reverse("buildings")},
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context

    def form_valid(self, form):
        building_id = self.kwargs["building_id"]
        building = get_object_or_404(Building, id=building_id)
        form.instance.building = building
        response = super().form_valid(form)
        Log.objects.create(
            action="CREATE",
            model_name="Flat",
            object_id=self.object.id,
            user=self.request.user,
            details=f"Mənzil yaradıldı: {self.object.name}",
            timestamp=timezone.now(),
        )
        return response

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
        context["is_superuser"] = self.request.user.is_superuser
        return context


class ServiceDetailView(LoginRequiredMixin, DetailView):
    login_url = "/login/"
    model = Service
    template_name = "service_detail.html"
    context_object_name = "service"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            {"title": "Xidmətlər", "url": reverse("services")},
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context


class ServiceUpdateView(LoginRequiredMixin, UpdateView):
    login_url = "/login/"
    model = Service
    template_name = "service_form.html"
    fields = ["field1", "field2", "field3"]  # Specify the fields you want to edit
    context_object_name = "service"
    success_url = reverse_lazy("services")  # Redirect after successful update

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            {"title": "Xidmətlər", "url": reverse("services")},
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
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
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        Log.objects.create(
            action="CREATE",
            model_name="Service",
            object_id=self.object.id,
            user=self.request.user,
            details=f"Xidmət yaradıldı: {self.object.name}",
            timestamp=timezone.now(),
        )
        return response


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
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser

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
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
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
        context["is_superuser"] = self.request.user.is_superuser
        return context


class PaymentCreateView(CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = "payment_form.html"
    success_url = "/payments/"  # Redirect after success

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["buildings"] = Building.objects.all()
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
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

    def form_valid(self, form):
        # Set the user to the current user before saving the form
        form.instance.user = self.request.user
        return super().form_valid(form)


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
        building_id = self.kwargs.get("building_id")
        branch_id = self.kwargs.get("branch_id")

        if building_id:
            queryset = User.objects.filter(building_id=building_id, resident=True)
        else:
            queryset = User.objects.filter(resident=True)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        building_id = self.kwargs.get("building_id")
        branch_id = self.kwargs.get("branch_id")

        if building_id:
            context["building"] = get_object_or_404(Building, id=building_id)

        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
        ]
        context["is_superuser"] = self.request.user.is_superuser
        context["user_name"] = self.request.user.username
        return context


class ResidentCreateView(CreateView):
    form_class = ResidentForm
    template_name = "add_resident.html"
    success_url = reverse_lazy("resident-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        building_id = self.kwargs.get("building_id")
        kwargs["building_id"] = building_id
        return kwargs

    def form_valid(self, form):
        building_id = self.kwargs.get("building_id")
        building = get_object_or_404(Building, id=building_id)
        form.instance.resident = True
        form.instance.branch = building.branch
        form.instance.building = building
        response = super().form_valid(form)

        flat = form.cleaned_data.get("flat")
        try:
            flat = Flat.objects.get(id=flat)  # Adjust if your field is different
            flat.user = form.instance
            flat.save()
        except Flat.DoesNotExist:
            messages.error(self.request, f"Flat with name {flat} does not exist.")
            return redirect(self.get_success_url())

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["building"] = get_object_or_404(Building, id=self.kwargs["building_id"])
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("buildings")},
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context

    def get_success_url(self):
        # Redirect to a list view or another appropriate URL after successful creation
        building_id = self.kwargs.get("building_id")
        return reverse_lazy("resident-list", kwargs={"building_id": building_id})


class LogListView(ListView):
    model = Log
    template_name = "log_list.html"
    context_object_name = "logs"
    ordering = ["-timestamp"]
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context


class NewsListView(ListView):
    model = News
    template_name = "news_list.html"
    context_object_name = "news_list"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context


class NewsCreateView(CreateView):
    model = News
    form_class = NewsForm
    template_name = "news_form.html"
    success_url = reverse_lazy("news-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        Log.objects.create(
            action="CREATE",
            model_name="News",
            object_id=self.object.id,
            user=self.request.user,
            details=f"Xəbər əlavə edildi: {self.object.title}",
            timestamp=timezone.now(),
        )
        return response


class NewsDetailView(DetailView):
    model = News
    template_name = "news_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context


class ServiceEditView(LoginRequiredMixin, UpdateView):
    login_url = "/login/"
    model = Service
    form_class = ServiceForm
    template_name = "service_edit.html"
    context_object_name = "service"

    def get_success_url(self):
        return reverse_lazy("service-detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse_lazy("branches")},
            {"title": "Xidmətlər", "url": reverse_lazy("services")},
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context


class ServiceDeleteView(LoginRequiredMixin, DeleteView):
    login_url = "/login/"
    model = Service
    template_name = "service_confirm_delete.html"
    context_object_name = "service"
    success_url = reverse_lazy("services")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse_lazy("branches")},
            {"title": "Xidmətlər", "url": reverse_lazy("services")},
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context

    def form_valid(self, form):
        object = self.get_object()
        response = super().form_valid(form)
        Log.objects.create(
            action="DELETE",
            model_name="Service",
            object_id=object.id,
            user=self.request.user,
            details=f"Xidmət silindi: {self.object.name}",
            timestamp=timezone.now(),
        )
        return response


class NewsUpdateView(UpdateView):
    model = News
    form_class = NewsForm
    template_name = "edit_news.html"
    success_url = reverse_lazy("news-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            {"title": "Xəbərlər", "url": reverse("news-list")},
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context


class NewsDeleteView(DeleteView):
    model = News
    success_url = reverse_lazy("news-list")

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)  # Perform delete on GET request

    def post(self, request, *args, **kwargs):
        object = self.get_object()
        response = super().post(request, *args, **kwargs)
        Log.objects.create(
            action="DELETE",
            model_name="News",
            object_id=object.id,
            user=self.request.user,
            details=f"Xəbər silindi: {self.object.title}",
            timestamp=timezone.now(),
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context


class CameraListView(ListView):
    model = Camera
    template_name = "camera_list.html"  # Replace with your actual template
    context_object_name = "cameras"

    def get_queryset(self):
        branch_id = self.kwargs["branch_id"]
        branch = get_object_or_404(Branch, id=branch_id)
        return Camera.objects.filter(branch=branch)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
        ]
        branch_id = self.kwargs["branch_id"]
        context["branch"] = get_object_or_404(Branch, id=branch_id)
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context


class CameraCreateView(LoginRequiredMixin, CreateView):
    login_url = "/login/"
    model = Camera
    form_class = CameraForm
    template_name = "camera_form.html"

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
        ]
        context["is_superuser"] = self.request.user.is_superuser
        context["user_name"] = self.request.user.username
        return context

    def form_valid(self, form):
        # Save the instance first to get an ID assigned
        response = super().form_valid(form)
        # Retrieve the branch using branch_id from URL
        branch_id = self.kwargs.get("branch_id")
        branch = get_object_or_404(Branch, id=branch_id)
        # Add the branch to the instance's many-to-many field
        self.object.branch = branch

        self.object.save()  # Save the changes to the instance
        return response

    def get_success_url(self):
        # Redirect to a list view or another appropriate URL after successful creation
        branch_id = self.kwargs.get("branch_id")
        return reverse_lazy("camera-list", kwargs={"branch_id": branch_id})


class CameraDeleteView(LoginRequiredMixin, DeleteView):
    model = Camera

    def get_success_url(self):
        branch_id = self.kwargs.get("branch_id")
        return reverse_lazy(
            "branches",
        )


class CameraUpdateView(UpdateView):
    model = Camera
    form_class = CameraForm
    template_name = "camera_edit.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["branch_id"] = self.kwargs.get("branch_id")
        return kwargs

    def get_success_url(self):
        branch_id = self.kwargs.get("branch_id")
        return reverse_lazy("camera-list", kwargs={"branch_id": branch_id})


def generate_flats(sequence, count):
    """Generate flat names based on the given sequence and count."""
    flats = []
    sequence_pattern = re.findall(r"\D+", sequence)  # Find all non-digit parts
    number_pattern = re.findall(r"\d+", sequence)  # Find all digit parts

    if number_pattern:
        start = int(number_pattern[0])
        for i in range(count):
            flat_name = sequence.replace(str(start), str(start + i), 1)
            flats.append(flat_name)
    else:
        for i in range(count):
            flats.append(sequence.replace(sequence[-1], chr(ord(sequence[-1]) + i), 1))

    return flats


def generate_flats(flat_sequence, floor_count):
    # Ensure flat_sequence is an integer
    flats = [str(i) for i in range(1, flat_sequence + 1)]
    return flats


def create_building(request):
    if request.method == "POST":
        form = BuildingCreationForm(request.POST)
        if form.is_valid():
            floor_count = form.cleaned_data["floor_count"]
            sector_count = form.cleaned_data["sector_count"]
            flat_sequence = int(
                form.cleaned_data["flat_sequence"]
            )  # Convert to integer
            branch = form.cleaned_data["branch"]

            # Create the building
            building = Building.objects.create(
                name="Dynamic Building",  # Adjust as needed
                address="123 Dynamic St",  # Adjust as needed
                branch=branch,
            )

            # Create sections and flats
            flat_counter = 1  # Initialize a counter for unique flat names

            for sector_num in range(1, sector_count + 1):
                section_name = f"Sector {sector_num}"
                section = Section.objects.create(building=building, name=section_name)

                for floor in range(1, floor_count + 1):
                    # Generate the number of flats based on the flat_sequence
                    for _ in range(flat_sequence):
                        Flat.objects.create(
                            building=building,
                            section=section,
                            name=str(flat_counter),  # Assign a unique name
                            square_metres=50.00,  # Adjust as needed
                        )
                        flat_counter += 1  # Increment the counter for the next flat

            return redirect("buildings")  # Redirect to a list or detail view

    else:
        form = BuildingCreationForm()

    return render(request, "create_building.html", {"form": form})
