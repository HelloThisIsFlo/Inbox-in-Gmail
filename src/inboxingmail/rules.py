from src.inboxingmail.dto import Email
from src.inboxingmail.gmail import Gmail


class Rules:
    def __init__(self):
        self._gmail = Gmail()
        self._category_label_id = self._gmail.get_label_id("CATEGORY")

    def tidy_up_inbox_by_adding_labels(self, emails: [Email]):
        result = []

        for email in emails:
            for label_id in email.labels_ids:
                label_name = self._gmail.get_label_name(label_id)
                if label_name.startswith('CATEGORY_'):
                    result.append({'email': email, 'label_ids_to_add': [self._category_label_id]})

        return result
