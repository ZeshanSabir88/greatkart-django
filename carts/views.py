from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from store.models import Product, Variation
from .models import Cart, CartItem
from django.http import HttpResponse # Generally not needed unless for debugging/API
from django.contrib.auth.decorators import login_required




def _cart_id(request):
    """Retrieves the current session key or creates a new one for the cart ID."""
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def add_cart(request, product_id):
    current_user = request.user
    product = get_object_or_404(Product, id=product_id) # Use get_object_or_404 for Product
    # if the user is authenticated

    if current_user.is_authenticated:
        product_variation = []
        if request.method == 'POST':
            for key in request.POST:
                value = request.POST.get(key)
                try:
                    variation = Variation.objects.get(
                        product=product,
                        variation_category__iexact=key,
                        variation_value__iexact=value
                    )
                    product_variation.append(variation)
                except Variation.DoesNotExist:
                    pass

        # Get or create cart
        # --- FIX: Variation Comparison Logic ---
        # Convert incoming variations to a set for order-independent comparison
        incoming_variation_set = set(product_variation)

        # Check if product already exists in cart with the EXACT same variations
        is_cart_item_exists = False
        id_to_increase = None

        cart_items = CartItem.objects.filter(product=product, user=current_user)

        if cart_items.exists():
            for item in cart_items:
                existing_variation_set = set(item.variations.all())

                # Compare the sets (order doesn't matter now)
                if existing_variation_set == incoming_variation_set:
                    is_cart_item_exists = True
                    id_to_increase = item.id
                    break

        if is_cart_item_exists:
            # If same variation exists → increase quantity
            item = CartItem.objects.get(product=product, id=id_to_increase)
            item.quantity += 1
            item.save()

        else:
            # If product exists but variation is different, OR product is new: create new CartItem
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                user=current_user,
            )

            if len(product_variation) > 0:
                # The * unpacks the list into arguments for .add()
                cart_item.variations.add(*product_variation)

            cart_item.save()

        return redirect('cart')


    # if user is not authenticated

    else:
    # Get product variations from POST
        product_variation = []
        if request.method == 'POST':
            for key in request.POST:
                value = request.POST.get(key)
                try:
                    variation = Variation.objects.get(
                        product=product,
                        variation_category__iexact=key,
                        variation_value__iexact=value
                    )
                    product_variation.append(variation)
                except Variation.DoesNotExist:
                    pass

        # Get or create cart
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))
            cart.save()

        # --- FIX: Variation Comparison Logic ---
        # Convert incoming variations to a set for order-independent comparison
        incoming_variation_set = set(product_variation)

        # Check if product already exists in cart with the EXACT same variations
        is_cart_item_exists = False
        id_to_increase = None

        cart_items = CartItem.objects.filter(product=product, cart=cart)

        if cart_items.exists():
            for item in cart_items:
                existing_variation_set = set(item.variations.all())

                # Compare the sets (order doesn't matter now)
                if existing_variation_set == incoming_variation_set:
                    is_cart_item_exists = True
                    id_to_increase = item.id
                    break

        if is_cart_item_exists:
            # If same variation exists → increase quantity
            item = CartItem.objects.get(product=product, id=id_to_increase)
            item.quantity += 1
            item.save()

        else:
            # If product exists but variation is different, OR product is new: create new CartItem
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                cart=cart,
            )

            if len(product_variation) > 0:
                # The * unpacks the list into arguments for .add()
                cart_item.variations.add(*product_variation)

            cart_item.save()

        return redirect('cart')


def remove_cart(request, product_id, cart_item_id):
    """Decrements the quantity of a cart item or removes it if quantity is 1."""

    product = get_object_or_404(Product, id=product_id)

    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)

        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            # If quantity is 1, delete the item entirely
            cart_item.delete()

    except CartItem.DoesNotExist:
        pass # Should handle error gracefully if item isn't found

    return redirect('cart')


def remove_cart_item(request, product_id, cart_item_id):
    """Deletes a specific CartItem entirely (used for 'Remove' button)."""


    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)


    cart_item.delete()
    return redirect('cart')


def cart(request, total=0, quantity=0, cart_items=None):


    try:
        tax = 0
        grand_total = 0
        # Check if user is authenticated (not shown in original code, but good practice)
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:
            # Ensure price exists before multiplying (safe guard)
            item_price = cart_item.product.price if cart_item.product.price else 0
            total += (item_price * cart_item.quantity)
            quantity += cart_item.quantity

        # Calculate tax and grand total
        if total > 0:
            # Tax calculation: (2 * total) / 100 is 2%
            TAX_RATE = 0.02
            tax = total * TAX_RATE
            grand_total = total + tax

    except ObjectDoesNotExist:
        pass  # cart or cart_items will be None, template handles it

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart.html', context)

@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):

    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:
            # Ensure price exists before multiplying (safe guard)
            item_price = cart_item.product.price if cart_item.product.price else 0
            total += (item_price * cart_item.quantity)
            quantity += cart_item.quantity

        # Calculate tax and grand total
        if total > 0:
            # Tax calculation: (2 * total) / 100 is 2%
            TAX_RATE = 0.02
            tax = total * TAX_RATE
            grand_total = total + tax

    except ObjectDoesNotExist:
        pass  # cart or cart_items will be None, template handles it

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/checkout.html', context)
