import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json

from process_email import RuleEngine, GmailActionHandler, process_emails


class TestRuleEngine(unittest.TestCase):

    def setUp(self):
        with open('test_rules.json', 'w') as f:
            json.dump({
                'rules': [
                    {
                        'name': 'Test Rule',
                        'predicate': 'All',
                        'conditions': [
                            {'field': 'Sender', 'predicate': 'contains', 'value': 'test'},
                            {'field': 'Received Date', 'predicate': 'less_than', 'value': 7}
                        ],
                        'actions': [{'action': 'mark_as_read'}]
                    },
                    {
                        'name': 'Test Rule 2',
                        'predicate': 'Any',
                        'conditions': [
                            {'field': 'Subject', 'predicate': 'equals', 'value': 'Important'},
                            {'field': 'Received Date', 'predicate': 'greater_than', 'value': {'amount': 1, 'unit': 'months'}}
                        ],
                        'actions': [{'action': 'move_message', 'value': 'Test Label'}]
                    }
                ]
            }, f)
        self.rule_engine = RuleEngine(rules_file='test_rules.json')

    def tearDown(self):
        import os
        os.remove('test_rules.json')

    def test_evaluate_condition_string_contains(self):
        email = MagicMock(sender='test@example.com')
        condition = {'field': 'Sender', 'predicate': 'contains', 'value': 'test'}
        self.assertTrue(self.rule_engine.evaluate_condition(condition, email))

    def test_evaluate_condition_date_less_than(self):
        email = MagicMock(received_date=datetime.now() - timedelta(days=3))
        condition = {'field': 'Received Date', 'predicate': 'less_than', 'value': 6}
        self.assertTrue(self.rule_engine.evaluate_condition(condition, email))

    def test_evaluate_condition_date_greater_than_relativedelta(self):
        email = MagicMock(received_date=datetime.now() + relativedelta(months=2))
        condition = {'field': 'Received Date', 'predicate': 'greater_than', 'value': {'amount': 1, 'unit': 'months'}}
        self.assertTrue(self.rule_engine.evaluate_condition(condition, email))

    def test_evaluate_rule_all_conditions_met(self):
        email = MagicMock(sender='test@example.com', received_date=datetime.now() - timedelta(days=5))
        rule = self.rule_engine.rules[0]
        self.assertTrue(self.rule_engine.evaluate_rule(rule, email))

    def test_evaluate_rule_any_conditions_met(self):
        email = MagicMock(subject='Important', received_date=datetime.now() - timedelta(days=5))
        rule = self.rule_engine.rules[1]
        self.assertTrue(self.rule_engine.evaluate_rule(rule, email))

class TestGmailActionHandler(unittest.TestCase):

    @patch('process_email.get_gmail_service')
    def setUp(self, mock_get_gmail_service):
        self.mock_service = MagicMock()
        mock_get_gmail_service.return_value = self.mock_service
        self.action_handler = GmailActionHandler()

    def test_execute_actions_mark_as_read(self):
        email = MagicMock(id='123', labels='UNREAD,IMPORTANT')
        self.action_handler.execute_actions(email, [{'action': 'mark_as_read'}])
        self.mock_service.users.return_value.messages.return_value.modify.assert_called_once()
        self.assertEqual(email.labels, 'IMPORTANT')

    def test_execute_actions_mark_as_unread(self):
        email = MagicMock()
        email.id = '123'
        email.labels = 'IMPORTANT'
        self.action_handler.service = MagicMock()
        self.action_handler.execute_actions(email, [{'action': 'mark_as_unread'}])
        self.action_handler.service.users.return_value.messages.return_value.modify.assert_called_once_with(
            userId='me',
            id='123',
            body={'addLabelIds': ['UNREAD'], 'removeLabelIds': []}
        )
        self.assertEqual(email.labels, 'IMPORTANT,UNREAD')



if __name__ == '__main__':
    unittest.main()