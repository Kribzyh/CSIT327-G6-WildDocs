"""
Custom Email Backend using Mailtrap's HTTP API.
This bypasses SMTP port blocking on platforms like Render.
"""

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
import mailtrap as mt


class MailtrapEmailBackend(BaseEmailBackend):
    """
    Custom email backend that uses Mailtrap's HTTP API instead of SMTP.
    This works on Render's free tier which blocks outbound SMTP ports.
    """
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_token = getattr(settings, 'MAILTRAP_API_TOKEN', '')
        self.client = None
        
    def open(self):
        if self.client is not None:
            return False
        try:
            self.client = mt.MailtrapClient(token=self.api_token)
            return True
        except Exception:
            if not self.fail_silently:
                raise
            return False
    
    def close(self):
        self.client = None
    
    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        
        if self.client is None:
            self.open()
        
        if self.client is None:
            return 0
        
        sent_count = 0
        for message in email_messages:
            try:
                # Build Mailtrap mail object
                mail = mt.Mail(
                    sender=mt.Address(email=message.from_email),
                    to=[mt.Address(email=addr) for addr in message.to],
                    subject=message.subject,
                    text=message.body,
                )
                
                # Add HTML content if present
                if hasattr(message, 'alternatives') and message.alternatives:
                    for content, mimetype in message.alternatives:
                        if mimetype == 'text/html':
                            mail.html = content
                            break
                
                # Add CC recipients
                if message.cc:
                    mail.cc = [mt.Address(email=addr) for addr in message.cc]
                
                # Add BCC recipients
                if message.bcc:
                    mail.bcc = [mt.Address(email=addr) for addr in message.bcc]
                
                # Send the email
                self.client.send(mail)
                sent_count += 1
                
            except Exception as e:
                if not self.fail_silently:
                    raise
                    
        return sent_count
