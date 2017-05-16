# TODO class for directory, file and chunk
class DirectoryEntry:
    def __init__(self, name, is_chunk=False, is_directory=False, file_size=0):
        self.__node_name = name
        self.__is_chunk = is_chunk
        self.__is_dir = is_directory
        self.__file_size = file_size

    @property
    def name(self):
        return self.__node_name

    @property
    def is_dir(self):
        return self.__is_dir

    @is_dir.setter
    def is_dir(self, val):
        if val:
            self.__is_dir = True
        else:
            self.__is_dir = False

    @property
    def is_chunk(self):
        return self.__is_chunk

    @is_chunk.setter
    def is_chunk(self, val):
        if val:
            self.__is_chunk = True
        else:
            self.__is_chunk = False

    @property
    def file_size(self):
        return self.__file_size

    @file_size.setter
    def file_size(self, val):
        if val < 0:
            val = 0
        self.__file_size = val