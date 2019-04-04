from __future__ import print_function

import os.path
import pickle
from pprint import pprint

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from src.inboxingmail.dto import Label


class Credentials:
    def __init__(self, client_secrets_file, token_file, scopes):
        self._client_secrets_file = client_secrets_file
        self._token_file = token_file
        self._scopes = scopes
        self._creds = None

    def get_creds(self):
        if not self._already_logged_in():
            self._login()

        self._load_creds_from_file()

        if self._creds.valid:
            return self._creds

        elif self._can_refresh_creds():
            self._refresh_creds()
            self._save_creds_to_file()
            return self._creds

        else:
            self._logout()
            return self.get_creds()

    def _already_logged_in(self):
        return os.path.exists(self._token_file)

    def _login(self):
        self._perform_initial_oauth_to_get_creds()
        self._save_creds_to_file()

    def _perform_initial_oauth_to_get_creds(self):
        flow = InstalledAppFlow.from_client_secrets_file(self._client_secrets_file, self._scopes)
        self._creds = flow.run_local_server()

    def _save_creds_to_file(self):
        with open(self._token_file, 'wb') as token:
            pickle.dump(self._creds, token)

    def _load_creds_from_file(self):
        with open(self._token_file, 'rb') as token:
            self._creds = pickle.load(token)

    def _can_refresh_creds(self):
        return self._creds is not None and self._creds.expired and self._creds.refresh_token

    def _refresh_creds(self):
        self._creds.refresh(Request())

    def _logout(self):
        os.remove(self._token_file)


class Service:
    def __init__(self, valid_credentials):
        self._gmail_service = build('gmail', 'v1', credentials=valid_credentials)
        self._user = 'Shockn745@gmail.com'

    def get_all_email_ids_in_inbox(self, label_to_filter=None) -> [str]:
        def extract_messages_ids_from_current_page(resp):
            if 'messages' not in resp:
                return []
            return [msg['id'] for msg in resp['messages']]

        params = dict()
        params['userId'] = self._user
        # params['maxResults'] = 5
        if label_to_filter:
            label_id_to_filter = self.find_label_id(label_to_filter)
            params['labelIds'] = ['INBOX', label_id_to_filter]
        else:
            params['labelIds'] = ['INBOX']

        messages_ids = []
        resp = self._gmail_service.users().messages().list(**params).execute()
        pprint(resp)
        pprint(resp['messages'])
        pprint(len(resp['messages']))

        messages_ids += extract_messages_ids_from_current_page(resp)
        while 'nextPageToken' in resp:
            params['pageToken'] = resp['nextPageToken']
            resp = self._gmail_service.users().messages().list(**params).execute()
            messages_ids += extract_messages_ids_from_current_page(resp)

        return messages_ids

    def get_all_labels_names(self) -> [str]:
        labels = self._get_all_labels()
        return [label['name'] for label in labels]

    def _get_all_labels(self):
        resp = self._gmail_service.users().labels().list(userId=self._user).execute()
        return resp.get('labels', [])

    def find_label_id(self, label_name):
        labels = self._get_all_labels()
        for label in labels:
            if label['name'] == label_name:
                return label['id']
        raise LabelNotFoundError(label_name)

    def all_emails_in_inbox_and_in_a_category(self):
        emails_in_inbox_and_in_a_category = []

        # Do not include: 'CATEGORY_PERSONAL'
        # This one category are emails in NO "category"
        for category_label in ['CATEGORY_FORUMS',
                               'CATEGORY_SOCIAL',
                               'CATEGORY_UPDATES',
                               'CATEGORY_PROMOTIONS']:
            ids_with_label_in_inbox = self.get_all_email_ids_in_inbox(category_label)
            emails_in_inbox_and_in_a_category += ids_with_label_in_inbox

        return emails_in_inbox_and_in_a_category

    def all_emails_in_inbox_and_newsletter(self):
        newsletter_sublabels = [l for l in self.get_all_labels_names() if l.startswith('Newsletters/')]
        emails_in_inbox_and_newsletter = []
        for category_label in newsletter_sublabels:
            ids_with_label_in_inbox = self.get_all_email_ids_in_inbox(category_label)
            emails_in_inbox_and_newsletter += ids_with_label_in_inbox

        return emails_in_inbox_and_newsletter

    def add_label(self, email_ids: [str], label_name):
        label_id = self.find_label_id(label_name)

        if len(email_ids) >= 1000:
            raise RuntimeError("Not yet supported! (But WILL BE)")

        batch_modify_params = {'ids': email_ids, 'addLabelIds': [label_id]}
        self._gmail_service.users().messages().batchModify(userId=self._user, body=batch_modify_params).execute()

    def remove_label(self, email_ids: [str], label_name):
        label_id = self.find_label_id(label_name)

        if len(email_ids) >= 1000:
            raise RuntimeError("Not yet supported! (But WILL BE)")

        batch_modify_params = {'ids': email_ids, 'removeLabelIds': [label_id]}
        self._gmail_service.users().messages().batchModify(userId=self._user, body=batch_modify_params).execute()

    def get_message(self, msg_id):
        resp = self._gmail_service.users().messages().get(userId=self._user, id=msg_id, format='full').execute()
        return resp


class InboxInGmailError(Exception):
    pass


class LabelNotFoundError(InboxInGmailError):
    def __init__(self, label_name: str):
        super().__init__(f"Could not find label with name: '{label_name}'")


CATEGORY_LABEL = 'Label_1237931893308775983'


def add_CATEGORY_label_to_all_emails_in_a_category(service):
    emails_in_inbox_and_cat = service.all_emails_in_inbox_and_in_a_category()
    service.add_label(emails_in_inbox_and_cat, "CATEGORY")


def add_Newsletters_label_to_all_emails_in_a_newsletter(service):
    emails_in_inbox_and_news = service.all_emails_in_inbox_and_newsletter()
    service.add_label(emails_in_inbox_and_news, "Newsletters")


DEBUG_ANCHOR = Label("DEBUG_ANCHOR", "Label_1584439875888341384")


def main():
    # If modifying these scopes, delete the file token.pickle.
    credentials = Credentials(client_secrets_file='credentials.json',
                              token_file='token.pickle',
                              scopes=['https://mail.google.com/'])

    creds = credentials.get_creds()
    service = Service(creds)

    msg = service.get_message('169c4d948afb4ba7')
    pprint(msg)

    pprint(service._get_all_labels())


def old_experimentations():
    # e = service.get_all_email_ids_in_inbox("Newsletters")
    # service.remove_label(e, "Newsletters")

    # add_Newsletters_label_to_all_emails_in_a_newsletter(service)
    # service.get_all_email_ids_in_inbox()

    # print(service.find_label_id("DEBUG_ANCHOR"))

    # print(service.get_all_email_ids_in_inbox(DEBUG_ANCHOR.name))

    # add_Newsletters_label_to_all_emails_in_a_newsletter(service)
    # help(service._gmail_service.users().messages().batchModify)

    #
    # all_emails_in_inbox = service.get_all_email_ids_in_inbox()
    # pprint(all_emails_in_inbox)
    # pprint(len(all_emails_in_inbox))
    #
    #
    # email_in_inbox_in_NO_category = [e for e in all_emails_in_inbox if e not in emails_in_inbox_and_in_a_category]
    # email_in_PERSONAL_category = service.get_all_email_ids_in_inbox('CATEGORY_PERSONAL')
    # assert email_in_PERSONAL_category == email_in_inbox_in_NO_category

    topic = 'projects/project-id-6589131843582340474/topics/inbox'
    user = 'ShockN745@gmail.com'
    # test_watch = service.users().watch(userId=user, body={'topicName': topic}).execute()
    # pprint(test_watch)
    # help(service.users().watch)
    # help(service.users().watch(userId='shockn745@gmail.com'))
    # watch_emails = service.users().

    # POST
    # https: // www.googleapis.com / gmail / v1 / users / userId / watch

    # pprint(labels)


def print_all_labels(labels):
    if not labels:
        print('No labels found.')
    else:
        print('Labels:')
        for label in labels:
            print(label['name'])


if __name__ == '__main__':
    main()
