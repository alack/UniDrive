class NoEntryError(Exception):
    def __init__(self, message):
        self.message = message


class DuplicateEntryError(Exception):
    def __init__(self, message):
        self.message = message


class DiskFullError(Exception):
    def __init__(self, message):
        self.message = message