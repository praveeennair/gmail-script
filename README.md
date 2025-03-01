# Gmail Automation Tool

This project automates fetching and processing emails from Gmail using the Gmail API. It stores emails in a local database and applies rules to perform actions like marking emails as read, moving them to trash, etc.

## Features
- Fetch emails from Gmail and store them in a local SQLite database.
- Process emails based on customizable rules defined in `rules.json`.
- Supports actions like marking emails as read/unread and moving them to specific labels.

## Installation

### Prerequisites
- Python 3.7 or higher.
- A Google Cloud Platform (GCP) project with the Gmail API enabled.
- OAuth 2.0 credentials (`credentials.json`) from GCP.

### Steps
1. **Clone the repository**:
   ```bash
   git clone https://github.com/praveeennair/gmail-script
   cd gmail-script
   ```
### install the requirements
```bash
pip install -r requirements.txt
```
### Set up Gmail API credentials:

Download credentials.json from your GCP project and place it in the project root.

Run the following command to authenticate and generate token.json:
```bash
python auth.py
```

### Fetch Emails
```bash
python fetch_emails.py
```
### Process Emails
```bash
python process_emails.py
```
