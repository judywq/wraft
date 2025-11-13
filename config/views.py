from datetime import datetime
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseServerError
from django.utils import timezone


# Email sending method constants
# Method 1: Use Django's send_mail helper (plain text)
# Method 2: Use EmailMessage class (supports HTML)
EMAIL_METHOD_SEND_MAIL = 1
EMAIL_METHOD_EMAIL_MESSAGE = 2


def _get_debug_info(method: int, from_email: str, to: str) -> str:
    """
    Generate formatted debug information for email testing.

    Args:
        method: Email sending method (1 = send_mail, 2 = EmailMessage)
        from_email: Sender email address
        to: Recipient email address

    Returns:
        Formatted debug information string
    """
    # Get current datetime (timezone-aware if USE_TZ is True)
    if settings.USE_TZ:
        current_time = timezone.now()
        time_str = current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        tz_info = "UTC"
    else:
        current_time = datetime.now()
        time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
        tz_info = "Local"

    # Get email backend information
    email_backend = getattr(settings, "EMAIL_BACKEND", "Not configured")
    email_host = getattr(settings, "EMAIL_HOST", "Not configured")
    email_port = getattr(settings, "EMAIL_PORT", "Not configured")

    # Determine method name
    method_name = "send_mail" if method == EMAIL_METHOD_SEND_MAIL else "EmailMessage"

    # Format debug information
    debug_info = f"""
═══════════════════════════════════════════════════════════
                    EMAIL DEBUG INFORMATION
═══════════════════════════════════════════════════════════

📧 Email Details:
   • From:        {from_email}
   • To:          {to}
   • Method:      {method_name} (method={method})
   • Subject:     Test Email - It Works!

⏰ Timestamp:
   • Sent At:     {time_str}
   • Timezone:    {tz_info}

⚙️  Email Configuration:
   • Backend:     {email_backend}
   • Host:        {email_host}
   • Port:        {email_port}
   • USE_TLS:     {getattr(settings, 'EMAIL_USE_TLS', False)}
   • USE_SSL:     {getattr(settings, 'EMAIL_USE_SSL', False)}

🌐 Django Settings:
   • DEBUG:       {settings.DEBUG}
   • Environment: {getattr(settings, 'ENVIRONMENT', 'Not set')}

═══════════════════════════════════════════════════════════
"""
    return debug_info


def send_test_email(request: HttpRequest, method: int, to: str) -> HttpResponse:
    """
    Test email sending functionality for development purposes.

    This view is only available when DEBUG=True. It allows testing email
    configuration by sending a test email using different methods.

    Args:
        request: The HTTP request object (unused but required by Django URL routing)
        method: Email sending method (1 = send_mail, 2 = EmailMessage)
        to: Recipient email address

    Returns:
        HttpResponse: Success message if email sent successfully
        HttpResponseBadRequest: If method is invalid
        HttpResponseServerError: If email sending fails

    URL Pattern:
        /send-email/<int:method>/<str:to>/

    Examples:
        /send-email/1/user@example.com/  - Send using send_mail
        /send-email/2/user@example.com/  - Send using EmailMessage
    """
    # Validate email method
    if method not in (EMAIL_METHOD_SEND_MAIL, EMAIL_METHOD_EMAIL_MESSAGE):
        return HttpResponseBadRequest(
            f"Invalid method: {method}. Use 1 (send_mail) or 2 (EmailMessage)."
        )

    # Email configuration
    subject = "Email Configuration Test"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [to]

    # Generate debug information
    debug_info = _get_debug_info(method, from_email, to)

    # Create email message with debug info
    message_body = (
        "If you are seeing this email, it means that the email configuration is working correctly.\n\n"
        + debug_info
    )

    try:
        if method == EMAIL_METHOD_SEND_MAIL:
            # Method 1: Use Django's send_mail helper function
            # This is the simplest way to send plain text emails
            send_mail(
                subject=subject,
                message=message_body,
                from_email=from_email,
                recipient_list=recipient_list,
                fail_silently=False,  # Raise exception on failure for debugging
            )

            # Create success response with debug info
            response_body = (
                f"✅ Email sent successfully using send_mail\n\n"
                + debug_info
            )
            return HttpResponse(
                response_body,
                content_type="text/plain",
            )

        else:  # method == EMAIL_METHOD_EMAIL_MESSAGE
            # Method 2: Use EmailMessage class for more control
            # This allows setting content type, attachments, etc.
            msg = EmailMessage(
                subject=subject,
                body=message_body,
                from_email=from_email,
                to=recipient_list,
            )
            # Set content type to HTML (though message is plain text in this example)
            # To send actual HTML, change 'message' to contain HTML tags
            msg.content_subtype = "html"

            # Send the email
            msg.send(fail_silently=False)

            # Create success response with debug info
            response_body = (
                f"✅ Email sent successfully using EmailMessage\n\n"
                + debug_info
            )
            return HttpResponse(
                response_body,
                content_type="text/plain",
            )

    except Exception as e:
        # Log the error and return a server error response
        # In production, you'd want to use proper logging here
        return HttpResponseServerError(
            f"Failed to send email: {str(e)}",
            content_type="text/plain",
        )
