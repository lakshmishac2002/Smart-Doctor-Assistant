"""
Free Email Integration using Gmail SMTP

100% FREE - No API keys needed, just use your Gmail account
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class FreeEmailClient:
    """Free email client using Gmail SMTP"""
    
    def __init__(self):
        """Initialize with Gmail SMTP settings"""
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.sender_email = os.getenv("SENDER_EMAIL", self.smtp_username)
    
    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        body: str,
        html: bool = False
    ) -> Dict[str, Any]:
        """
        Send email via Gmail SMTP (100% FREE)
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (text or HTML)
            html: Whether body is HTML
            
        Returns:
            Result dictionary with success status
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            print(f"[SUCCESS] Email sent to {to_email}")
            return {
                "success": True,
                "message": f"Email sent successfully to {to_email}",
                "provider": "Gmail SMTP (FREE)"
            }

        except Exception as e:
            print(f"[ERROR] Email error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to send email. Check SMTP configuration in .env"
            }
    
    def send_appointment_confirmation(
        self, 
        patient_email: str,
        patient_name: str,
        doctor_name: str,
        appointment_date: str,
        appointment_time: str
    ) -> Dict[str, Any]:
        """
        Send appointment confirmation email with nice formatting
        
        Args:
            patient_email: Patient's email
            patient_name: Patient's name
            doctor_name: Doctor's name
            appointment_date: Date of appointment
            appointment_time: Time of appointment
            
        Returns:
            Result dictionary
        """
        subject = "Appointment Confirmation - Smart Doctor Assistant"
        
        # HTML email body
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <h2 style="color: #667eea;">✅ Appointment Confirmed</h2>
                    
                    <p>Dear {patient_name},</p>
                    
                    <p>Your appointment has been successfully booked!</p>
                    
                    <div style="background-color: #f8f9ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #667eea;">Appointment Details:</h3>
                        <p style="margin: 5px 0;"><strong>Doctor:</strong> {doctor_name}</p>
                        <p style="margin: 5px 0;"><strong>Date:</strong> {appointment_date}</p>
                        <p style="margin: 5px 0;"><strong>Time:</strong> {appointment_time}</p>
                    </div>
                    
                    <p><strong>Important Reminders:</strong></p>
                    <ul>
                        <li>Please arrive 10 minutes before your appointment</li>
                        <li>Bring your ID and insurance card</li>
                        <li>Bring any previous medical records if applicable</li>
                    </ul>
                    
                    <p>If you need to reschedule or cancel, please contact us at least 24 hours in advance.</p>
                    
                    <hr style="border: 1px solid #eee; margin: 20px 0;">
                    
                    <p style="color: #666; font-size: 12px;">
                        This is an automated message from Smart Doctor Assistant.<br>
                        Powered by FREE technology: Gmail SMTP
                    </p>
                </div>
            </body>
        </html>
        """
        
        return self.send_email(patient_email, subject, html_body, html=True)


# Global email client instance
email_client = None

def get_email_client() -> FreeEmailClient:
    """Get or create email client"""
    global email_client
    if email_client is None:
        email_client = FreeEmailClient()
    return email_client
