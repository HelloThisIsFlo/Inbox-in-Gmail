from unittest.mock import patch

from pytest import fixture, mark

from src.inboxingmail.dto import Email
from src.inboxingmail.gmail import Gmail
from src.inboxingmail.rules import Rules


def test_yo():
    print("yo")


CATEGORY_LABEL_ID = "1234567890"


@fixture
def rules():
    with patch.object(Gmail, 'get_label_id') as get_label_id:
        get_label_id.side_effect = lambda label_id: {'CATEGORY': CATEGORY_LABEL_ID}[label_id]
        yield Rules()


@patch.object(Gmail, 'get_label_name')
def test_no_category_no_news__no_changes(get_label_name, rules):
    get_label_name.side_effect = lambda label_id: {'8888': 'some_label'}[label_id]

    emails = [Email('123', ['8888']),
              Email('345', [])]

    assert rules.tidy_up_inbox_by_adding_labels(emails) == []


@patch.object(Gmail, 'get_label_name')
def test_category_email__add_category_label(get_label_name, rules):
    get_label_name.side_effect = lambda label_id: {
        'CATEGORY_UPDATES': 'CATEGORY_UPDATES',
        'CATEGORY_SOCIAL': 'CATEGORY_SOCIAL',
        '8888': 'some_label',
        '9999': 'other_label'}[label_id]

    emails = [Email('123', ['CATEGORY_UPDATES']),
              Email('345', ['8888']),
              Email('345', ['9999', 'CATEGORY_SOCIAL'])]

    assert rules.tidy_up_inbox_by_adding_labels(emails) == [
        {'email': Email('123', ['CATEGORY_UPDATES']),
         'label_ids_to_add': [CATEGORY_LABEL_ID]},
        {'email': Email('345', ['9999', 'CATEGORY_SOCIAL']),
         'label_ids_to_add': [CATEGORY_LABEL_ID]}]
