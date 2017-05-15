from .store import Store
from requests_oauthlib import OAuth2Session

class GoogleDriveStore(Store):
    client_id = ''
    client_secret = ''
    redirect_uri = 'https://localhost'
    authorization_base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url = "https://www.googleapis.com/oauth2/v4/token"
    scope = [
        "https://www.googleapis.com/auth/drive.appfolder",
        "https://www.googleapis.com/auth/drive"
    ]

    def __init__(self):
        super()

    def getAuthorizeURL(self):
        self.google = OAuth2Session(self.client_id, scope=self.scope, redirect_uri=self.redirect_uri)
        authorization_url, state = self.google.authorization_url(self.authorization_base_url, access_type="offline",
                                                            approval_prompt="force")
        return authorization_url

    def fetchToken(self, redirect_response):
        token_dict = self.google.fetch_token(self.token_url, client_secret=self.client_secret,
                                        authorization_response=redirect_response)
        payload = {'id_token': token_dict['id_token']}
        r = self.google.get('https://www.googleapis.com/oauth2/v3/tokeninfo', params=payload);

    def downloadFile(self, meta):
        down_uri = 'https://www.googleapis.com/drive/v3/files/' + meta.id
        r = self.google.get(url=down_uri)
        return r.content

    def uploadFile(self, meta, data):
        r = self.google.post('https://www.googleapis.com/upload/drive/v3/files?uploadType=media',data=data)
        return r
