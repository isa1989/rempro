import re
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseNotAllowed
from django.db.models.functions import ExtractMonth, ExtractYear
from django.db.models import Sum
from django.utils import timezone
from django.http import HttpResponseNotFound
from django.template.loader import render_to_string
from django.forms import formset_factory
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.db.models import Count, Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DeleteView, UpdateView, View
from django.views.generic.edit import FormView
from django.contrib.auth.views import LoginView as BaseLoginView, LogoutView
from django.views.generic.detail import DetailView
from django.urls import reverse_lazy
from buildings.utils import get_weather_data
from django.views.generic.edit import CreateView
from datetime import timedelta

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
    Charge,
    Garage,
    CarPlate,
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
    CarPlateForm,
    BuildingCreationForm,
    ExpenseForm,
    GarageForm,
)
from django.contrib.auth.decorators import login_required


def flat_autocomplete(request):
    q = request.GET.get("q", "")
    building_id = request.GET.get("building_id")
    flats = Flat.objects.filter(
        Q(name__icontains=q) | Q(resident__phone_number__icontains=q),
        building_id=building_id,
    )
    results = [{"id": flat.id, "text": flat.name} for flat in flats]
    return JsonResponse({"results": results})


def flat_autocomplete_sec(request):
    building_id = request.GET.get("building_id")
    flats = Flat.objects.filter(building_id=building_id)
    results = [{"id": flat.id, "text": flat.name} for flat in flats]
    return JsonResponse({"results": results})


def section_autocomplete(request):
    building_id = request.GET.get("building_id")
    sections = Section.objects.filter(building_id=building_id)
    results = [{"id": section.id, "text": section.name} for section in sections]
    return JsonResponse({"results": results})


def building_autocomplete(request):
    q = request.GET.get("q", "")
    branch_id = request.GET.get("branch_id")
    buildings = Building.objects.filter(name__icontains=q, branch_id=branch_id)
    results = [{"id": building.id, "text": building.name} for building in buildings]
    return JsonResponse({"results": results})


def charge_detail(request):
    charge_id = request.GET.get("charge_id")
    if charge_id:
        charge = Charge.objects.get(id=charge_id)
        return JsonResponse({"amount": charge.amount})
    else:
        return JsonResponse({"amount": None})


def charge_autocomplete(request):
    flat_id = request.GET.get("flat_id")
    charges = Charge.objects.filter(
        flat_id=flat_id,
        is_paid=False,
    )
    results = [
        {"id": charge.id, "text": f"{charge.service.name} - {charge.amount}"}
        for charge in charges
    ]

    return JsonResponse({"results": results})


class DashboardView(LoginRequiredMixin, View):
    login_url = "/login/"
    template_name = "dashboard.html"

    def get(self, request, *args, **kwargs):
        user = self.request.user
        one_month_ago = timezone.now() - timedelta(days=30)
        if user.is_superuser:
            branch_count = Branch.objects.filter(owner=user).count()
            building_count = Building.objects.filter(branch__owner=user).count()
            section_count = Section.objects.filter(building__branch__owner=user).count()
            flat_count = Flat.objects.filter(building__branch__owner=user).count()
            resident_count = (
                User.objects.filter(flat__building__branch__owner=user, resident=True)
                .distinct()
                .count()
            )
            payment_count = Payment.objects.filter(
                flat__building__branch__owner=user
            ).count()
            delayed_resident = User.objects.filter(
                flat__building__branch__owner=user,
                flat__balance__lt=0,
                resident=True,
            ).count()
            total_expenses = (
                Expense.objects.filter(outcome_date__gte=one_month_ago).aggregate(
                    total=Sum("price")
                )["total"]
                or 0
            )
        elif user.commandant:
            user_buildings = user.building.all()
            branch_count = 0
            building_count = Building.objects.filter(commandant=user).count()
            section_count = Section.objects.filter(
                building__in=user.building.all()
            ).count()
            flat_count = Flat.objects.filter(building__in=user_buildings).count()
            resident_count = (
                User.objects.filter(flat__building__in=user_buildings, resident=True)
                .distinct()
                .count()
            )
            payment_count = Payment.objects.filter(
                flat__building__in=user_buildings
            ).count()
            delayed_resident = User.objects.filter(
                flat__building__in=user_buildings, resident=True
            ).count()
            total_expenses = (
                Expense.objects.filter(
                    building__in=user_buildings, outcome_date__gte=one_month_ago
                ).aggregate(total=Sum("price"))["total"]
                or 0
            )
        else:
            branch_count = 0
            building_count = 0
            section_count = 0
            flat_count = 0
            resident_count = 0
            payment_count = 0
            delayed_resident = 0
            total_expenses = 0
        context = {
            "page_title": "Dashboard",
            "breadcrumbs": [
                {"title": "Ana səhifə", "url": reverse("dashboard")},
            ],
            "branch_count": branch_count,
            "building_count": building_count,
            "section_count": section_count,
            "flat_count": flat_count,
            "resident_count": resident_count,
            "payment_count": payment_count,
            "delayed_resident": delayed_resident,
            "total_expenses": total_expenses,
            "user_name": request.user.username,
            "is_superuser": request.user.is_superuser,
        }
        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context


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
        return redirect("/login/")


class UserProfileView(DetailView):
    model = User
    template_name = "user_profile.html"
    context_object_name = "user"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            {"title": "Binalar", "url": reverse("buildings")},
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
        """
        Return the queryset of branches filtered by user type.
        """
        user = self.request.user
        if user.is_superuser:
            return Branch.objects.filter(owner=user).annotate(
                commandant_count=Count("buildings__commandant", distinct=True),
                building_count=Count("buildings", distinct=True),
                camera_count=Count("cameras", distinct=True),
            )
        else:
            return Branch.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add is_superuser status to context
        context["is_superuser"] = self.request.user.is_superuser
        context["user_name"] = self.request.user.username
        for branch in context["branches"]:
            branch.has_buildings = branch.building_count > 0
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
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
        ]
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
        CameraFormSet = formset_factory(CameraForm, extra=1)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
        ]
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
            branch = form.save(commit=False)
            branch.owner = request.user  # Set the owner to the current user
            branch.save()

            for camera_form in formset:
                if camera_form.cleaned_data:
                    Camera.objects.create(
                        url=camera_form.cleaned_data.get("url"),
                        description=camera_form.cleaned_data.get("description"),
                        branch=branch,
                    )
            messages.success(request, f"{branch} yaradıldı!")
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
        buildings = Building.objects.filter(branch_id=branch_id)
        users = User.objects.filter(
            building__in=buildings,
            commandant=True,
        ).distinct()
        return users

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        branch_id = self.kwargs["branch_id"]
        context["branch"] = Branch.objects.get(id=branch_id)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            {"title": "Binalar", "url": reverse("buildings")},
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
        response = super().form_valid(form)
        branch_id = self.kwargs.get("branch_id")
        branch = get_object_or_404(Branch, id=branch_id)

        # Seçilen binaları komendantın binalarına ekle
        selected_buildings = form.cleaned_data.get("buildings", [])
        for building in selected_buildings:
            building.commandant.add(self.object)

        self.object.is_staff = True
        self.object.commandant = True
        self.object.save()

        messages.success(
            self.request, f"{self.object.username} adlı komendant oluşturuldu!"
        )
        return response

    def get_success_url(self):
        # Redirect to a list view or another appropriate URL after successful creation
        branch_id = self.kwargs.get("branch_id")
        return reverse_lazy("commandant-list", kwargs={"branch_id": branch_id})


class ComendantDeleteView(LoginRequiredMixin, DeleteView):
    login_url = "/login/"
    model = User

    def post(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(
            self.request, f"{self.object.username} adlı komendant silindi!"
        )
        return response

    def get_success_url(self):
        branch_id = self.kwargs.get("branch_id")
        return reverse_lazy("commandant-list", kwargs={"branch_id": branch_id})


class BuildingListView(LoginRequiredMixin, ListView):
    login_url = "/login/"
    model = Building
    template_name = "buildings.html"
    context_object_name = "buildings"

    def get_queryset(self):
        user = self.request.user
        branch_id = self.kwargs.get("branch_id")
        if user.is_superuser:
            branch_id = user.branch.values_list("id", flat=True)
        elif user.commandant:
            branch_id = user.building.first().branch.id
            return Building.objects.filter(
                branch_id=branch_id, commandant=user
            ).annotate(
                flat_count=Count("flat", distinct=True),
                section_count=Count("section", distinct=True),
                users_count=Count("flat__resident", distinct=True),
            )
        return Building.objects.filter(branch_id__in=branch_id).annotate(
            flat_count=Count("flat", distinct=True),
            section_count=Count("section", distinct=True),
            users_count=Count("flat__resident", distinct=True),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        branch_id = self.kwargs.get("branch_id")
        if user.is_superuser:
            branch_id = user.branch.values_list("id", flat=True).last()
        elif user.commandant:
            branch_id = user.building.first().branch.id

        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            # {"title": "Binalar", "url": reverse("buildings")},
        ]
        context["branch_id"] = branch_id
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context


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
        messages.success(self.request, f"{self.object.name} adlı bina yaradıldı!")

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
        user = self.request.user  # Başlangıçta boş queryset

        if user.is_superuser:
            queryset = Section.objects.filter(building__branch__owner=user)
        elif user.commandant:
            queryset = Section.objects.filter(
                building__in=Building.objects.filter(commandant=user)
            )

        building_id = self.kwargs.get("building_id")
        if building_id:
            queryset = queryset.filter(building_id=building_id)

        name = self.request.GET.get("name")
        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            {"title": "Binalar", "url": reverse("buildings")},
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context


class SectionsCreateView(LoginRequiredMixin, CreateView):
    login_url = "/login/"
    form_class = SectionForm
    template_name = "add_section.html"
    success_url = reverse_lazy("section-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["building_id"] = self.kwargs.get("building_id")
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            {"title": "Binalar", "url": reverse("buildings")},
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        Log.objects.create(
            action="CREATE",
            model_name="Section",
            object_id=self.object.id,
            user=self.request.user,
            details=f"Blok yaradıldı: {self.object.name}",
            timestamp=timezone.now(),
        )
        messages.success(self.request, f"{self.object.name} bloku yaradıldı!")
        return response


class FlatListView(LoginRequiredMixin, ListView):
    login_url = "/login/"
    model = Flat
    form = FlatForm
    template_name = "flat.html"
    context_object_name = "flats"
    paginate_by = 50

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            queryset = Flat.objects.filter(building__branch__owner=user).distinct()
        if user.commandant:
            queryset = Flat.objects.filter(
                building__in=Building.objects.filter(commandant=user)
            ).distinct()
        building_id = self.request.GET.get("building")
        section_id = self.request.GET.get("section")
        min_square_metres = self.request.GET.get("min_square_metres")
        max_square_metres = self.request.GET.get("max_square_metres")
        name = self.request.GET.get("name")
        phone = self.request.GET.get("phone")
        if building_id:
            queryset = queryset.filter(building_id=building_id)
        if section_id:
            queryset = queryset.filter(section_id=section_id)
        if min_square_metres:
            queryset = queryset.filter(square_metres__gte=min_square_metres)
        if max_square_metres:
            queryset = queryset.filter(square_metres__lte=max_square_metres)
        if name:
            queryset = queryset.filter(name__icontains=name)
        if phone:
            queryset = queryset.filter(resident__phone_number__contains=phone)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_superuser:
            user_branches = Branch.objects.filter(owner=user)
            buildings = Building.objects.filter(branch__in=user_branches)
        if user.commandant:
            buildings = Building.objects.filter(commandant=user)
        context["buildings"] = buildings
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            {"title": "Binalar", "url": reverse("buildings")},
        ]
        # building_id = self.kwargs["building_id"]
        # building = get_object_or_404(Building, id=building_id)
        # context["building_id"] = building.id
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        # context["sections"] = Section.objects.filter(building_id=building_id)
        return context


class FlatCreateView(LoginRequiredMixin, CreateView):
    login_url = "/login/"
    model = Flat
    form_class = FlatForm
    template_name = "add_flat.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            {"title": "Binalar", "url": reverse("buildings")},
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        Log.objects.create(
            action="CREATE",
            model_name="Flat",
            object_id=self.object.id,
            user=self.request.user,
            details=f"Mənzil yaradıldı: {self.object.name}",
            timestamp=timezone.now(),
        )
        messages.success(self.request, f"{self.object.name} mənzili yaradıldı!")
        return response

    def get_success_url(self):
        return reverse_lazy(
            "flat-list",
        )


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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        if user.is_superuser:
            context["branches"] = Branch.objects.filter(owner=user)
        elif user.commandant:
            buildings = Building.objects.filter(commandant=user)
            context["branches"] = Branch.objects.filter(
                buildings__in=buildings
            ).distinct()
        else:
            context["branches"] = Branch.objects.none()
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            {"title": "Xidmətlər", "url": reverse("services")},
        ]
        context["user_name"] = user.username
        context["is_superuser"] = user.is_superuser
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
        messages.success(self.request, f"{self.object.name} yaradıldı!")
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
        flat = get_object_or_404(Flat, id=flat_id)
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
        context["services_with_values"] = [
            {"service": service, "value": round(service.price * flat.square_metres)}
            for service in context["services"]
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

        return redirect(reverse("flat-list"))

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


class ChargeListView(LoginRequiredMixin, ListView):
    model = Charge
    template_name = "charge_list.html"  # Create this template
    context_object_name = "debts"
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            user_branches = Branch.objects.filter(owner=user)
            user_buildings = Building.objects.filter(branch__in=user_branches)
            return Charge.objects.filter(
                flat__building__in=user_buildings, is_paid=False
            ).distinct()

        if user.commandant:
            user_buildings = Building.objects.filter(commandant=user)
            return Charge.objects.filter(
                flat__building__in=user_buildings, is_paid=False
            ).distinct()

        return Charge.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context


class ExpenseListView(LoginRequiredMixin, ListView):
    login_url = "/login/"
    model = Expense
    template_name = "expense_list.html"
    context_object_name = "expenses"
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            user_branches = Branch.objects.filter(owner=user)
            return Expense.objects.filter(branch__in=user_branches).distinct()

        if user.commandant:
            user_buildings = Building.objects.filter(commandant=user)
            return Expense.objects.filter(building__in=user_buildings).distinct()

        return Expense.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("buildings")},
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context


class ExpenseCreateView(LoginRequiredMixin, CreateView):
    login_url = "/login/"
    model = Expense
    form_class = ExpenseForm
    template_name = "add_expense.html"
    success_url = reverse_lazy("expense-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("buildings")},
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        Log.objects.create(
            action="CREATE",
            model_name="Expense",
            object_id=self.object.id,
            user=self.request.user,
            details=f"Xərc yaradıldı: {self.object.name}",
            timestamp=timezone.now(),
        )
        messages.success(self.request, f"{self.object.name} yaradıldı!")
        return response


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

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            user_branches = Branch.objects.filter(owner=user)
            user_buildings = Building.objects.filter(branch__in=user_branches)
            return Payment.objects.filter(flat__building__in=user_buildings).distinct()

        if user.commandant:
            user_buildings = Building.objects.filter(commandant=user)
            return Payment.objects.filter(flat__building__in=user_buildings).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context


class PaymentCreateView(CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = "payment_form.html"
    success_url = "/payments/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            {"title": "Ödənişlər", "url": reverse("payment-list")},
        ]
        user = self.request.user
        if user.is_superuser:
            user_branches = Branch.objects.filter(owner=user)
            context["buildings"] = Building.objects.filter(branch__in=user_branches)
        elif user.commandant:
            context["buildings"] = Building.objects.filter(commandant=user)
        else:
            context["buildings"] = Building.objects.none()
        context["user_name"] = user.username
        context["is_superuser"] = user.is_superuser
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        if user.is_superuser:
            user_branches = Branch.objects.filter(owner=user)
            buildings = Building.objects.filter(branch__in=user_branches)
            form.fields["building"].queryset = buildings
        elif user.commandant:
            buildings = Building.objects.filter(commandant=user)
            form.fields["building"].queryset = buildings
        else:
            form.fields["building"].queryset = Building.objects.none()
        return form

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
        form.instance.user = self.request.user
        response = super().form_valid(form)
        charge_id = form.instance.charge.id if form.instance.charge else None
        if charge_id:
            Charge.objects.filter(id=charge_id).update(is_paid=True)
        else:
            flat = form.instance.flat
            flat.balance += form.cleaned_data["amount"]
            flat.save()
        Log.objects.create(
            action="CREATE",
            model_name="Payment",
            object_id=self.object.id,
            user=self.request.user,
            details=f"Ödəniş yaradıldı: {self.object.flat}-{round(self.object.amount, 1)} manat",
            timestamp=timezone.now(),
        )
        messages.success(
            self.request, f"{form.instance.flat} mənzili üçün ödəniş yaradıldı!"
        )
        return response


class PaymentChartView(ListView):
    model = Payment
    template_name = "payment_chart.html"
    context_object_name = "payments"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payment_data = (
            Payment.objects.annotate(month=ExtractMonth("date"))
            .annotate(year=ExtractYear("date"))
            .values("year", "month")
            .annotate(total=Sum("amount"))
            .order_by("year", "month")
        )
        labels = []
        data_points = []
        if payment_data:
            for data in payment_data:
                label = f"{data['month']:02d}/{data['year']}"
                labels.append(label)
                data_points.append(float(data["total"]))

            start_year = payment_data[0]["year"]
            end_year = payment_data.last()["year"]
            all_months = {
                f"{month:02d}/{year}": 0
                for month in range(1, 13)
                for year in range(start_year, end_year + 1)
            }

            for entry in zip(labels, data_points):
                month_label, value = entry
                all_months[month_label] = value
            labels = list(all_months.keys())
            data_points = list(all_months.values())
        else:
            start_year = timezone.now().year
            end_year = start_year
            labels = [
                f"{month:02d}/{year}"
                for year in range(start_year, end_year + 1)
                for month in range(1, 13)
            ]
            data_points = [0] * 12

        context["is_superuser"] = self.request.user.is_superuser
        context["breadcrumbs"] = [
            {"title": "Ana Sayfa", "url": reverse("branches")},
        ]
        context["labels"] = labels
        context["data_points"] = data_points
        context["user_name"] = self.request.user.username

        return context


class ResidentListView(ListView):
    login_url = "/login/"
    model = User
    form = ResidentForm
    template_name = "residents.html"
    context_object_name = "residents"

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            queryset = User.objects.filter(
                flat__building__branch__owner=user
            ).distinct()
        if user.commandant:
            queryset = User.objects.filter(
                flat__building__in=Building.objects.filter(commandant=user)
            ).distinct()
        building_id = self.request.GET.get("building")
        section_id = self.request.GET.get("section")
        flatname = self.request.GET.get("flatname")
        phone = self.request.GET.get("phone")
        negative_balance = self.request.GET.get("negative_balance")
        if building_id:
            queryset = queryset.filter(flat__building_id=building_id)

        if section_id:
            queryset = queryset.filter(flat__section_id=section_id)
        if flatname:
            queryset = queryset.filter(flat__name=flatname)
        if phone:
            queryset = queryset.filter(phone_number__contains=phone)
        if negative_balance:
            queryset = queryset.filter(flat__balance__lt=0)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # building_id = self.kwargs.get("building_id")
        # branch_id = self.kwargs.get("branch_id")
        if user.is_superuser:
            user_branches = Branch.objects.filter(owner=user)
            buildings = Building.objects.filter(branch__in=user_branches)
        if user.commandant:
            buildings = Building.objects.filter(commandant=user)
        context["buildings"] = buildings
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            {"title": "Binalar", "url": reverse("buildings")},
        ]
        context["is_superuser"] = self.request.user.is_superuser
        context["user_name"] = self.request.user.username
        return context


class ResidentCreateView(CreateView):
    form_class = ResidentForm
    template_name = "add_resident.html"
    success_url = reverse_lazy("all-residents")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        user.resident = True
        user.save()
        flat = form.cleaned_data.get("flat")
        try:
            flat = Flat.objects.get(id=flat.id)
            flat.resident = form.instance
            flat.save()
        except Flat.DoesNotExist:
            messages.error(self.request, f"Flat with name {flat} does not exist.")
            return redirect(self.get_success_url())
        messages.success(self.request, f"{user.username} adlı sakin əlavə edildi!")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            {"title": "Binalar", "url": reverse("buildings")},
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context


class ResidentDeleteView(LoginRequiredMixin, DeleteView):
    login_url = "/login/"
    model = User
    context_object_name = "resident"
    success_url = reverse_lazy("all-residents")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse_lazy("branches")},
            {"title": "Xidmətlər", "url": reverse_lazy("all-residents")},
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context

    def form_valid(self, form):
        object = self.get_object()
        response = super().form_valid(form)
        Log.objects.create(
            action="DELETE",
            model_name="User",
            object_id=object.id,
            user=self.request.user,
            details=f"Sakin silindi: {self.object.username}",
            timestamp=timezone.now(),
        )
        messages.success(
            self.request, f"{self.object.username} adlı sakin əlavə silindi!"
        )
        return response


class GarageListView(LoginRequiredMixin, ListView):
    login_url = "/login/"
    model = Garage
    template_name = "garage_list.html"
    context_object_name = "garages"

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Garage.objects.filter(building__branch__owner=user).annotate(
                car_plate_count=Count("carplate")
            )
        elif user.commandant:
            return Garage.objects.filter(
                building__in=Building.objects.filter(commandant=user)
            ).annotate(car_plate_count=Count("carplate"))
        return Garage.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse_lazy("branches")},
            {"title": "Xidmətlər", "url": reverse_lazy("all-residents")},
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context


class GarageDetailView(LoginRequiredMixin, DetailView):
    model = Garage
    template_name = "garage_detail.html"
    context_object_name = "garage"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = BranchForm(instance=self.object)
        context["is_superuser"] = self.request.user.is_superuser
        context["user_name"] = self.request.user.username
        return context


class GarageEditView(LoginRequiredMixin, UpdateView):
    model = Garage
    form_class = GarageForm
    template_name = "garage_edit.html"
    success_url = reverse_lazy("garage-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = GarageForm(instance=self.object)
        context["is_superuser"] = self.request.user.is_superuser
        context["user_name"] = self.request.user.username
        return context


class GarageCreateView(CreateView):
    model = Garage
    form_class = GarageForm
    template_name = "garage_form.html"
    success_url = reverse_lazy("garage-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse_lazy("branches")},
            {"title": "Qaraj əlavə et", "url": reverse_lazy("garage-add")},
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context


class CarPlateListView(LoginRequiredMixin, ListView):
    login_url = "/login/"
    model = CarPlate
    template_name = "carplate_list.html"
    context_object_name = "carplates"

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return CarPlate.objects.filter(garage__building__branch__owner=user)
        return CarPlate.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse_lazy("branches")},
            {"title": "Qarajlar", "url": reverse_lazy("garage-list")},
        ]
        context["garage_id"] = self.kwargs.get("garage_id")
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context


class CarPlateAddView(LoginRequiredMixin, CreateView):
    model = CarPlate
    form_class = CarPlateForm
    template_name = "carplate_add.html"
    success_url = reverse_lazy("carplate-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse_lazy("branches")},
            {"title": "Maşın Nömrələri", "url": reverse_lazy("carplate-list")},
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context


class CarPlateDeleteView(LoginRequiredMixin, DeleteView):
    login_url = "/login/"
    model = CarPlate
    context_object_name = "carplate"
    success_url = reverse_lazy("carplate-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse_lazy("branches")},
            {"title": "Araba Plakaları", "url": reverse_lazy("carplate-list")},
        ]
        return context

    def form_valid(self, form):
        object = self.get_object()
        response = super().form_valid(form)
        Log.objects.create(
            action="DELETE",
            model_name="CarPlate",
            object_id=object.id,
            user=self.request.user,
            details=f"Maşın nömrəsi silindi: {self.object.plate}",
            timestamp=timezone.now(),
        )
        messages.success(self.request, f"{self.object.plate} silindi!")
        return response


class LogListView(ListView):
    model = Log
    template_name = "log_list.html"
    context_object_name = "logs"
    ordering = ["-timestamp"]
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            # user_branches = Branch.objects.filter(owner=user)
            # queryset = Log.objects.filter(branch__in=user_branches)
            return (
                Log.objects.filter(user__branch__owner=user)
                .distinct()
                .order_by("-timestamp")
            )

        if user.commandant:
            queryset = Log.objects.filter(commandant=user)
            return queryset

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


class NewsCreateView(LoginRequiredMixin, CreateView):
    login_url = "/login/"
    model = News
    form_class = NewsForm
    template_name = "news_form.html"
    success_url = reverse_lazy("news-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"title": "Ana səhifə", "url": reverse("branches")},
            {"title": "Xəbərlər", "url": reverse("news-list")},
        ]
        context["user_name"] = self.request.user.username
        context["is_superuser"] = self.request.user.is_superuser
        return context

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
        messages.success(self.request, f"{self.object.title} yaradıldı!")
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

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


def custom_404_view(request, exception=None):
    context = {
        "user_name": request.user.username,
        "is_superuser": request.user.is_superuser,
    }
    content = render_to_string("error-404.html", context)
    return HttpResponseNotFound(content)


def get_weather(request):
    from .utils import get_weather_data

    city_id = "587084"  # Default city ID for Baku
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        # Handle AJAX request
        try:
            weather_data = get_weather_data(city_id)
            return JsonResponse(weather_data)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    # Handle regular page request
    try:
        weather_data = get_weather_data(city_id)
        context = {"city": city_id, "weather": weather_data}
    except:
        context = {"city": city_id}

    return render(request, "weather.html", context)
