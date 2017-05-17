import json
from pathlib import PurePath
from abc import ABC, abstractclassmethod


class Store(ABC):
    authorization_base_url = ""
    token_url = ""
    redirect_url = "https://localhost"
    upload_url = ""
    scope = []
    token_path = None
    token = None
    session = None
    client_secret = ""
    client_id = ""

    def load_token(self):
        if self.token_path.exists():
            try:
                with open(self.token_path, 'r') as token_file:
                    self.token = json.loads(token_file.read())
            except json.JSONDecodeError:
                self.token = None

    def save_token(self, token=None):
        if token:
            self.token = token
        with open(self.token_path, 'w') as token_json:
            token_json.write(json.dumps(self.token, indent=4))

    def authorized(self):
        return self.session.authorized

    def get_authorization_url(self):
        authorization_url, state = self.session.authorization_url(self.authorization_base_url)
        return authorization_url

    def fetch_token(self, redirect_response):
        self.token = self.session.fetch_token(self.token_url, client_secret=self.client_secret,
                                              authorization_response=redirect_response)
        self.save_token()

    @abstractclassmethod
    def download_file(self, path: PurePath):
        pass

    @abstractclassmethod
    def upload_file(self, path: PurePath, data: bytes, is_chunk: bool):
        pass

    @abstractclassmethod
    def get_list(self, path: PurePath):
        pass

    @abstractclassmethod
    def make_dir(self, path: PurePath, name: str):
        pass

    @abstractclassmethod
    def remove(self, path: PurePath):
        pass