import os
import uuid

filename_to_uuid = {}
STORE_DIR = os.environ.get('STORE_DIR', './data')
os.makedirs(STORE_DIR, exist_ok = True)

def save(filename, content):
    """
    stores file

    :param filename:
    :param content:
    :return :
    """
    _, ext = os.path.splitext(filename)
    file_id = uuid.uuid1().hex + ext

    filename_to_uuid[filename] = file_id
    save_path = os.path.join(STORE_DIR, file_id)
    
    try:
        content.save(save_path)
    except Exception:
        return False

    return True

def load(filename):
    """
    fetches file
    """
    ...