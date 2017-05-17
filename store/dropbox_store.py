import json
from pathlib import PurePath
from . store import Store
from . directory_entry import DirectoryEntry
from exceptions import *
from requests_oauthlib import OAuth2Session


class DropboxStore(Store):
    __download_url = "https://content.dropboxapi.com/2/files/download"
    __delete_url = "https://api.dropboxapi.com/2/files/delete"
    __mkdir_url = "https://api.dropboxapi.com/2/files/create_folder"
    __list_url = "https://api.dropboxapi.com/2/files/list_folder"

    def __init__(self, global_config, name):
        super()
        # set Dropbox specific variables
        self.client_id = global_config['dropbox_client_id']
        self.client_secret = global_config['dropbox_client_secret']
        # TODO think proper way to store keys
        self.token_path = global_config['__project_dir'] / ('dropbox_token_{0}.json'.format(name))
        self.authorization_base_url = "https://www.dropbox.com/oauth2/authorize"
        self.token_url = "https://api.dropboxapi.com/oauth2/token"
        self.upload_url = "https://content.dropboxapi.com/2/files/upload"

        self.load_token()
        self.session = OAuth2Session(self.client_id, scope=self.scope, token=self.token,
                                     redirect_uri=self.redirect_url)

    def get_authorization_url(self):
        authorization_url, state = self.session.authorization_url(self.authorization_base_url)
        return authorization_url

    def download_file(self, path: PurePath):
        args = {
            'path': path.as_posix()
        }
        headers = {
            'Dropbox-API-Arg': json.dumps(args)
        }
        response = self.session.post(self.__download_url, headers=headers)
        # TODO handle download failure
        try:
            response.raise_for_status()
        except Exception:
            response = response.json()
            reason = response['error']['path']['.tag']
            if 'not_found' == reason:
                raise NoEntryError('download fail')
            else:
                raise Exception('download fail : reason = {0}'.format(reason))
        return response.content

    def upload_file(self, path: PurePath, data: bytes, is_chunk=False):
        # TODO handle chunk
        args = {
            'path': path.as_posix(),
            'mode': 'add'
        }
        headers = {
            'Content-Type': 'application/octet-stream',
            'Dropbox-API-Arg': json.dumps(args)
        }
        response = self.session.post(self.upload_url, data=data, headers=headers)
        # TODO handle upload failure
        response = response.json()
        if 'error' in response:
            reason = response['error']['reason']['.tag']
            if 'conflict' == reason:
                raise DuplicateEntryError('duplicate upload')
            elif 'malformed_path' == reason:
                raise NoEntryError('wrong path')
            else:
                raise Exception('upload fail : reason = {0}'.format(reason))

    def get_list(self, path):
        body = {'path': path.as_posix()}
        if body['path'] == '/':
            body['path'] = ''
        response = self.session.post(self.__list_url, data=json.dumps(body),
                                     headers={'Content-Type':'application/json'})
        results = []
        while True:
            # TODO
            try:
                response.raise_for_status()
            except Exception:
                response = response.json()
                if 'error' in response:
                    reason = response['error']['path']['.tag']
                    if 'not_found' == reason:
                        raise NoEntryError('get list fail')
                    else :
                        raise Exception('get list fail : reason = {0}'.format(reason))
            response = response.json()
            for file in response['entries']:
                entry = DirectoryEntry(file['name'])
                if file['.tag'] == 'folder':
                    entry.is_dir = True
                results.append(entry)
            # TODO handle chunk
            if response['has_more'] is False:
                break
            response = self.session.post(self.__list_url + '/continue',
                                         data=json.dumps({'cursor':response['cursor']}),
                                         headers={'Content-Type':'application/json'})
        return results

    def make_dir(self, path, name):
        body = {
            'path': (path/name).as_posix(),
            'autorename': False
        }
        response = self.session.post(self.__mkdir_url, data=json.dumps(body),
                                     headers={'Content-Type':'application/json'})
        # TODO
        response = response.json()
        if 'error' in response:
            reason = response['error']['path']['.tag']
            if 'conflict' == reason:
                raise DuplicateEntryError("make dir fail")
            elif 'insufficient_space' == reason:
                raise DiskFullError("make dir fail")
            else:
                raise Exception('make dir fail : reason = {0}'.format(reason))

    def remove(self, path):
        body = {
            'path': path.as_posix()
        }
        response = self.session.post(self.__delete_url, data=json.dumps(body),
                                     headers={'Content-Type': 'application/json'})
        # TODO handle remove fail
        response = response.json()
        if 'error' in response:
            reason = response['error']['.tag']
            if 'path_lookup' == reason:
                reason = response['error']['path_lookup']['.tag']
                if 'not_found' == reason:
                    raise NoEntryError('remove fail')
                else:
                    raise Exception('remove fail : reason = {0}'.format(reason))
            elif 'path_write' == reason:
                reason = response['error']['path_write']['.tag']
                raise Exception('remove fail : reason = {0}'.format(reason))
            raise Exception('remove fail : reason = {0}'.format(reason))