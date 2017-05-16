import pathlib
import json
import unittest
import webbrowser
from store import GoogleDriveStore
from exceptions import *


class TestGoogleDriveStore(unittest.TestCase):
    def setUp(self):
        self.__project_dir = (pathlib.Path(__file__).resolve()).parents[1]
        with open(self.__project_dir / 'config.json', 'r') as config_file:
            self.config = json.loads(config_file.read())
        self.config['__project_dir'] = self.__project_dir
        self.store = GoogleDriveStore(self.config, 'test')
        if self.store.authorized() is False:
            webbrowser.open(self.store.get_authorization_url())
            res = input('response url :')
            self.store.fetch_token(res)

    # TODO testcases below are common for store classes
    def test_authorized(self):
        self.assertTrue(self.store.authorized())

    def test_save_token(self):
        self.assertTrue(self.store.authorized())
        del self.store
        self.store = GoogleDriveStore(self.config, 'test')
        self.assertTrue(self.store.authorized())

    def test_upload_file(self):
        test_dir = pathlib.PurePath('/')
        test_data_name = 'sample1'
        test_path = test_dir / test_data_name
        with open(self.__project_dir / 'tests' / 'samples' / test_data_name, 'rb') as testfile:
            test_data = testfile.read()
        self.store.upload_file(test_path, test_data)
        entries = self.store.get_list(test_dir)
        found = False
        for entry in entries:
            if entry.name == test_data_name and entry.is_dir is False and entry.is_chunk is False:
                found = True
                break
        self.assertTrue(found)
        # clean
        self.store.remove(test_path)

    def test_download_file(self):
        test_dir = pathlib.PurePath('/')
        test_data_name = 'sample2'
        test_path = test_dir / test_data_name
        with open(self.__project_dir / 'tests' / 'samples' / test_data_name, 'rb') as testfile:
            test_data = testfile.read()
        self.store.upload_file(test_path, test_data)
        download_data = self.store.download_file(test_path)
        self.assertEqual(test_data, download_data)
        # clean
        self.store.remove(test_path)

    def test_make_directory(self):
        test_dir = pathlib.PurePath('/')
        test_dir_name = 'myDir1'
        self.store.make_dir(test_dir, test_dir_name)
        entries = self.store.get_list(test_dir)
        found = False
        for entry in entries:
            if entry.name == test_dir_name and entry.is_dir is True and entry.is_chunk is False:
                found = True
                break
        self.assertTrue(found)
        # clean
        self.store.remove(test_dir / test_dir_name)

    def test_get_list(self):
        test_samples_dir = pathlib.PurePath('/samples')
        sample_files = ['sample1', 'sample2', 'sample3']
        self.store.make_dir(test_samples_dir.parent, 'samples')
        for sample in sample_files:
            with open(self.__project_dir / 'tests' / 'samples'/ sample, 'rb') as infile:
                self.store.upload_file(test_samples_dir / sample, infile.read())
        entries = self.store.get_list(test_samples_dir)
        # we gonna check only names
        names = []
        for entry in entries:
            names.append(entry.name)
        self.assertCountEqual(sample_files, names)
        # clean
        self.store.remove(test_samples_dir)

    def test_delete_file(self):
        # upload one file
        test_path = pathlib.PurePath('/sample1')
        with open(self.__project_dir / 'tests' / 'samples' / 'sample1', 'rb') as testfile:
            self.store.upload_file(test_path, testfile.read())
        # try to download after removal
        self.store.remove(test_path)
        with self.assertRaises(NoEntryError):
            sample1_data = self.store.download_file(test_path)

    def test_delete_directory(self):
        # entries before upload samples directory
        test_root = pathlib.PurePath('/')
        before_upload = self.store.get_list(test_root)
        # upload samples directory
        test_samples_dir = pathlib.PurePath('/samples')
        sample_files = ['sample1', 'sample2', 'sample3']
        self.store.make_dir(test_samples_dir.parent, 'samples')
        for sample in sample_files:
            with open(self.__project_dir / 'tests' / 'samples' / sample, 'rb') as infile:
                self.store.upload_file(test_samples_dir / sample, infile.read())
        self.store.remove(test_samples_dir)
        # it will be same if removal was successful
        after_upload = self.store.get_list(test_root)
        self.assertCountEqual(before_upload, after_upload)

    def test_delete_entry_not_exists(self):
        test_path = pathlib.PurePath('/someEntry')
        with self.assertRaises(NoEntryError):
            self.store.remove(test_path)

    def test_upload_duplicate_name(self):
        test_path = pathlib.PurePath('/sample1')
        with open(self.__project_dir / 'tests' / 'samples' / 'sample1', 'rb') as testfile:
            self.store.upload_file(test_path, testfile.read())
        # same name but different content
        with open(self.__project_dir / 'tests' / 'samples' / 'sample2', 'rb') as testfile:
            with self.assertRaises(DuplicateEntryError):
                self.store.upload_file(test_path, testfile.read())
        # clean
        self.store.remove(test_path)

    def test_make_duplicate_directory(self):
        test_dir = pathlib.PurePath('/')
        test_dir_name = 'myDir1'
        self.store.make_dir(test_dir, test_dir_name)
        with self.assertRaises(DuplicateEntryError):
            self.store.make_dir(test_dir, test_dir_name)
        # clean
        self.store.remove(test_dir/test_dir_name)

    def test_download_file_not_exists(self):
        test_path = pathlib.PurePath('/sample1')
        with self.assertRaises(NoEntryError):
            data = self.store.download_file(test_path)

    def tearDown(self):
        dir = pathlib.PurePath('/')
        entries = self.store.get_list(dir)
        for entry in entries:
            self.store.remove(dir / entry.name)
        del self.store

if __name__ == '__main__':
    unittest.main()