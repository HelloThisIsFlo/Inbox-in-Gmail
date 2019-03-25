from __future__ import print_function

import os.path
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


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


def main():
    # If modifying these scopes, delete the file token.pickle.
    credentials = Credentials(client_secrets_file='credentials.json',
                              token_file='token.pickle',
                              scopes=['https://www.googleapis.com/auth/gmail.readonly'])

    creds = credentials.get_creds()
    service = build('gmail', 'v1', credentials=creds)

    # Call the Gmail API
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    print_all_labels(labels)


def print_all_labels(labels):
    if not labels:
        print('No labels found.')
    else:
        print('Labels:')
        for label in labels:
            print(label['name'])


if __name__ == '__main__':
    main()
