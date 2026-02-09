import requests
from django.conf import settings

def initialize_paystack_payment(email, amount, callback_url):
    url = "https://api.paystack.co/transaction/initialize"
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    data = {
        "email": email,
        "amount": int(amount * 100), # Paystack works in kobo/cents
        "callback_url": callback_url
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()