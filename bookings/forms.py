import datetime as dt

from django import forms
from django.utils import timezone

from hotel.models import RoomType

from .models import Booking, RateRule


class DateInput(forms.DateInput):
    input_type = "date"


class SearchForm(forms.Form):
    check_in = forms.DateField(widget=DateInput)
    check_out = forms.DateField(widget=DateInput)
    adults = forms.IntegerField(min_value=1, max_value=12, initial=2)
    children = forms.IntegerField(min_value=0, max_value=8, initial=0)
    rooms = forms.IntegerField(min_value=1, max_value=8, initial=1)

    def clean(self):
        cleaned = super().clean()
        ci, co = cleaned.get("check_in"), cleaned.get("check_out")
        if ci and co and co <= ci:
            raise forms.ValidationError("Check-out must be after check-in.")
        if ci and ci < timezone.localdate():
            raise forms.ValidationError("Check-in cannot be in the past.")
        return cleaned


class GuestBookingForm(forms.Form):
    """Step 2 of the guest wizard: contact details + payment intent."""

    guest_name = forms.CharField(max_length=160, label="Full name")
    guest_email = forms.EmailField(label="Email")
    guest_phone = forms.RegexField(
        regex=r"^[0-9+() .-]{7,32}$",
        label="Phone number",
        error_messages={"invalid": "Enter a valid phone number, for example +855 12 345 678."},
        widget=forms.TextInput(attrs={
            "type": "tel",
            "autocomplete": "tel",
            "inputmode": "tel",
            "placeholder": "+855 12 345 678",
        }),
    )
    special_requests = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)
    pay_now = forms.BooleanField(required=False, initial=True, label="Pay now (secure card)")
    payment_method = forms.ChoiceField(
        choices=[("card", "Credit / debit card"), ("wallet", "E-wallet"), ("bank_transfer", "Bank transfer")],
        initial="card", required=False,
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            self.fields["guest_name"].initial = user.get_full_name()
            self.fields["guest_email"].initial = user.email
            self.fields["guest_phone"].initial = getattr(user, "phone", "")


class StaffBookingForm(forms.ModelForm):
    """Front-desk reservation creation (walk-ins, phone, OTA)."""

    class Meta:
        model = Booking
        fields = [
            "guest", "guest_name", "guest_email", "guest_phone", "room_type",
            "check_in", "check_out", "rooms_count", "adults", "children",
            "source", "special_requests",
        ]
        widgets = {
            "check_in": DateInput,
            "check_out": DateInput,
            "special_requests": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["guest"].required = False
        self.fields["guest"].queryset = self.fields["guest"].queryset.order_by("username")
        self.fields["room_type"].queryset = RoomType.objects.filter(is_active=True)
        today = timezone.localdate()
        self.fields["check_in"].initial = today
        self.fields["check_out"].initial = today + dt.timedelta(days=1)

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("guest_name") and cleaned.get("guest"):
            cleaned["guest_name"] = cleaned["guest"].get_full_name() or cleaned["guest"].username
        if not cleaned.get("guest_name"):
            self.add_error("guest_name", "Required for walk-in reservations.")
        return cleaned


class CheckInForm(forms.Form):
    """Room assignment picker rendered from available vacant-clean rooms."""

    def __init__(self, *args, booking=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.booking = booking
        if booking:
            from hotel.models import Room
            free = Room.objects.filter(
                room_type=booking.room_type, status=Room.Status.VACANT_CLEAN
            ).order_by("number")
            self.fields["rooms"] = forms.ModelMultipleChoiceField(
                queryset=free,
                widget=forms.CheckboxSelectMultiple,
                label=f"Assign {booking.rooms_count} room(s)",
                help_text="Only vacant & clean rooms of the booked type can be assigned.",
            )

    def clean_rooms(self):
        rooms = self.cleaned_data["rooms"]
        if self.booking and len(rooms) != self.booking.rooms_count:
            raise forms.ValidationError(f"Select exactly {self.booking.rooms_count} room(s).")
        return rooms


class PaymentForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    method = forms.ChoiceField(choices=[("cash", "Cash"), ("card", "Card"), ("bank_transfer", "Bank transfer"), ("wallet", "E-wallet")])
    note = forms.CharField(max_length=255, required=False)


class RateRuleForm(forms.ModelForm):
    class Meta:
        model = RateRule
        fields = ["name", "rule_type", "property", "room_type", "start_date", "end_date", "multiplier", "priority", "is_active"]
        widgets = {"start_date": DateInput, "end_date": DateInput}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["room_type"].required = False
        self.fields["property"].required = False


class RoomStatusForm(forms.Form):
    status = forms.ChoiceField(choices=[])

    def __init__(self, *args, **kwargs):
        from hotel.models import Room
        super().__init__(*args, **kwargs)
        self.fields["status"].choices = Room.Status.choices
