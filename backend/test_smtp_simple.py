"""Simple Gmail SMTP test"""

import smtplib

# Your credentials from .env
smtp_host = "smtp.gmail.com"
smtp_port = 587
smtp_username = "lakshmishac2002@gmail.com"
smtp_password = "fzrfxhaihisblywe"

print("Testing Gmail SMTP Connection...")
print(f"Host: {smtp_host}:{smtp_port}")
print(f"Username: {smtp_username}")
print(f"Password length: {len(smtp_password)}")
print()

try:
    print("Step 1: Connecting...")
    server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
    print("SUCCESS: Connected")

    print("Step 2: Starting TLS...")
    server.starttls()
    print("SUCCESS: TLS started")

    print("Step 3: Logging in...")
    server.login(smtp_username, smtp_password)
    print("SUCCESS: Login successful!")

    server.quit()
    print()
    print("ALL TESTS PASSED - Email is configured correctly!")

except smtplib.SMTPAuthenticationError as e:
    print(f"FAILED: Authentication error - {e}")
    print()
    print("Solution:")
    print("1. Go to: https://myaccount.google.com/apppasswords")
    print("2. Generate a new App Password")
    print("3. Copy it WITHOUT spaces")
    print("4. Update SMTP_PASSWORD in .env file")

except Exception as e:
    print(f"FAILED: {e}")
