from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Building,
    Section,
    Flat,
    Service,
    Branch,
    User,
    Expense,
    Payment,
    News,
    Camera,
)


class CustomUserAdmin(UserAdmin):
    model = User
    list_display = [
        "username",
        "email",
        "commandant",
        "resident",
        "display_branch",  # Use a custom method for displaying related fields
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

    def display_branch(self, obj):
        """Custom method to display related branches."""
        return (
            ", ".join([branch.name for branch in obj.branch.all()])
            if obj.branch.exists()
            else "None"
        )

    display_branch.short_description = "Branch"


admin.site.register(User, CustomUserAdmin)
admin.site.register(Camera)
admin.site.register(Branch)
admin.site.register(Building)
admin.site.register(Section)
admin.site.register(Flat)
admin.site.register(Service)
admin.site.register(Expense)
admin.site.register(Payment)
admin.site.register(News)
