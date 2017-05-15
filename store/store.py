from abc import ABC, abstractclassmethod

class Store(ABC):
    @abstractclassmethod
    def getAuthorizationURL(self):
        pass

    @abstractclassmethod
    def fetchToken(self, res):
        pass

    @abstractclassmethod
    def downloadFile(self, meta):
        pass

    @abstractclassmethod
    def uploadFile(self, meta, data):
        pass