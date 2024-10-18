import re
from django.utils import timezone
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import RegexValidator


def validate_day(value):
    if value < 1 or value > 31:
        raise ValidationError("Day must be between 1 and 31.")


class User(AbstractUser):
    phone_number = models.CharField(
        max_length=13,
        blank=True,
        null=True,
    )
    commandant = models.BooleanField(default=False)
    resident = models.BooleanField(default=False)
    email = models.EmailField(unique=True, blank=True, null=True)
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


class Branch(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="branch")
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    whatsapp_link = models.URLField(blank=True, null=True)
    telegram = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Filial"
        verbose_name_plural = "Filial"


class Camera(models.Model):
    url = models.CharField(max_length=255, verbose_name="Kamera linki")
    description = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Kamera məzmunu"
    )
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="cameras", blank=True, null=True
    )

    def __str__(self):
        return self.url

    class Meta:
        verbose_name = "Camera"
        verbose_name_plural = "Camera"


class Service(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="service")
    name = models.CharField(
        max_length=255,
        verbose_name="Xidmətin adı",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Qiymət",
    )
    invoice_day = models.IntegerField(
        verbose_name="Ödəniş günü",
        validators=[validate_day],
    )
    is_active = models.BooleanField(default=True, verbose_name="aktiv")

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
    commandant = models.ManyToManyField(
        User, related_name="building", blank=True, verbose_name="Komendant"
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


class Flat(models.Model):
    resident = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name="flat", null=True, blank=True
    )
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, verbose_name="blok")
    name = models.CharField(max_length=255, verbose_name="ad")
    services = models.ManyToManyField(
        Service, related_name="flats", blank=True, verbose_name="Xidmətlər"
    )
    balance = models.DecimalField(
        default=0, max_digits=10, decimal_places=2, verbose_name="balans"
    )
    square_metres = models.DecimalField(
        max_digits=8, decimal_places=2, verbose_name="Sahəsi"
    )
    is_active = models.BooleanField(default=True)
    is_rent = models.BooleanField(default=False, verbose_name="Icarə")
    tenant_document = models.FileField(
        upload_to="documents/", blank=True, null=True, verbose_name="Icarəçi sənədi"
    )
    owner_document = models.FileField(
        upload_to="documents/", verbose_name="Sahibkar sənədi"
    )

    class Meta:
        ordering = ["id"]
        verbose_name = "Mənzillər"
        verbose_name_plural = "Mənzillər"

    def __str__(self):
        return self.name

    @property
    def services_count(self):
        return self.services.count()

    @property
    def rent_status(self):
        return "Bəli" if self.is_rent else "Xeyr"


class Expense(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    outcome_date = models.DateField()
    outcome_document = models.FileField(upload_to="documents/", blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    building = models.ForeignKey(
        Building,
        on_delete=models.CASCADE,
        related_name="expenses",
        blank=True,
        null=True,
        verbose_name="Bina",
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="expenses",
        blank=True,
        null=True,
        verbose_name="Filial",
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-outcome_date"]
        verbose_name = "Xərc"
        verbose_name_plural = "Xərclər"


class Charge(models.Model):
    flat = models.ForeignKey(
        Flat,
        on_delete=models.SET_NULL,
        related_name="fcharge",
        verbose_name="Mənzil",
        blank=True,
        null=True,
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        related_name="scharge",
        blank=True,
        null=True,
        verbose_name="Xidmət",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Məbləğ",
    )
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Borc {self.flat} - {self.amount}"

    class Meta:
        verbose_name = "Borc"
        verbose_name_plural = "Borclar"


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
    charge = models.ForeignKey(
        Charge,
        on_delete=models.CASCADE,
        related_name="payments",
        blank=True,
        null=True,
        verbose_name="Borc",
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(verbose_name="Tarix", help_text="Ödənişin tarixi")

    def __str__(self):
        return f"Payment of {self.amount} on {self.date} for {self.flat}"

    class Meta:
        ordering = ["-date"]
        verbose_name = "Ödəniş"
        verbose_name_plural = "Ödəniş"


class Garage(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    number = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.number

    class Meta:
        verbose_name = "Qaraj"
        verbose_name_plural = "Qarajlar"


class CarPlate(models.Model):
    name = models.CharField(max_length=200)
    plate = models.CharField(max_length=50, blank=True, null=True)
    garage = models.ForeignKey(Garage, on_delete=models.CASCADE)

    def __str__(self):
        return self.plate

    class Meta:
        verbose_name = "Maşın nömrəsi"
        verbose_name_plural = "Maşın nömrələri"


class Log(models.Model):
    ACTION_CHOICES = [
        ("CREATE", "Əlavə edildi"),
        ("UPDATE", "Dəyişdirildi"),
        ("DELETE", "Silindi"),
        ("ACCESS", "İcazə"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="logs")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50)
    object_id = models.PositiveIntegerField()
    timestamp = models.DateTimeField(default=timezone.now)
    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user} {self.action} {self.model_name} #{self.object_id} at {self.timestamp}"


class News(models.Model):
    building = models.ForeignKey(
        Building,
        on_delete=models.CASCADE,
        related_name="news",
        verbose_name="Bina",
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Xəbərlər"
        verbose_name_plural = "Xəbərlər"


class Notification(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )

    def __str__(self):
        return f"{self.title} - {self.user.username} ({self.timestamp})"

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Bildiriş"
        verbose_name_plural = "Bildirişlər"
