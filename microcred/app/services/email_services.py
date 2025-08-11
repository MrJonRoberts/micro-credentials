import smtplib, os
from email.message import EmailMessage

class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_pass = os.getenv("SMTP_PASS")

    def send_award_notification(self, to_email: str, award_name: str):
        if not self.smtp_host or not to_email:
            return False
        msg = EmailMessage()
        msg["Subject"] = f"You’ve earned: {award_name}"
        msg["From"] = self.smtp_user or "no-reply@example.com"
        msg["To"] = to_email
        msg.set_content(f"Congrats! You received the '{award_name}' badge.")
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as s:
            s.starttls()
            if self.smtp_user and self.smtp_pass:
                s.login(self.smtp_user, self.smtp_pass)
            s.send_message(msg)
        return True
