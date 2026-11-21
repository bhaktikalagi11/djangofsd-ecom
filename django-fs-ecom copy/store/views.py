
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.views.decorators.http import require_POST
from decimal import Decimal

from .models import Product, Order, OrderItem
from .forms import ProductForm, CheckoutForm


# HOME PAGE
def home(request):
    query = request.GET.get('q', '')

    products = Product.objects.all()

    if query:
        products = products.filter(name__icontains=query)

    return render(request, 'home.html', {
        'products': products,
        'query': query
    })


# PRODUCT DETAILS
def product_detail(request, id):
    product = get_object_or_404(Product, id=id)

    return render(request, 'product_detail.html', {
        'product': product
    })


# ADMIN CHECK
def is_admin(user):
    return user.is_authenticated and user.is_staff


# ADD PRODUCT
@login_required
@user_passes_test(is_admin)
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('home')

    else:
        form = ProductForm()

    return render(request, 'product_form.html', {
        'form': form,
        'page_title': 'Add a product',
        'submit_label': 'Add product',
    })


# UPDATE PRODUCT
@login_required
@user_passes_test(is_admin)
def update_product(request, id):
    product = get_object_or_404(Product, id=id)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)

        if form.is_valid():
            form.save()
            return redirect('home')

    else:
        form = ProductForm(instance=product)

    return render(request, 'product_form.html', {
        'form': form,
        'page_title': f'Update {product.name}',
        'submit_label': 'Save changes',
        'product': product,
    })


# DELETE PRODUCT
@login_required
@user_passes_test(is_admin)
def delete_product(request, id):
    product = get_object_or_404(Product, id=id)

    if request.method == 'POST':
        product.delete()
        return redirect('home')

    return render(request, 'delete_product.html', {
        'product': product
    })


# REGISTER
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('login')

    else:
        form = UserCreationForm()

    return render(request, 'register.html', {
        'form': form
    })


# LOGIN
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('home')

        else:
            messages.error(request, 'Invalid credentials')

    return render(request, 'login.html')


# LOGOUT
@require_POST
def user_logout(request):
    logout(request)
    return redirect('login')


# ADD TO CART
@login_required
@require_POST
def add_to_cart(request, id):
    product = get_object_or_404(Product, id=id)

    cart = request.session.get('cart', {})
    product_id = str(product.id)
    quantity = cart.get(product_id, 0)

    if product.stock < 1 or quantity >= product.stock:
        messages.error(request, 'This product is out of stock.')
        return redirect('home')

    cart[product_id] = quantity + 1

    request.session['cart'] = cart

    messages.success(request, 'Product added to cart')

    return redirect('home')


# VIEW CART
@login_required
def view_cart(request):
    cart = request.session.get('cart', {})

    cart_items = []

    total = 0

    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)

        subtotal = product.price * quantity

        total += subtotal

        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal
        })

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total': total
    })


# REMOVE FROM CART
@login_required
@require_POST
def remove_cart(request, id):
    cart = request.session.get('cart', {})

    cart.pop(str(id), None)

    request.session['cart'] = cart

    return redirect('view_cart')


# CHECKOUT
@login_required
def checkout(request):
    cart = request.session.get('cart', {})

    if not cart:
        return redirect('view_cart')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():

                    total = Decimal('0.00')

                    products = {}

                    for product_id, quantity in cart.items():
                        product = get_object_or_404(
                            Product.objects.select_for_update(),
                            id=product_id
                        )

                        if quantity < 1 or product.stock < quantity:
                            raise ValueError(
                                f"Insufficient stock for {product.name}"
                            )

                        products[product_id] = product

                        total += product.price * quantity

                    order = Order.objects.create(
                        user=request.user,
                        total_amount=total,
                        address=form.cleaned_data['address']
                    )

                    for product_id, quantity in cart.items():
                        product = products[product_id]

                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            quantity=quantity,
                            price=product.price
                        )

                        product.stock -= quantity

                        product.save()

                request.session['cart'] = {}

                messages.success(
                    request,
                    'Order placed successfully!'
                )

                return redirect('my_orders')

            except ValueError as error:
                messages.error(request, str(error))
                return redirect('view_cart')

    else:
        form = CheckoutForm()

    return render(request, 'checkout.html', {
        'form': form
    })


# MY ORDERS
@login_required
def my_orders(request):
    orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(request, 'orders.html', {
        'orders': orders
    })


def not_found(request, exception):
    return render(request, '404.html', status=404)
