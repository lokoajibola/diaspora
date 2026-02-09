from django.conf import settings

def currency_processor(request):
    currency = request.session.get('currency', 'NGN')
    rate = settings.EXCHANGE_RATES.get(currency, 1.0)
    
    symbols = {'NGN': '₦', 'GBP': '£', 'USD': '$'}
    
    return {
        'CURRENCY_CODE': currency,
        'CURRENCY_SYMBOL': symbols.get(currency, '₦'),
        'CURRENCY_RATE': rate
    }