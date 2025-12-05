"""
Custom Email Backend using Mailjet's HTTP API.
This bypasses SMTP port blocking on platforms like Render.
"""

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
import requests
from requests.auth import HTTPBasicAuth


class MailjetEmailBackend(BaseEmailBackend):
    """
    Custom email backend that uses Mailjet's HTTP API instead of SMTP.
    This works on Render's free tier which blocks outbound SMTP ports.
    """
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'MAILJET_API_KEY', '')
        self.secret_key = getattr(settings, 'MAILJET_SECRET_KEY', '')
        self.api_url = 'https://api.mailjet.com/v3.1/send'
    
    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        
        if not self.api_key or not self.secret_key:
            if not self.fail_silently:
                raise ValueError("MAILJET_API_KEY and MAILJET_SECRET_KEY must be configured")
            return 0
        
        sent_count = 0
        for message in email_messages:
            try:
                # Build recipients
                to_list = [{'Email': email} for email in message.to]
                
                # Build the message payload
                msg_data = {
                    'From': {
                        'Email': message.from_email.split('<')[-1].rstrip('>') if '<' in message.from_email else message.from_email,
                        'Name': message.from_email.split('<')[0].strip() if '<' in message.from_email else 'WildDocs'
                    },
                    'To': to_list,
                    'Subject': message.subject,
                }
                
                # Add CC if present
                if message.cc:
                    msg_data['Cc'] = [{'Email': email} for email in message.cc]
                
                # Add BCC if present
                if message.bcc:
                    msg_data['Bcc'] = [{'Email': email} for email in message.bcc]
                
                # Check for HTML content
                html_content = None
                if hasattr(message, 'alternatives'):
                    for content, mimetype in message.alternatives:
                        if mimetype == 'text/html':
                            html_content = content
                            break
                
                if html_content:
                    msg_data['HTMLPart'] = html_content
                    msg_data['TextPart'] = message.body
                else:
                    msg_data['TextPart'] = message.body
                
                # Send via Mailjet API
                response = requests.post(
                    self.api_url,
                    auth=HTTPBasicAuth(self.api_key, self.secret_key),
                    json={'Messages': [msg_data]}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('Messages', [{}])[0].get('Status') == 'success':
                        sent_count += 1
                    elif not self.fail_silently:
                        raise Exception(f"Mailjet error: {result}")
                else:
                    if not self.fail_silently:
                        raise Exception(f"Mailjet API error: {response.status_code} - {response.text}")
                        
            except Exception as e:
                if not self.fail_silently:
                    raise
        
        return sent_count
