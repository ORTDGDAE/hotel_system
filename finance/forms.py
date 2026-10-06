from django import forms


class PaymentForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0.01, label="Amount")
    method = forms.ChoiceField(
        choices=[("cash", "Cash"), ("card", "Card"), ("bank_transfer", "Bank transfer"), ("wallet", "E-wallet")],
        label="Method",
    )
    note = forms.CharField(max_length=255, required=False, label="Note")
