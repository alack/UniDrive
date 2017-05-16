import pathlib
import webbrowser
from tests import BaseTestStoreMethods
from store import GoogleDriveStore


class TestGoogleDriveStore(BaseTestStoreMethods.TestStoreMethods):
    store_class = GoogleDriveStore

    def setUp(self):
        self.store = self.store_class(self.config, self.store_name)
        if self.store.authorized() is False:
            webbrowser.open(self.store.get_authorization_url())
            res = input('response url :')
            self.store.fetch_token(res)

    def tearDown(self):
        test_dir = pathlib.PurePath('/')
        entries = self.store.get_list(test_dir)
        for entry in entries:
            self.store.remove(test_dir / entry.name)
        del self.store
