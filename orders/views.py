from django.shortcuts import render, redirect
from django.http import HttpResponse
from carts.models import CartItem
from .forms import OrderForm
import datetime
from .models import Order, Payment, OrderProduct
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

# 1. Payments View (Online Payment ke liye)
def payments(request):
    try:
        order = Order.objects.filter(user=request.user, is_ordered=False).last()
        payment = Payment.objects.filter(user=request.user).last()
    except Order.DoesNotExist:
        return redirect('checkout')

    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save() # Pehle ID generate karne ke liye save

        # Variations set karein
        product_variations = item.variations.all()
        orderproduct.variations.set(product_variations)
        orderproduct.save()

        # Stock kam karein
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    # Cart khali karein
    CartItem.objects.filter(user=request.user).delete()

    # Order update karein
    order.is_ordered = True
    order.save()

    # Email Send karein
    mail_subject = 'Thank you for your order!'
    message = render_to_string('orders/order_recieved_email.html', {
        'user': request.user,
        'order': order,
    })
    to_email = request.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()

    return render(request, 'orders/payments.html')

# 2. Place Order View
def place_order(request, total=0, quantity=0):
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()

    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total)/100
    grand_total = total + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
            }
            return render(request, 'orders/payments.html', context)
        else:
            return redirect('checkout')
    else:
        return redirect('checkout')

# 3. Cash on Delivery Logic (Updated with Email & Highlight Fix)
def cash_on_delivery(request, order_number):
    try:
        # Order fetch karein
        order = Order.objects.get(user=request.user, is_ordered=False, order_number=order_number)

        # 1. Payment entry banayein
        payment = Payment(
            user = request.user,
            payment_id = order_number,
            payment_method = 'Cash on Delivery',
            amount_paid = order.order_total,
            status = 'Pending',
        )
        payment.save()

        # 2. Order update karein
        order.payment = payment
        order.is_ordered = True
        order.save()

        # 3. Cart items ko OrderProduct mein move karein
        cart_items = CartItem.objects.filter(user=request.user)
        for item in cart_items:
            orderproduct = OrderProduct()
            orderproduct.order_id = order.id
            orderproduct.payment = payment
            orderproduct.user_id = request.user.id
            orderproduct.product_id = item.product_id
            orderproduct.quantity = item.quantity
            orderproduct.product_price = item.product.price
            orderproduct.ordered = True
            orderproduct.save() # ID banane ke liye save

            # Variations ko set karein
            product_variations = item.variations.all()
            orderproduct.variations.set(product_variations)
            orderproduct.save()

            # Stock kam karein
            product = Product.objects.get(id=item.product_id)
            product.stock -= item.quantity
            product.save()

        # 4. Cart khali karein
        CartItem.objects.filter(user=request.user).delete()

        # 5. Send Email Notification
        mail_subject = 'Thank you for your order!'
        message = render_to_string('orders/order_recieved_email.html', {
            'user': request.user,
            'order': order,
        })
        to_email = request.user.email
        send_email = EmailMessage(mail_subject, message, to=[to_email])
        send_email.send()

        context = {
            'order': order,
            'payment': payment,
        }
        return render(request, 'orders/order_complete.html', context)

    except Order.DoesNotExist:
        return redirect('home')
