import os, uuid

from .curl import curl_fetch
from .general.transfer import SaveResult, LoadResult


FILENAME_TO_UUID = {}
STORE_DIR = os.environ.get('STORE_DIR', './data')
os.makedirs(STORE_DIR, exist_ok = True)

def save(filename, content) -> SaveResult | None:
    """
    stores file

    :param filename:
    :type str:
    :param content:
    :type werkzeug.datastructures.file_storage.FileStorage:
    
    :returns: SaveResult | None
    """
    _, ext = os.path.splitext(filename)
    file_id = uuid.uuid1().hex + ext

    FILENAME_TO_UUID[filename] = file_id
    save_path = os.path.join(STORE_DIR, file_id)
    
    try:
        content.save(save_path)
    except Exception as e:
        raise e
    
    return SaveResult(filename, file_id)

def load(uri) -> LoadResult | None:
    """
    fetches file

    :param uri:
    :type str:

    :returns: LoadResult | None
    """
    try:
        _, header, body = curl_fetch(uri)
    except Exception as e:
        raise e
    
    return LoadResult(body, header.get("content-type", "appplication/octet-stream"))
