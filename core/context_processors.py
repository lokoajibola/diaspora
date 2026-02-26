from django.conf import settings

def currency_processor(request):
    currency = request.session.get('currency', 'NGN')
    rate = settings.EXCHANGE_RATES.get(currency, 1.0)

    symbols = {'NGN': '₦', 'GBP': '£', 'USD': '$'}
    currency_names = {
        'NGN': 'Nigerian Naira',
        'GBP': 'British Pound',
        'USD': 'US Dollar',
    }

    currencies = [
        {
            'code': code,
            'symbol': symbols.get(code, '₦'),
            'name': currency_names.get(code, code),
        }
        for code in settings.EXCHANGE_RATES.keys()
    ]

    selected_currency = {
        'code': currency,
        'symbol': symbols.get(currency, '₦'),
        'name': currency_names.get(currency, currency),
    }

    return {
        'CURRENCY_CODE': currency,
        'CURRENCY_SYMBOL': symbols.get(currency, '₦'),
        'CURRENCY_RATE': rate,
        'currencies': currencies,
        'selected_currency': selected_currency,
        'CURRENCY': selected_currency,
    }