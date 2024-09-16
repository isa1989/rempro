from django import forms
from django.forms import inlineformset_factory
from .models import (
    Building,
    Section,
    Flat,
    Service,
    Branch,
    User,
    Payment,
    News,
    Camera,
    Expense,
)
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm


class BuildingForm(forms.ModelForm):
    class Meta:
        model = Building
        fields = ["name", "address"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Binanın adı"}
            ),
            "address": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Binanın adresi"}
            ),
        }


class BuildingCreationForm(forms.Form):
    floor_count = forms.IntegerField(label="Number of Floors", min_value=1)
    sector_count = forms.IntegerField(label="Number of Sectors", min_value=1)
    flat_sequence = forms.CharField(label="Flat Sequence", max_length=255)
    branch = forms.ModelChoiceField(queryset=Branch.objects.all(), label="Branch")


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ["building", "name"]

    building = forms.ModelChoiceField(
        queryset=Building.objects.all(),
        empty_label="Select Building",
        widget=forms.HiddenInput(),
    )
    name = forms.CharField(
        max_length=15,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Blokun adını yaz"}
        ),
    )

    def __init__(self, *args, **kwargs):
        building_id = kwargs.pop("building_id", None)  # Extract building_id
        super().__init__(*args, **kwargs)

        if building_id:
            # Filter sections based on building_id
            # self.fields["section"].queryset = Section.objects.filter(
            #     building_id=building_id
            # )
            # Set the initial value for building field
            self.initial["building"] = building_id
            self.fields["building"].widget.attrs.update({"value": building_id})
            for field in self.fields.values():
                field.label = ""

        # self.fields["owner_document"].required = False


class FlatForm(forms.ModelForm):
    building = forms.ModelChoiceField(
        queryset=Building.objects.all(),
        empty_label="Select Building",
        widget=forms.HiddenInput(),  # Hidden field for building ID
    )

    class Meta:
        model = Flat
        fields = [
            "building",
            "section",
            "name",
            "square_metres",
            "is_rent",
            "tenant_document",
            "owner_document",
            "services",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "square_metres": forms.NumberInput(attrs={"class": "form-control"}),
            "is_rent": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "tenant_document": forms.ClearableFileInput(
                attrs={"class": "form-control-file"}
            ),
            "owner_document": forms.ClearableFileInput(
                attrs={"class": "form-control-file"}
            ),
            "services": forms.SelectMultiple(attrs={"class": "form-control"}),
            "section": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        building_id = kwargs.pop("building_id", None)  # Extract building_id
        super().__init__(*args, **kwargs)

        if building_id:
            # Filter sections based on building_id
            self.fields["section"].queryset = Section.objects.filter(
                building_id=building_id
            )
            # Set the initial value for building field
            self.initial["building"] = building_id
            self.fields["building"].widget.attrs.update({"value": building_id})

        self.fields["owner_document"].required = False


class ServiceForm(forms.ModelForm):
    invoice_day = forms.IntegerField(
        min_value=1,
        max_value=31,
        label="Ödəniş günü",
        error_messages={
            "min_value": "Invoice day must be between 1 and 31.",
            "max_value": "Invoice day must be between 1 and 31.",
        },
    )

    class Meta:
        model = Service
        fields = ["name", "price", "invoice_day"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "price": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "invoice_day": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
        }


class AddServiceForm(ModelForm):
    class Meta:
        model = Flat
        fields = ["services"]

        widgets = {
            "services": forms.CheckboxSelectMultiple,  # You can use any widget here that fits your needs
        }


class CameraForm(forms.ModelForm):
    class Meta:
        model = Camera
        fields = ["url", "description"]
        widgets = {
            "url": forms.URLInput(attrs={"class": "form-control"}),
            "description": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        # Extract branch_id from kwargs if present
        self.branch_id = kwargs.pop("branch_id", None)
        super().__init__(*args, **kwargs)


class CameraFormSet(forms.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # You can add custom behavior here if needed


# Define the inline formset factory
CameraFormSetFactory = inlineformset_factory(
    Branch, Camera, form=CameraForm, formset=CameraFormSet, extra=1, can_delete=True
)


class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = [
            "name",
            "address",
            "email",
            "whatsapp_link",
            "telegram",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "whatsapp_link": forms.URLInput(attrs={"class": "form-control"}),
            "telegram": forms.URLInput(attrs={"class": "form-control"}),
        }
        labels = {
            "name": "Filial adı",
            "address": "Adress",
            "email": "Email Address",
            "whatsapp_link": "WhatsApp Link",
            "telegram": "Telegram Link",
        }

    cameras = CameraFormSetFactory()


class CommandantForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        ]
        widgets = {
            "username": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Komendant adı"}
            ),
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Adı"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Soyadı"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Email"}
            ),
        }

    def __init__(self, *args, **kwargs):
        # Extract branch_id from kwargs if present
        self.branch_id = kwargs.pop("branch_id", None)
        super().__init__(*args, **kwargs)
        self.fields["password1"].label = "New Password"
        self.fields["password2"].label = "Confirm New Password"
        self.fields["password1"].widget = forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Parol yarat",
                "autocomplete": "new-password",
            }
        )
        self.fields["password2"].widget = forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Parolu təkrar yaz",
                "autocomplete": "new-password",
            }
        )
        for field in self.fields.values():
            field.help_text = None
            field.label = ""


class ResidentForm(UserCreationForm):
    flat = forms.CharField(
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-control select2",
            }
        ),
    )

    class Meta:
        model = User
        fields = [
            "flat",
            "username",
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "password1",
            "password2",
        ]
        widgets = {
            "username": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "İstifadəçi"}
            ),
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Adı"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Soyadı"}
            ),
            "phone_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Mobil nömrəsi",
                    "type": "tel",
                }
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Email"}
            ),
        }

    def __init__(self, *args, **kwargs):
        building_id = kwargs.pop("building_id", None)
        self.branch_id = kwargs.pop("branch_id", None)
        request_user = kwargs.pop("request_user", None)
        super().__init__(*args, **kwargs)
        if building_id:
            self.fields["flat"].queryset = Flat.objects.filter(building_id=building_id)
        self.fields["password1"].label = "New Password"
        self.fields["password2"].label = "Confirm New Password"
        self.fields["password1"].widget = forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Parol yarat",
                "autocomplete": "new-password",
            }
        )
        self.fields["password2"].widget = forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Parolunuzu təsdiq edin",
                "autocomplete": "new-password",
            }
        )
        for field in self.fields.values():
            field.help_text = None
            field.label = ""


class ResidentCreationForm(UserCreationForm):
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.none(),  # Başlangıçta boş bir queryset
        required=False,
        widget=forms.Select(attrs={"class": "form-control select2"}),
    )
    building = forms.ModelChoiceField(
        queryset=Building.objects.none(),  # Başlangıçta boş bir queryset
        required=False,
        widget=forms.Select(attrs={"class": "form-control select2"}),
    )
    flat = forms.ModelChoiceField(
        queryset=Flat.objects.none(),  # Başlangıçta boş bir queryset
        required=False,
        widget=forms.Select(attrs={"class": "form-control select2"}),
    )

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "branch",
            "building",
            "flat",
            "password1",
            "password2",
        ]
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "phone_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "type": "tel",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if user:
            # Kullanıcıya özgü verilerle queryset'leri güncelle
            self.fields["branch"].queryset = Branch.objects.filter(users=user)
            self.fields["building"].queryset = Building.objects.filter(
                branch__in=user.branch.all()
            )
            self.fields["flat"].queryset = Flat.objects.filter(
                building__in=Building.objects.filter(branch__in=user.branch.all())
            )

        self.fields["password1"].label = "Parol"
        self.fields["password2"].label = "Parolayı Doğrula"
        self.fields["password1"].widget = forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Parol yarat",
                "autocomplete": "new-password",
            }
        )
        self.fields["password2"].widget = forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Parolunuzu təsdiq edin",
                "autocomplete": "new-password",
            }
        )
        for field in self.fields.values():
            field.help_text = None
            field.label = ""


class PaymentForm(forms.ModelForm):
    flat = forms.ModelChoiceField(
        queryset=Flat.objects.all(),  # Customize this queryset as needed
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-control select2",
                "data-placeholder": "Mənzili seç",
            }
        ),
        empty_label="Seçin",
        label="Mənzil",
    )

    class Meta:
        model = Payment
        fields = ["building", "flat", "amount", "service", "date"]
        widgets = {
            "building": forms.Select(
                attrs={
                    "class": "form-control form-select",
                    "data-placeholder": "Binanı seç",
                }
            ),
            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "data-placeholder": "Məbləğ",
                    "step": "0.01",
                }
            ),
            "service": forms.Select(
                attrs={
                    "class": "form-control form-select",
                    "data-placeholder": "Xidməti seç",
                }
            ),
            "date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "data-placeholder": "Tarix",
                    "type": "date",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.help_text = None
            # field.label = ""


class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ["title", "content"]

        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Başlıq"}
            ),
            "content": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Məzmun"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.label = ""


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["name", "price", "outcome_date", "outcome_document", "description"]

        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Başlıq"}
            ),
            "price": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Qiymət"}
            ),
            "outcome_date": forms.DateInput(
                attrs={"class": "form-control", "placeholder": "Tarix", "type": "date"}
            ),
            "outcome_document": forms.ClearableFileInput(
                attrs={"class": "form-control"}
            ),
            "description": forms.Textarea(
                attrs={"class": "form-control", "placeholder": "Açıqlama", "rows": 3}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.label = ""
            field.help_text = None
