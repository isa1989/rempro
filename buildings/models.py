from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser, Group, Permission


def validate_day(value):
    if value < 1 or value > 31:
        raise ValidationError("Day must be between 1 and 31.")


class Branch(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    whatsapp_link = models.URLField(blank=True, null=True)
    telegram = models.URLField(blank=True, null=True)
    camera_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Filial"
        verbose_name_plural = "Filial"


class Service(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name="Service Name",
        help_text="Enter the name of the service",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Price",
        help_text="Enter the price of the service",
    )
    invoice_day = models.IntegerField(
        verbose_name="Invoice Day",
        help_text="Enter the day of the month when the invoice is issued",
        validators=[validate_day],
    )

    class Meta:
        verbose_name = "Xidmətlər"
        verbose_name_plural = "Xidmətlər"

    def __str__(self):
        return self.name


class Building(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="buildings"
    )

    class Meta:
        ordering = ["id"]
        verbose_name = "Binalar"
        verbose_name_plural = "Binalar"

    def __str__(self):
        return self.name


class Section(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    name = models.CharField(max_length=15)

    class Meta:
        ordering = ["id"]
        verbose_name = "Bloklar"
        verbose_name_plural = "Bloklar"

    def __str__(self):
        return self.name


class User(AbstractUser):
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="users",
        blank=True,
        null=True,
    )
    commandant = models.BooleanField(default=False)
    resident = models.BooleanField(default=False)
    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_set",
        blank=True,
        help_text="The groups this user belongs to.",
        related_query_name="user",
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_permissions_set",
        blank=True,
        help_text="Specific permissions for this user.",
        related_query_name="user",
    )

    def __str__(self):
        return self.username

    def set_password(self, raw_password):
        super().set_password(raw_password)

    class Meta:
        ordering = ["id"]
        verbose_name = "İstifadəçilər"
        verbose_name_plural = "İstifadəçilər"


class Flat(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    services = models.ManyToManyField(
        Service, related_name="flats", blank=True, verbose_name="Services"
    )
    balance = models.DecimalField(
        default=0,
        max_digits=10,
        decimal_places=2,
    )
    square_metres = models.DecimalField(max_digits=8, decimal_places=2)
    is_rent = models.BooleanField(default=False)
    tenant_document = models.FileField(upload_to="documents/", blank=True, null=True)
    owner_document = models.FileField(upload_to="documents/")

    class Meta:
        ordering = ["id"]
        verbose_name = "Mənzillər"
        verbose_name_plural = "Mənzillər"

    def __str__(self):
        return self.name

    @property
    def services_count(self):
        return self.services.count()


class Expense(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    outcome_date = models.DateField()
    outcome_document = models.FileField(upload_to="documents/", blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["id"]
        verbose_name = "Xərclər"
        verbose_name_plural = "Xərclər"


class Payment(models.Model):
    building = models.ForeignKey(
        Building,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Bina",
        help_text="Ödəniş edilən bina",
    )
    flat = models.ForeignKey(
        Flat,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Mənzil",
        help_text="Ödəniş edilən mənzil",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Məbləğ",
        help_text="Ödənişin məbləği",
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="payments",
        blank=True,
        null=True,
        verbose_name="Xidmət",
        help_text="Ödəmə ilə əlaqəli xidmət (əgər varsa)",
    )
    date = models.DateField(verbose_name="Tarix", help_text="Ödənişin tarixi")

    def __str__(self):
        return f"Payment of {self.amount} on {self.date} for {self.flat}"

    class Meta:
        ordering = ["-date"]
        verbose_name = "Ödəniş"
        verbose_name_plural = "Ödəniş"
