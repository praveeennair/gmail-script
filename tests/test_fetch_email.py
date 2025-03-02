import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import base64
from dateutil.parser import parse

from fetch_emails import decode_body, fetch_emails, Email 


class TestEmailFetcher(unittest.TestCase):

    def test_decode_body_plain_text(self):
        parts = [
            {
                'mimeType': 'text/plain',
                'body': {'data': base64.urlsafe_b64encode(b'Hello, world!').decode('utf-8')}
            }
        ]
        self.assertEqual(decode_body(parts), 'Hello, world!')

    def test_decode_body_nested_parts(self):
        parts = [
            {
                'mimeType': 'multipart/alternative',
                'parts': [
                    {
                        'mimeType': 'text/plain',
                        'body': {'data': base64.urlsafe_b64encode(b'Nested text.').decode('utf-8')}
                    }
                ]
            }
        ]
        self.assertEqual(decode_body(parts), 'Nested text.')

    def test_decode_body_multiple_parts(self):
        parts = [
            {
                'mimeType': 'text/plain',
                'body': {'data': base64.urlsafe_b64encode(b'Part 1.').decode('utf-8')}
            },
            {
                'mimeType': 'text/plain',
                'body': {'data': base64.urlsafe_b64encode(b'Part 2.').decode('utf-8')}
            }
        ]
        self.assertEqual(decode_body(parts), 'Part 1.Part 2.')

    @patch('fetch_emails.build')
    @patch('fetch_emails.init_db')
    @patch('fetch_emails.get_session')
    @patch('fetch_emails.get_gmail_service')
    def test_fetch_emails(self, mock_get_gmail_service, mock_get_session, mock_init_db, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_list_execute = MagicMock()
        mock_list_execute.return_value = {'messages': [{'id': '123'}]}
        mock_service.users.return_value.messages.return_value.list.return_value.execute = mock_list_execute

        mock_get_execute = MagicMock()
        mock_get_execute.return_value = {
            'id': '123',
            'threadId': '456',
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'sender@example.com'},
                    {'name': 'To', 'value': 'recipient@example.com'},
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'Date', 'value': 'Tue, 12 Dec 2023 10:00:00 +0000'}
                ],
                'parts': [
                    {
                        'mimeType': 'text/plain',
                        'body': {'data': base64.urlsafe_b64encode(b'Test Body.').decode('utf-8')}
                    }
                ]
            },
            'labelIds': ['INBOX', 'IMPORTANT']
        }
        mock_service.users.return_value.messages.return_value.get.return_value.execute = mock_get_execute

        mock_engine = MagicMock()
        mock_init_db.return_value = mock_engine
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        fetch_emails()

        mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_get_gmail_service.return_value)
        mock_service.users.return_value.messages.return_value.list.assert_called_once_with(userId='me', labelIds=['INBOX'])
        mock_service.users.return_value.messages.return_value.get.assert_called_once_with(userId='me', id='123', format='full')
        mock_session.merge.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_get_session.assert_called_once_with(mock_engine)

        # Check that the Email object was created with the correct data
        email_args = mock_session.merge.call_args[0][0]
        self.assertEqual(email_args.id, '123')
        self.assertEqual(email_args.thread_id, '456')
        self.assertEqual(email_args.sender, 'sender@example.com')
        self.assertEqual(email_args.recipient, 'recipient@example.com')
        self.assertEqual(email_args.subject, 'Test Subject')
        self.assertEqual(email_args.body, 'Test Body.')
        self.assertEqual(email_args.received_date, parse('Tue, 12 Dec 2023 10:00:00 +0000'))
        self.assertEqual(email_args.labels, 'INBOX,IMPORTANT')

if __name__ == '__main__':
    unittest.main()