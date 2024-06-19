from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from PetStore import settings
from pets.models import Cart, CartItem, Order, OrderItems, Pet, Product
from .forms import OrderCreateForm, SearchForm, UserRegistrationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import razorpay
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail

# Create your views here.
def pet_list(request):
    form = SearchForm(request.GET or None)
    pets = Pet.objects.all()

    if form.is_valid():
        query = form.cleaned_data['query']
        pets = pets.filter(name__icontains=query)

    return render(request, 'pets/pet_list.html', {'pets': pets, 'form': form})

def pet_detail(request, pk):
    pet = get_object_or_404(Pet, pk=pk)
    return render(request, 'pets/pet_detail.html', {'pet': pet})

def product_list(request):
    form = SearchForm(request.GET or None)
    products = Product.objects.all()

    if form.is_valid():
        query = form.cleaned_data['query']
        products = products.filter(name__icontains=query)

    return render(request, 'pets/product_list.html', {'products': products, 'form': form})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'pets/product_detail.html', {'product': product})

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'pets/register.html', {'form':form})    
    
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('pet_list')
            else : 
                messages.error(request, 'Invalid username or password')
        else:
            messages.error(request, 'Invalid username or password')
    else:
        form = AuthenticationForm()
    return render(request, 'pets/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('login')


@login_required
def add_to_cart(request, item_type, item_id):
    user_cart, created = Cart.objects.get_or_create(user_id=request.user.id)
    if item_type == 'pet':
        item = get_object_or_404(Pet, id=item_id)
        cart_item, created = CartItem.objects.get_or_create(cart=user_cart, pet=item)
    else:
        item = get_object_or_404(Product, id=item_id)
        cart_item, created = CartItem.objects.get_or_create(cart=user_cart, product=item)

    if not created:
        cart_item.quantity += 1
    cart_item.save()
    return redirect('cart_detail')

@login_required
def cart_detail(request):
    cart, created = Cart.objects.get_or_create(user_id=request.user.id)
    cart_items = CartItem.objects.filter(cart=cart) 
    total = sum(item.total for item in cart_items)
    print("total : ", total )
    return render(request, 'pets/cart_detail.html', {'cart_items': cart_items, 'total': total})

def increase_qunatity(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.quantity += 1
    cart_item.save()
    return redirect('cart_detail')

def decrease_quantity(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart_detail')

# @login_required
# def send_order_confirmation_email(order, to_email):
#     subject = 'Your Order Confirmation'
#     message = f'Thank you for your order! Your order ID is {order.id}.'
#     from_email = settings.EMAIL_HOST_USER
#     recipient_list = [to_email]
#     send_mail(subject, message, from_email, recipient_list)

@login_required
def order_create(request):
    #cart = Cart.objects.get(id=1)
    cart, created = Cart.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save()
            for item in cart.items.all():
                if item.product:
                    if item.product.quantity < item.quantity:
                        messages.error(request, f"Not enough stock for {item.product.name}. Available quantity: {item.product.quantity}.")
                        return redirect('cart_detail')  # Adjust this to your order create view name
                elif item.pet:
                    if item.pet.quantity < item.quantity:
                        messages.error(request, f"Not enough stock for {item.pet.name}. Available quantity: {item.pet.quantity}.")
                        return redirect('cart_detail')  # Adjust this to your order create view name                
            # If all items are available, proceed to create order items and update quantities
                OrderItems.objects.create(
                    order = order,
                    product = item.product,
                    pet = item.pet,
                    price = item.product.price if item.product else item.pet.price,
                    quantity = item.quantity
                )
                  # Update the quantity of the product/pet
                if item.product:
                    item.product.quantity -= item.quantity
                    item.product.save()
                elif item.pet:
                    item.pet.quantity -= item.quantity
                    item.pet.save()
            # cart.items.all().delete()
            print("Total=> " ,order.total_cost)
            amount=float(order.total_cost *100)
            client = razorpay.Client(auth=(settings.RAZORPAY_TEST_KEY_ID, settings.RAZORPAY_TEST_KEY_SECRET))
            payment_data = {
                'amount': amount,
                'currency': 'INR',
                'receipt': f'order_{order.id}', 
            }
            print("Total (INR)=> ",amount)
            print(payment_data)
            payment = client.order.create(data=payment_data)

            # Send email confirmation to user
            # subject = f'Order Confirmation - Order #{order.id}'
            # message = f'Thank you for your order! Your order #{order.id} has been successfully placed.'
            # from_email = settings.EMAIL_HOST_USER
            # to_email = [request.user.email]  # Replace with actual user email
            
            # send_mail(subject, message, from_email, to_email)

            #send_order_confirmation_email(order, request.user.email)
            print(request.user.email)
            cart.items.all().delete()
            return render(request, 'pets/order_created.html', {'order': order, 'payment': payment, 'razorpay_key_id': settings.RAZORPAY_TEST_KEY_ID})
    else : 
        form = OrderCreateForm()
    return render(request, 'pets/order_create.html', {'cart': cart, 'form': form})


def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    messages.success(request, 'Item removed from cart successfully.')
    return redirect('cart_detail')  # Adjust this to the name of your cart detail view

@csrf_exempt
def process_payment(request):
    if request.method == 'POST':
        return HttpResponse("Payment Successful")
    return HttpResponse(status=400)

