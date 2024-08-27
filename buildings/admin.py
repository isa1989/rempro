from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Building, Section, Flat, Service, Branch, User, Expense, Payment


class CustomUserAdmin(UserAdmin):
    model = User
    list_display = [
        "username",
        "email",
        "commandant",
        "resident",
        "branch",
        "is_staff",
        "is_superuser",
    ]
    list_filter = ["commandant", "branch", "is_staff", "is_superuser"]
    fieldsets = UserAdmin.fieldsets + (
        (
            None,
            {
                "fields": (
                    "phone_number",
                    "commandant",
                    "branch",
                    "resident",
                    "building",
                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            None,
            {
                "fields": (
                    "commandant",
                    "branch",
                    "resident",
                )
            },
        ),
    )


admin.site.register(User, CustomUserAdmin)
admin.site.register(Branch)
admin.site.register(Building)
admin.site.register(Section)
admin.site.register(Flat)
admin.site.register(Service)
admin.site.register(Expense)
admin.site.register(Payment)
