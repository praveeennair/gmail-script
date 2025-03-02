import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from googleapiclient.discovery import build
from database import init_db, Email, get_session
from auth import get_gmail_service

class RuleEngine:
    def __init__(self, rules_file='rules.json'):
        with open(rules_file) as f:
            self.rules = json.load(f)['rules']
    
    def evaluate_condition(self, condition, email):
        field = condition['field']
        predicate = condition['predicate']
        value = condition['value']
        email_value = getattr(email, field.lower().replace(' ', '_'), None)

        if field == 'Received Date':
            return self._evaluate_date(predicate, email_value, value)
        else:
            return self._evaluate_string(predicate, str(email_value), value)

    def _evaluate_date(self, predicate, email_date, value):
        if isinstance(value, dict):
            amount = value['amount']
            unit = value['unit']
            delta = relativedelta(**{unit: amount})
        else:
            delta = timedelta(days=value)

        if predicate == 'less_than':
            threshold = datetime.now() - delta
            return email_date > threshold
        elif predicate == 'greater_than':
            threshold = datetime.now() + delta
            return email_date > threshold
        else:
            return False 

    def _evaluate_string(self, predicate, email_value, value):
        if email_value is None:
            return False
        email_value = str(email_value).lower()
        value = str(value).lower()

        return {
            'contains': value in email_value,
            'does_not_contain': value not in email_value,
            'equals': email_value == value,
            'does_not_equal': email_value != value
        }.get(predicate, False)

    def evaluate_rule(self, rule, email):
        results = [self.evaluate_condition(c, email) for c in rule['conditions']]
        return all(results) if rule['predicate'] == 'All' else any(results)

class GmailActionHandler:
    def __init__(self):
        # Use the 'process' scope from auth.py
        self.cred = get_gmail_service('process')
        self.service = build('gmail', 'v1', credentials=self.cred)
    
    def execute_actions(self, email, actions):
        label_updates = {'addLabelIds': [], 'removeLabelIds': []}
        current_labels = set(email.labels.split(',')) if email.labels else set()
        
        for action in actions:
            action_type = action['action']
            
            if action_type == 'mark_as_read':
                if 'UNREAD' in current_labels:
                    label_updates['removeLabelIds'].append('UNREAD')
            elif action_type == 'mark_as_unread':
                if 'UNREAD' not in current_labels:
                    label_updates['addLabelIds'].append('UNREAD')
            elif action_type == 'move_message':
                label_id = self._get_or_create_label(action['value'])
                if label_id and label_id not in current_labels:
                    label_updates['addLabelIds'].append(label_id)
        
        if label_updates['addLabelIds'] or label_updates['removeLabelIds']:
            self.service.users().messages().modify(
                userId='me', id=email.id, body=label_updates).execute()
            
            # Update local copy
            new_labels = current_labels - set(label_updates['removeLabelIds'])
            new_labels.update(label_updates['addLabelIds'])
            email.labels = ','.join(new_labels)

    def _get_or_create_label(self, label_name):
        results = self.service.users().labels().list(userId='me').execute()
        for label in results.get('labels', []):
            if label['name'] == label_name:
                return label['id']
        
        try:
            new_label = self.service.users().labels().create(
                userId='me',
                body={'name': label_name, 'labelListVisibility': 'labelShow'}
            ).execute()
            return new_label['id']
        except Exception as e:
            print(f"Error creating label: {e}")
            return None

def process_emails():
    engine = init_db()
    session = get_session(engine)
    rule_engine = RuleEngine()
    action_handler = GmailActionHandler()

    for email in session.query(Email).all():
        for rule in rule_engine.rules:
            if rule_engine.evaluate_rule(rule, email):
                action_handler.execute_actions(email, rule['actions'])
    
    session.commit()

if __name__ == "__main__":
    process_emails()