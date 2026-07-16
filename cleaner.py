import os
import re
from collections import defaultdict
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def extract_domain(sender):
    match = re.search(r'@([\w\.\-]+)', sender)
    if match:
        domain = match.group(1).lower()
        parts = domain.split('.')
        if len(parts) >= 2:
            return parts[-2]
    return None

def get_all_emails(service):
    print("📬 Fetching all emails — this may take a while...\n")
    messages = []
    page_token = None
    page = 0

    while True:
        page += 1
        print(f"   Fetching page {page} ({len(messages)} emails so far)...")
        kwargs = {'userId': 'me', 'maxResults': 500}
        if page_token:
            kwargs['pageToken'] = page_token
        results = service.users().messages().list(**kwargs).execute()
        batch = results.get('messages', [])
        messages.extend(batch)
        page_token = results.get('nextPageToken')
        if not page_token:
            break

    print(f"\n✅ Found {len(messages)} total emails\n")
    return messages

def get_sender(service, msg_id):
    msg = service.users().messages().get(
        userId='me',
        id=msg_id,
        format='metadata',
        metadataHeaders=['From']
    ).execute()
    headers = {h['name']: h['value'] for h in msg['payload']['headers']}
    return headers.get('From', ''), msg_id

def get_or_create_label(service, name):
    labels = service.users().labels().list(userId='me').execute().get('labels', [])
    for label in labels:
        if label['name'].lower() == name.lower():
            return label['id']
    new_label = service.users().labels().create(
        userId='me',
        body={'name': name, 'labelListVisibility': 'labelShow', 'messageListVisibility': 'show'}
    ).execute()
    return new_label['id']

def apply_label(service, msg_id, label_id):
    service.users().messages().modify(
        userId='me',
        id=msg_id,
        body={'addLabelIds': [label_id]}
    ).execute()

if __name__ == "__main__":
    service = get_service()

    # Step 1 — fetch all emails
    all_messages = get_all_emails(service)

    # Step 2 — count emails per sender domain
    print("🔍 Analysing senders...\n")
    sender_emails = defaultdict(list)
    total = len(all_messages)

    for i, msg in enumerate(all_messages):
        if i % 100 == 0:
            print(f"   Processing {i}/{total}...")
        sender, msg_id = get_sender(service, msg['id'])
        domain = extract_domain(sender)
        if domain:
            sender_emails[domain].append(msg_id)

    # Step 3 — find senders with 100+ emails
    print("\n📊 Senders with 100+ emails:")
    print("=" * 55)
    bulk_senders = {k: v for k, v in sender_emails.items() if len(v) >= 100}
    for domain, emails in sorted(bulk_senders.items(), key=lambda x: -len(x[1])):
        print(f"  {domain:30} — {len(emails)} emails")
    print("=" * 55)
    print(f"\nFound {len(bulk_senders)} senders to label\n")

    # Step 4 — create labels and apply
    for domain, emails in bulk_senders.items():
        label_name = f"Auto/{domain.capitalize()}"
        print(f"📁 Creating label '{label_name}' for {len(emails)} emails...")
        label_id = get_or_create_label(service, label_name)
        for msg_id in emails:
            apply_label(service, msg_id, label_id)
        print(f"   ✅ Done")

    print(f"\n✅ Inbox organised! {len(bulk_senders)} labels created.")