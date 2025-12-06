"""
Custom Email Backend using Mailjet's HTTP API.
This bypasses SMTP port blocking on platforms like Render.
"""

from typing import Any, Dict, List, Optional

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail.backends.base import BaseEmailBackend
import requests
from requests.auth import HTTPBasicAuth


class MailjetAPIError(Exception):
    """Custom exception for Mailjet API errors."""


class MailjetEmailBackend(BaseEmailBackend):
    """
    Custom email backend that uses Mailjet's HTTP API instead of SMTP.
    This works on Render's free tier which blocks outbound SMTP ports.
    """
    
    def __init__(self, fail_silently: bool = False, **kwargs: Any) -> None:
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'MAILJET_API_KEY', '')
        self.secret_key = getattr(settings, 'MAILJET_SECRET_KEY', '')
        self.api_url = 'https://api.mailjet.com/v3.1/send'
    
    def _parse_from_email(self, from_email: str) -> Dict[str, str]:
        """Parse from_email into Email and Name components."""
        if '<' in from_email:
            return {
                'Email': from_email.split('<')[-1].rstrip('>'),
                'Name': from_email.split('<')[0].strip()
            }
        return {'Email': from_email, 'Name': 'WildDocs'}
    
    def _get_html_content(self, message: EmailMessage) -> Optional[str]:
        """Extract HTML content from email alternatives if present."""
        alternatives = getattr(message, 'alternatives', None)
        if not alternatives:
            return None
        for content, mimetype in alternatives:
            if mimetype == 'text/html':
                return content
        return None
    
    def _build_message_payload(self, message: EmailMessage) -> Dict[str, Any]:
        """Build the Mailjet message payload from an EmailMessage."""
        msg_data: Dict[str, Any] = {
            'From': self._parse_from_email(message.from_email),
            'To': [{'Email': email} for email in message.to],
            'Subject': message.subject,
        }
        
        if message.cc:
            msg_data['Cc'] = [{'Email': email} for email in message.cc]
        
        if message.bcc:
            msg_data['Bcc'] = [{'Email': email} for email in message.bcc]
        
        html_content = self._get_html_content(message)
        if html_content:
            msg_data['HTMLPart'] = html_content
            msg_data['TextPart'] = message.body
        else:
            msg_data['TextPart'] = message.body
        
        return msg_data
    
    def _send_single_message(self, message: EmailMessage) -> bool:
        """Send a single email message via Mailjet API. Returns True if successful."""
        msg_data = self._build_message_payload(message)
        
        response = requests.post(
            self.api_url,
            auth=HTTPBasicAuth(self.api_key, self.secret_key),
            json={'Messages': [msg_data]}
        )
        
        if response.status_code != 200:
            raise MailjetAPIError(f"Mailjet API error: {response.status_code} - {response.text}")
        
        result = response.json()
        if result.get('Messages', [{}])[0].get('Status') == 'success':
            return True
        
        raise MailjetAPIError(f"Mailjet error: {result}")
    
    def send_messages(self, email_messages: List[EmailMessage]) -> int:
        """Send one or more EmailMessage objects and return the number sent."""
        if not email_messages:
            return 0
        
        if not self.api_key or not self.secret_key:
            if not self.fail_silently:
                raise ValueError("MAILJET_API_KEY and MAILJET_SECRET_KEY must be configured")
            return 0
        
        sent_count = 0
        for message in email_messages:
            try:
                if self._send_single_message(message):
                    sent_count += 1
            except MailjetAPIError:
                if not self.fail_silently:
                    raise
        
        return sent_count
