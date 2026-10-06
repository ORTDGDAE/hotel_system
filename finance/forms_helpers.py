from .forms import PaymentForm


def payment_form_from_request(request) -> PaymentForm:
    return PaymentForm(request.POST or None)
