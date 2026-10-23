import logging
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

logger = logging.getLogger(__name__)

def _log_email(destinatario, asunto, template_name='', cuerpo_html='', cuerpo_texto='', estado='ENVIADO', error_mensaje=''):
    try:
        from .models import EmailLog
        EmailLog.objects.create(
            destinatario=destinatario,
            asunto=asunto,
            template_name=template_name,
            cuerpo_html=cuerpo_html,
            cuerpo_texto=cuerpo_texto,
            estado=estado,
            error_mensaje=error_mensaje
        )
    except Exception as e:
        logger.warning(f"[EMAIL LOGGING ERROR] No se pudo guardar EmailLog: {e}")

def send_transactional_email(subject, template_name, context, recipient_list):
    """
    Utility function to send HTML emails using Django templates.
    """
    html_message = ''
    plain_message = ''
    dest = recipient_list[0] if recipient_list else ''
    try:
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Violett <hola@violett.com.ar>')
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=from_email,
            to=recipient_list
        )
        msg.attach_alternative(html_message, "text/html")
        sent = msg.send(fail_silently=False)
        
        logger.info(f"[EMAIL RESEND] Enviado exitosamente '{subject}' a {recipient_list}")
        _log_email(
            destinatario=dest,
            asunto=subject,
            template_name=template_name,
            cuerpo_html=html_message,
            cuerpo_texto=plain_message,
            estado='ENVIADO'
        )

        try:
            from backend_core.hooks import registry
            registry.execute('email_enviado_tracker', {'subject': subject, 'recipient_list': recipient_list})
        except Exception as te:
            logger.warning(f"[EMAIL TRACKER ERROR] {te}")
            
        return sent
    except Exception as e:
        logger.error(f"[EMAIL RESEND ERROR] Error enviando '{subject}' a {recipient_list}: {type(e).__name__} - {e}")
        _log_email(
            destinatario=dest,
            asunto=subject,
            template_name=template_name,
            cuerpo_html=html_message,
            cuerpo_texto=plain_message,
            estado='FALLIDO',
            error_mensaje=str(e)
        )
        raise e

def send_simple_email(subject, message, recipient_list):
    """
    Utility function to send a plain text email.
    """
    dest = recipient_list[0] if recipient_list else ''
    try:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Violett <hola@violett.com.ar>')
        sent = send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False,
        )
        logger.info(f"[EMAIL RESEND] Plain text email enviado '{subject}' a {recipient_list}")
        _log_email(
            destinatario=dest,
            asunto=subject,
            cuerpo_texto=message,
            estado='ENVIADO'
        )
        try:
            from backend_core.hooks import registry
            registry.execute('email_enviado_tracker', {'subject': subject, 'recipient_list': recipient_list})
        except Exception as te:
            logger.warning(f"[EMAIL TRACKER ERROR] {te}")
        return sent
    except Exception as e:
        logger.error(f"[EMAIL RESEND ERROR] Error enviando simple '{subject}' a {recipient_list}: {type(e).__name__} - {e}")
        _log_email(
            destinatario=dest,
            asunto=subject,
            cuerpo_texto=message,
            estado='FALLIDO',
            error_mensaje=str(e)
        )
        raise e
