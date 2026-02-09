from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Order
from django.shortcuts import get_object_or_404, redirect

# Create your views here.
@login_required
def logistics_dashboard(request):
    if request.user.role != 'logistics':
        return redirect('home')
    orders = Order.objects.exclude(status='delivered')
    return render(request, 'logistics/dashboard.html', {'orders': orders})

def update_delivery(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        order.status = request.POST.get('status')
        order.save()
    return redirect('logistics_dashboard')