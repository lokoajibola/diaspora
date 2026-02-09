
from django.contrib import admin
from django.urls import path, include
from users.views import CustomLoginView, register  # Assuming register view is defined
from django.conf import settings
from django.conf.urls.static import static
from products.views import home, set_currency
from users import views as user_views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/', register, name='register'),
    path('vendor/', include('products.urls')),
    path('payments/', include('payments.urls')),
    path('orders/', include('orders.urls')),
    path('users/', include('users.urls')),
    path('', home, name='home'),
    path('set-currency/', set_currency, name='set_currency'),
    path('login-redirect/', user_views.role_based_redirect, name='login_redirect'),
    # Add other apps as we build them
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)