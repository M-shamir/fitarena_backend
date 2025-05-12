# payment/urls.py
from django.urls import path
from .views import CreateCheckoutSessionView, stripe_webhook, VerifyPaymentView

urlpatterns = [
    path('create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('verify-payment/', VerifyPaymentView.as_view(), name='verify-payment'),  # New endpoint
    path('webhook/', stripe_webhook, name='stripe-webhook'),
]