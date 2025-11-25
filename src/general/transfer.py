import uuid

class SaveResult:
    def __init__(self, filename: str, uuid: uuid):
        self.__filename = filename
        self.__uuid = uuid
    
    @property
    def filename(self): return self.__filename

    @property
    def uuid(self): return self.__uuid

class LoadResult:
    def __init__(self, content, content_type: str):
        self.__content = content
        self.__content_type = content_type

    @property
    def content(self): return self.__content

    @property
    def content_type(self): return self.__content_type
