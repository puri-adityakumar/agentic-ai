import os
from api.emailer.gmail_imap_parser import GmailImapParser

EMAIL_ADDRESS=os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD=os.environ.get("EMAIL_PASSWORD")


def read_inbox(hours_ago=24, unread_only=True, verbose=False):
    parser = GmailImapParser(
        email_address=EMAIL_ADDRESS,
        app_password=EMAIL_PASSWORD
    )

    # Fetch unread emails from last 24 hours
    emails = parser.fetch_emails(hours=hours_ago, unread_only=unread_only)

    if verbose:
        for email in emails:
            print(f"From: {email['from']}")
            print(f"Subject: {email['subject']}")
            print(f"Date: {email['timestamp']}")
            print("---")
    return emails

