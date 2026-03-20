from django.conf import settings

def currency_processor(request):
    currency = request.session.get('currency', 'NGN')
    if currency not in settings.CURRENCIES:
        currency = 'NGN'

    rate = settings.EXCHANGE_RATES.get(currency, 1.0)
    selected_currency = {
        'code': currency,
        **settings.CURRENCIES[currency],
    }
    currencies = [
        {'code': code, **details}
        for code, details in settings.CURRENCIES.items()
    ]

    return {
        'CURRENCY_CODE': currency,
        'CURRENCY_SYMBOL': selected_currency['symbol'],
        'CURRENCY_RATE': rate,
        'selected_currency': selected_currency,
        'currencies': currencies,
        'CURRENCY': selected_currency,
    }