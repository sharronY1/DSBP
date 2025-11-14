"""
Email utilities for sending invitations
"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
from backend.config import settings


async def send_invitation_email(
    to_email: str,
    inviter_name: str,
    project_name: str,
    invitation_token: str,
    invitation_url: str,
) -> bool:
    """Send an invitation email"""
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = f"Invitation to join {project_name} on DSBP"
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = to_email
        
        # Create the HTML email body
        html_template = """
        <html>
          <body>
            <h2>You've been invited to join a project!</h2>
            <p>Hello,</p>
            <p>{{ inviter_name }} has invited you to join the project <strong>{{ project_name }}</strong> on DSBP.</p>
            <p>Click the link below to accept the invitation:</p>
            <p><a href="{{ invitation_url }}?token={{ invitation_token }}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Accept Invitation</a></p>
            <p>Or copy and paste this URL into your browser:</p>
            <p>{{ invitation_url }}?token={{ invitation_token }}</p>
            <p>This invitation will expire in 7 days.</p>
            <p>Best regards,<br>The DSBP Team</p>
          </body>
        </html>
        """
        
        template = Template(html_template)
        html_body = template.render(
            inviter_name=inviter_name,
            project_name=project_name,
            invitation_url=invitation_url,
            invitation_token=invitation_token,
        )
        
        message.attach(MIMEText(html_body, "html"))
        
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=True,
        )
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

