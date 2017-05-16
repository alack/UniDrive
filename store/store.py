from abc import ABC, abstractclassmethod

class Store(ABC):
    @abstractclassmethod
    def save_token(self, token):
        pass

    @abstractclassmethod
    def authorized(self):
        pass

    @abstractclassmethod
    def get_authorization_url(self):
        pass

    @abstractclassmethod
    def fetch_token(self, res):
        pass

    @abstractclassmethod
    def download_file(self, path):
        pass

    @abstractclassmethod
    def upload_file(self, path, data):
        pass

    @abstractclassmethod
    def get_list(self, path):
        pass

    @abstractclassmethod
    def make_dir(self, path, name):
        pass

    @abstractclassmethod
    def remove(self, path):
        pass