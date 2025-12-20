"""
Debug script for Gmail SMTP authentication
"""

import smtplib

def test_gmail_connection():
    """Test Gmail SMTP connection with detailed debugging"""

    # Read directly from user input (hardcoded for testing)
    smtp_host = "smtp.gmail.com"
    smtp_port = 587
    smtp_username = "lakshmishac2002@gmail.com"
    smtp_password = "fzrfxhaihisblywe"  # Your password from .env

    print("=" * 60)
    print("Gmail SMTP Configuration Test")
    print("=" * 60)
    print(f"Host: {smtp_host}")
    print(f"Port: {smtp_port}")
    print(f"Username: {smtp_username}")
    print(f"Password length: {len(smtp_password) if smtp_password else 0} chars")
    print(f"Password (masked): {'*' * len(smtp_password) if smtp_password else 'NOT SET'}")
    print()

    # Check for common issues
    if not smtp_username or not smtp_password:
        print("❌ ERROR: SMTP_USERNAME or SMTP_PASSWORD not set in .env")
        return False

    if ' ' in smtp_password:
        print("⚠️  WARNING: Password contains spaces - Gmail app passwords should NOT have spaces")
        print("   Remove spaces from your app password in .env file")
        print()

    try:
        print("Step 1: Connecting to SMTP server...")
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        print("✅ Connected successfully")
        print()

        print("Step 2: Starting TLS encryption...")
        server.starttls()
        print("✅ TLS started successfully")
        print()

        print("Step 3: Attempting login...")
        server.login(smtp_username, smtp_password)
        print("✅ Login successful!")
        print()

        server.quit()

        print("=" * 60)
        print("✅ ALL TESTS PASSED - Email configuration is working!")
        print("=" * 60)
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ AUTHENTICATION FAILED: {e}")
        print()
        print("Common fixes:")
        print("1. Make sure you're using an App Password, not your regular Gmail password")
        print("   → Go to: https://myaccount.google.com/apppasswords")
        print("   → Generate a new app password")
        print("   → Copy it WITHOUT spaces (e.g., 'abcdabcdabcdabcd')")
        print()
        print("2. Ensure 2-Step Verification is enabled on your Google Account")
        print("   → Go to: https://myaccount.google.com/security")
        print()
        print("3. The password in .env should NOT have spaces or quotes")
        print("   Correct:   SMTP_PASSWORD=abcdabcdabcdabcd")
        print("   Wrong:     SMTP_PASSWORD=abcd abcd abcd abcd")
        print("   Wrong:     SMTP_PASSWORD=\"abcdabcdabcdabcd\"")
        return False

    except smtplib.SMTPException as e:
        print(f"❌ SMTP ERROR: {e}")
        return False

    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

if __name__ == "__main__":
    test_gmail_connection()
