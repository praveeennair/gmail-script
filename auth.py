import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = {
    'fetch': ['https://www.googleapis.com/auth/gmail.readonly'],
    'process': [
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/gmail.labels'
    ]
}

def get_gmail_service(mode="fetch"):
  """
  """
  creds = None
  token_filename = "token.json"
  if os.path.exists(token_filename):
    creds = Credentials.from_authorized_user_file(token_filename, SCOPES.get(mode))
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES.get(mode)
      )
      creds = flow.run_local_server(port=0)
    with open(token_filename, "w") as token:
      token.write(creds.to_json())
    return creds
  