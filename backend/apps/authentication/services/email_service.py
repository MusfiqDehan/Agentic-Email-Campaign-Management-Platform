class EmailService:
    """Stub email service; replace with real integration (e.g. SendGrid)."""
    def send_verification_email(self, to_email: str, token: str):
        print(f"[EmailService] Verification email to {to_email} token={token}")

    def send_password_reset_email(self, to_email: str, token: str):
        print(f"[EmailService] Password reset email to {to_email} token={token}")