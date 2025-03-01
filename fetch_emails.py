import base64
from googleapiclient.discovery import build
from dateutil.parser import parse
from auth import get_gmail_service
from database import init_db, Email, get_session

def decode_body(parts):
    body = ''
    for part in parts:
        if part['mimeType'] == 'text/plain':
            data = part['body'].get('data', '')
            body += base64.urlsafe_b64decode(data).decode('utf-8')
        elif 'parts' in part:
            body += decode_body(part['parts'])
    return body

def fetch_emails():
    service = build('gmail', 'v1', credentials=get_gmail_service('fetch'))
    engine = init_db()
    session = get_session(engine)
    
    results = service.users().messages().list(
        userId='me', labelIds=['INBOX']).execute()
    messages = results.get('messages', [])
    
    for msg in messages:
        message = service.users().messages().get(
            userId='me', id=msg['id'], format='full').execute()
        
        headers = {h['name']: h['value'] for h in message['payload']['headers']}
        
        email = Email(
            id=message['id'],
            thread_id=message['threadId'],
            sender=headers.get('From', ''),
            recipient=headers.get('To', ''),
            subject=headers.get('Subject', ''),
            body=decode_body(message['payload'].get('parts', [])),
            received_date=parse(headers['Date']),
            labels=','.join(message.get('labelIds', []))
        )
        
        session.merge(email)
    
    session.commit()
    print(f"Processed {len(messages)} emails")


if __name__ == "__main__":
  fetch_emails()