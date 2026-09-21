from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def send_transactional_email(subject, template_name, context, recipient_list):
    """
    Utility function to send HTML emails using Django templates.
    
    Args:
        subject (str): The email subject line.
        template_name (str): The path to the HTML template (e.g., 'emails/welcome.html').
        context (dict): The context dictionary to render the template.
        recipient_list (list): List of recipient email addresses.
    """
    html_message = render_to_string(template_name, context)
    plain_message = strip_tags(html_message)
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Violett <hola@violett.com.ar>')
    
    # Use EmailMultiAlternatives to send both HTML and plain text
    msg = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=from_email,
        to=recipient_list
    )
    msg.attach_alternative(html_message, "text/html")
    return msg.send(fail_silently=False)

def send_simple_email(subject, message, recipient_list):
    """
    Utility function to send a plain text email.
    """
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Violett <hola@violett.com.ar>')
    return send_mail(
        subject,
        message,
        from_email,
        recipient_list,
        fail_silently=False,
    )
