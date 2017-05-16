from . store import Store
from . directory_entry import DirectoryEntry
from exceptions import *
import json
import pathlib
from requests_oauthlib import OAuth2Session
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.encoders import encode_noop


class GoogleDriveStore(Store):
    __redirect_base_url = "https://localhost"
    __root_id = 'appDataFolder'
    __authorization_base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    __token_url = "https://www.googleapis.com/oauth2/v4/token"
    __file_url = "https://www.googleapis.com/drive/v3/files/"
    __upload_url = "https://www.googleapis.com/upload/drive/v3/files"
    # __token_info_url = "https://www.googleapis.com/oauth2/v3/tokeninfo"
    __scope = [
        "https://www.googleapis.com/auth/drive.appfolder",
        "https://www.googleapis.com/auth/drive",
        "profile",
        "email",
        "openid"
    ]

    def __init__(self, global_config, name, redirect_port=None):
        super()
        if redirect_port:
            self.set_redirect_port(redirect_port)
        else:
            self.__redirect_url = GoogleDriveStore.__redirect_base_url

        self.__client_id = global_config['google_client_id']
        self.__client_secret = global_config['google_client_secret']
        self.__token_path = global_config['__project_dir'] / ('google_token_{0}.json'.format(name))
        if self.__token_path.exists():
            try:
                with open(self.__token_path, 'r') as tokenfile:
                    self.__token = json.loads(tokenfile.read())
            except json.JSONDecodeError:
                self.__token = None
        else:
            self.__token = None

        extra = {
            'client_id' : self.__client_id,
            'client_secret' : self.__client_secret
        }
        self.google = OAuth2Session(self.__client_id, scope=GoogleDriveStore.__scope, token=self.__token,
                                    redirect_uri=self.__redirect_url,
                                    auto_refresh_kwargs=extra,
                                    auto_refresh_url=GoogleDriveStore.__token_url,
                                    token_updater=self.save_token)

    def set_redirect_port(self, port):
        self.__redirect_url = "{0}:{1}".format(GoogleDriveStore.__redirect_base_url, port)

    def authorized(self):
        return self.google.authorized

    def save_token(self, token=None):
        if token:
            self.__token = token
        with open(self.__token_path, 'w') as token_json:
            token_json.write(json.dumps(self.__token, indent=4))

    def get_authorization_url(self):
        authorization_url, state = self.google.authorization_url(GoogleDriveStore.__authorization_base_url,
                                                                 access_type="offline", approval_prompt="force")
        return authorization_url

    def fetch_token(self, redirect_response):
        self.__token = self.google.fetch_token(GoogleDriveStore.__token_url, client_secret=self.__client_secret,
                                               authorization_response=redirect_response)
        self.save_token()

    def search_files_with_parent_id(self, parent_id, filename=""):
        params = {
            'corpora': 'user',
            'pageSize': 1000,
            'spaces': GoogleDriveStore.__root_id,
            'q': "'{0}' in parents".format(parent_id)
        }
        if filename:
            params['q'] = params['q'] + " and name = '{0}'".format(filename.replace("'",r"\'"))
        results = []
        while True:
            response = self.google.get(GoogleDriveStore.__file_url, params=params)
            response.raise_for_status()
            response = response.json()
            if 'files' in response:
                results.extend(response['files'])
            else:
                print(response.keys())

            if 'nextPageToken' in response:
                params['nextPageToken'] = response['nextPageToken']
            else:
                break

        return results

    def get_file_id(self, path):
        parent_id = GoogleDriveStore.__root_id
        for filename  in path.parts[1:]:
            search = self.search_files_with_parent_id(parent_id, filename)
            if not search:
                raise NoEntryError('path is not valid')
            parent_id = search[0]['id']
        return parent_id

    def download_file(self, path):
        if not isinstance(path, pathlib.PurePath):
            raise Exception('path is not instance of pathlib.PurePath')
        file_id = self.get_file_id(path)
        file = self.__download_file(file_id)
        return file['data']

    def __download_file(self, file_id):
        file = {}
        url = GoogleDriveStore.__file_url + file_id
        r = self.google.get(url=url)
        # temporary
        r.raise_for_status()
        file['meta'] = r.json()

        r = self.google.get(url=url, params={'alt':'media'})
        # temporary
        r.raise_for_status()
        file['data'] = r.content
        return file

    def upload_file(self, path, data, is_chunk=False):
        if not isinstance(path, pathlib.PurePath):
            raise Exception('path is not instance of pathlib.PurePath')

        # prevent duplicate path
        try:
            self.get_file_id(path)
        except NoEntryError:
            parent_id = self.get_file_id(path.parent)
            metadata = {
                'name': path.name,
                'parents': [parent_id]
            }
            if is_chunk:
                metadata['appProperties'] = {
                    'chunk': True
                }
            return self.__upload_file(metadata, data) # temporary
        else:
            raise DuplicateEntryError('Duplicate path')

    def __upload_file(self, meta, data):
        related = MIMEMultipart('related', 'separator')
        mm = MIMEApplication(json.dumps(meta), 'json', encode_noop)
        mm.set_payload(json.dumps(meta))
        dd = MIMEApplication(data)
        related.attach(mm)
        related.attach(dd)
        body = related.as_string().split('\n\n', 1)[1]
        r = self.google.post(GoogleDriveStore.__upload_url, data=body,
                             headers={'Content-Type':'multipart/related; boundary=separator'},
                             params={'uploadType': 'multipart'})
        # temporary
        r.raise_for_status()
        return r.json()

    def get_list(self, path):
        if not isinstance(path, pathlib.PurePath):
            raise Exception('path is not instance of pathlib.PurePath')
        parent_id = self.get_file_id(path)
        search = self.search_files_with_parent_id(parent_id)
        results = []
        for file in search:
            # TODO make file (virtual directory node) class which can express chunk, directory and file
            entry = DirectoryEntry(file['name'])
            if 'size' in file:
                entry.file_size(file['size'])

            if file['mimeType'] == 'application/vnd.google-apps.folder':
                entry.is_dir = True
            elif 'appProperties' in file:
                if 'chunk' in file['appProperties']:
                    entry.is_chunk = True
            results.append(entry)
        return results

    def make_dir(self, path, name):
        if not isinstance(path, pathlib.PurePath):
            raise Exception('path is not instance of pathlib.PurePath')
        try:
            test_path = path / name
            self.get_file_id(test_path)
        except NoEntryError:
            parent_id = self.get_file_id(path)
            metadata = {
                'parents' : [parent_id],
                'name' : name,
                'mimeType' : 'application/vnd.google-apps.folder'
            }
            response = self.google.post(GoogleDriveStore.__file_url, data=json.dumps(metadata),
                                        headers={'Content-Type': 'application/json'})
            response.raise_for_status()
        else:
            raise DuplicateEntryError('Duplicate path')

    def remove(self, path):
        # if path is directory all descendants will be deleted
        if not isinstance(path, pathlib.PurePath):
            raise Exception('path is not instance of pathlib.PurePath')
        file_id = self.get_file_id(path)
        url = GoogleDriveStore.__file_url + file_id
        response = self.google.delete(url)
        response.raise_for_status()