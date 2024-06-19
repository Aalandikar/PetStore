from django.core.mail import send_mail
from django.conf import settings

def send_order_confirmation_email(order, recipient_email):
    subject = 'Your Order Confirmation'
    message = f'Thank you for your order! Your order ID is {order.id}.'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [recipient_email]
    
    send_mail(subject, message, from_email, recipient_list)
