import os
import smtplib
import ssl
import logging
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()



def send_otp_email(to_email: str, otp_code: str, first_name:str, last_name:str) -> None:
    """
    Send OTP to the user's email using SMTP settings from environment variables or .env file.
    If SMTP settings are not provided, this will print the OTP to stdout (dev fallback).
    
    Supported env vars:
      SMTP_HOST (default: smtp.gmail.com)
      SMTP_PORT (default: 465 for SMTPS, or 587 for STARTTLS)
      SMTP_USER
      SMTP_PASSWORD
      SMTP_FROM (defaults to SMTP_USER)
    """
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    try:
        smtp_port = int(os.getenv("SMTP_PORT", "465"))
    except ValueError:
        smtp_port = 587
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM", smtp_user)

    
    subject = "Your OTP for Todo Application"
    body =(
        
        f"Dear {first_name} {last_name},\n\n"
      f"Your verification OTP is: {otp_code}.\n\n"
          f"If you didn't request this, ignore this message."
        )

    print(smtp_user, smtp_password, smtp_from, "these are the credentials")
    if not smtp_host or not smtp_user or not smtp_password:
        # Development fallback — print to console so you can copy the OTP during testing
        print(f"[DEV EMAIL] To: {to_email} Subject: {subject}\n{body}")
        return

    msg = EmailMessage()
    msg["From"] = smtp_from
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        context = ssl.create_default_context()
        if smtp_port == 465:
            # SMTPS: implicit SSL, no starttls() call needed
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
        else:
            # STARTTLS: explicit starttls() after EHLO
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
        
        logging.info("Sent OTP email to %s via %s:%s", to_email, smtp_host, smtp_port)
    except Exception as exc:
        # Log the error and fall back to printing the OTP for development
        logging.exception("Failed to send OTP email to %s: %s", to_email, exc)
        print(f"[DEV EMAIL] To: {to_email} Subject: {subject}\n{body}")
# ...existing code...