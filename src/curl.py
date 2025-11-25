import os, io, pycurl

from urllib.parse import urlparse

from .error_handle.error import FileNotFound, InternalError

TIMEOUT = os.environ.get('TIMEOUT', 5)

class CurlError(Exception): pass

def process_header(raw_header):
    header_blocks = raw_header.strip().split('\r\n\r\n')
    last_block = header_blocks[-1] if header_blocks else ""

    header = {}

    for line in last_block.split('\r\n'):
        if not line or ":" not in line: continue

        key, value = line.split(":", 1)
        header[key.strip().lower()] = value.strip()

    return header

def curl_fetch(url):
    header_buf, body_buf = io.BytesIO(), io.BytesIO()

    c = pycurl.Curl()

    try:
        c.setopt(pycurl.URL, url.encode('utf-8'))
        c.setopt(pycurl.WRITEDATA, body_buf)
        c.setopt(pycurl.HEADERFUNCTION, header_buf.write)

        c.setopt(pycurl.FOLLOWLOCATION, True)

        c.setopt(pycurl.CONNECTTIMEOUT, TIMEOUT)
        c.setopt(pycurl.TIMEOUT, TIMEOUT)

        c.setopt(pycurl.SSL_VERIFYPEER, 0)
        c.setopt(pycurl.SSL_VERIFYHOST, 0)
        
        c.setopt(pycurl.VERBOSE, True)

        c.perform()

        status_code = c.getinfo(pycurl.RESPONSE_CODE)
    except pycurl.error as e:
        errno, errmsg = e.args

        if errno == 37: raise FileNotFound()
        else: raise InternalError(errmsg)
    finally:
        c.close()

        raw_header = header_buf.getvalue().decode("iso-8859-1", errors = "replace")
        header = process_header(raw_header)
        body = body_buf.getvalue()

    scheme = urlparse(url).scheme
    if scheme not in ['http', 'https'] and status_code == 0: status_code = 200

    return status_code, header, body
