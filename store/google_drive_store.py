import json
from typing import Dict
from pathlib import PurePath
from requests_oauthlib import OAuth2Session
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.encoders import encode_noop
from . store import Store
from . directory_entry import DirectoryEntry
from exceptions import *


class GoogleDriveStore(Store):
    __root_id = 'appDataFolder'
    __file_url = "https://www.googleapis.com/drive/v3/files/"
    # __token_info_url = "https://www.googleapis.com/oauth2/v3/tokeninfo"

    def __init__(self, global_config: Dict, name: str):
        super()
        # set GoogleDrive specific variables
        self.client_id = global_config['google_client_id']
        self.client_secret = global_config['google_client_secret']
        # TODO think proper way to store keys
        self.token_path = global_config['__project_dir'] / ('google_token_{0}.json'.format(name))
        self.authorization_base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.upload_url = "https://www.googleapis.com/upload/drive/v3/files"
        self.token_url = "https://www.googleapis.com/oauth2/v4/token"
        self.scope = [
            "https://www.googleapis.com/auth/drive.appfolder",
            "https://www.googleapis.com/auth/drive",
            "profile",
            "email",
            "openid"
        ]
        self.load_token()
        extra = {
            'client_id' : self.client_id,
            'client_secret' : self.client_secret
        }
        self.session = OAuth2Session(self.client_id, scope=self.scope, token=self.token,
                                     redirect_uri=self.redirect_url,
                                     auto_refresh_kwargs=extra,
                                     auto_refresh_url=self.token_url,
                                     token_updater=self.save_token)

    def get_authorization_url(self):
        authorization_url, state = self.session.authorization_url(self.authorization_base_url,
                                                                  access_type="offline")
        return authorization_url

    def search_files_with_parent_id(self, parent_id: str, filename=""):
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
            response = self.session.get(GoogleDriveStore.__file_url, params=params)
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

    def get_file_id(self, path: PurePath):
        parent_id = GoogleDriveStore.__root_id
        for filename  in path.parts[1:]:
            search = self.search_files_with_parent_id(parent_id, filename)
            if not search:
                raise NoEntryError('path is not valid')
            parent_id = search[0]['id']
        return parent_id

    def download_file(self, path: PurePath):
        file_id = self.get_file_id(path)
        file = self.__download_file(file_id)
        # TODO Handle download failure
        return file['data']

    def __download_file(self, file_id: str):
        file = {}
        url = GoogleDriveStore.__file_url + file_id
        r = self.session.get(url=url)
        # temporary
        r.raise_for_status()
        file['meta'] = r.json()

        r = self.session.get(url=url, params={'alt': 'media'})
        # TODO raise proper exceiption
        r.raise_for_status()
        file['data'] = r.content
        return file

    def upload_file(self, path: PurePath, data: bytes, is_chunk=False):
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
            # TODO handle upload failure
            return self.__upload_file(metadata, data)
        else:
            raise DuplicateEntryError('Duplicate path')

    def __upload_file(self, meta: Dict, data: bytes):
        related = MIMEMultipart('related', 'separator')
        mm = MIMEApplication(json.dumps(meta), 'json', encode_noop)
        mm.set_payload(json.dumps(meta))
        dd = MIMEApplication(data)
        related.attach(mm)
        related.attach(dd)
        body = related.as_string().split('\n\n', 1)[1]
        r = self.session.post(self.upload_url, data=body,
                              headers={'Content-Type':'multipart/related; boundary=separator'},
                              params={'uploadType': 'multipart'})
        # TODO raise proper exceiption
        r.raise_for_status()
        return r.json()

    def get_list(self, path: PurePath):
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

    def make_dir(self, path: PurePath, name: str):
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
            response = self.session.post(GoogleDriveStore.__file_url, data=json.dumps(metadata),
                                         headers={'Content-Type': 'application/json'})
            response.raise_for_status()
        else:
            raise DuplicateEntryError('Duplicate path')

    def remove(self, path: PurePath):
        # if path is directory all descendants will be deleted
        file_id = self.get_file_id(path)
        url = GoogleDriveStore.__file_url + file_id
        response = self.session.delete(url)
        response.raise_for_status()