import os
import re
import socket
import datetime
import base64
import hmac
import os.path
from urllib.parse import quote_plus
from hashlib import sha1
from time import sleep
from subprocess import check_output


class Bucket:

    bucket_name = ''
    access_key = ''
    secret_key = ''
    s3_subdomain = 's3'

    more_headers = {}
    debug = False

    def __init__(self, env='local'):
        self.method = None
        self.path = None
        self.mimetype = ''
        self.date = None
        self._set_credentials()

    def _set_credentials(self):
        with open('credentials', 'r') as f:
            content = f.read().split('\n')
            bucket = content[0]
            credentials = content[1].split(':')
            self.bucket_name = bucket
            self.access_key = credentials[0]
            self.secret_key = credentials[1]

    def _request(self, method='GET', path='', filename=None, **kwargs):
        self.method = method
        if path == '/':
            path = ''
        self.path = quote_plus(path)
        self.date = datetime.datetime.utcnow()
        zone = 'UTC'
        self.date = self.date.strftime('%a, %d %b %Y %H:%M:%S ') + zone
        hostname = self.s3_subdomain + '.amazonaws.com'
        hostname = self.bucket_name + '.' + hostname

        self._set_mimetype()
        _headers = ''
        for h in self.more_headers:
            _headers += h + ': ' + self.more_headers[h] + '\n'

        headers = self.method + ' /' + self.path + ' HTTP/1.0\n'
        headers += 'Host: ' + hostname + '\n'
        headers += _headers

        isdir = 'isdir' in kwargs and kwargs['isdir']

        if method == 'PUT' and 'x-amz-copy-source' not in self.more_headers:
            if not isdir:
                filesize = os.path.getsize(filename)
            else:
                filesize = 0
            headers += 'Content-type: ' + self.mimetype + '\n'
            headers += 'Content-length: ' + str(filesize) + '\n'
        elif method == 'DELETE':
            headers += 'Content-type: ' + self.mimetype + '\n'

        headers += 'Authorization: ' + self._auth().decode() + '\n'
        headers += 'Date: ' + self.date + '\n'
        headers += 'Connection: close\n'
        headers += '\n'

        s = socket.socket()
        s.settimeout(30)
        try:
            s.connect((hostname, 80))
        except Exception as e:
            print('>>> S3 :: ERROR: Unable to connect to', hostname)
            return False
        s.send(headers.encode())

        if not isdir:
            if method == 'PUT' and 'x-amz-copy-source' not in self.more_headers:
                headers += '--- data ---\n\n'
                sent = 0
                with open(filename, 'rb') as f:
                    while True:
                        chunk = f.read(4096)
                        try:
                            s.send(chunk)
                            sent += len(chunk)
                            if filesize > 0:
                                _msg = '\r>>> S3 :: Uploading {} - {}% '.format(path, round(sent / filesize * 100))
                                print(_msg, end='', flush=True)
                        except Exception as e:
                            print('>>> S3 :: ERROR: Unable to send data')
                            print(e)
                            return False
                        if not chunk:
                            break
                    print('')
                try:
                    s.send(b'\n\n')
                except Exception as e:
                    print('>>> S3 :: ERROR: Unable to finish upload')
                    print(e)
                    return False

        if self.debug:
            print(headers + '\n--------------\n')

        return s

    def _set_mimetype(self):
        if self.method in ['PUT']:
            _mime = check_output(['mimetype', self.path]).decode()
            self.mimetype = re.sub('.*: (.*)\n$', r'\1', _mime)
            if not self.mimetype:
                self.mimetype = 'application/octet-stream'
            if self.debug:
                print('\n>>> Mimetype computed: {}'.format(self.mimetype))

    def _auth(self):
        if re.findall('\?', self.path):
            self.path = re.findall('([^\?]+)\?(.*)', self.path)[0][0]

        auth_line = self.method.encode() + b'\n\n'

        if 'x-amz-copy-source' not in self.more_headers:
            auth_line += self.mimetype.encode()

        auth_line += b'\n' + self.date.encode() + b'\n'

        if 'x-amz-copy-source' in self.more_headers:
            auth_line += b'x-amz-copy-source:'
            auth_line += self.more_headers['x-amz-copy-source'].encode() + b'\n'

        auth_line += b'/' + self.bucket_name.encode() + b'/' + self.path.encode()

        r = base64.b64encode(hmac.new(
            self.secret_key.encode(),
            auth_line,
            sha1).digest())
        r = b'AWS ' + self.access_key.encode() + b':' + r

        if self.debug:
            print('\n============ auth ============\n' + auth_line.decode().replace('\r', '\\r').replace('\n', '\\n\n') + '\n============ /auth ============\n')

        return r

    def _add_header(self, key, value):
        self.more_headers[key] = value

    def _clear_headers(self):
        self.more_headers = {}

    def split_header(self, r):
        l = r.split(b'\r\n\r\n')
        responseHeaders = l[0]
        if len(l) > 1:
            l = l[1]
        else:
            l = None
        return responseHeaders, l

    def ls(self, path=None):
        if path:
            path = '/?prefix=' + path
        else:
            path = '/'
        s = self._request('GET', path)
        r = b''
        while True:
            l = s.recv(4096)
            r += l
            if self.debug:
                print(l)
            if not l:
                break
        s.close()
        content = []
        r = r.decode().split('<Key>')
        r.pop(0)
        for l in r:
            f = l.split('</Key>')[0]
            content.append(f)
        return content

    def get(self, remote_path, local_path, filesize=None):
        s = self._request('GET', remote_path)
        r = b''
        received = 0
        is_header = True
        while True:
            chunk = s.recv(4096)
            if not is_header:
                received += len(chunk)
            r += chunk
            print('\r>>> S3 :: Downloading {} - {} bytes '.format(local_path, received), end='', flush=True)
            if not chunk:
                break
            is_header = False

        if os.path.isdir(local_path):
            filename = re.findall('^(.*)/([^/]+)$', remote_path)[0][1]
            local_path += '/' + filename
        a = open(local_path, 'wb')
        content = self.split_header(r)[1]
        a.write(content)
        a.close()
        s.close()
        if re.findall(b'<Code>NoSuchKey</Code>', content):
            return False
        return local_path

    def put(self, local_path, remote_path):
        if os.path.isfile(local_path):
            s = self._request('PUT', remote_path, local_path)
            if s:
                s.close()
            else:
                print('retrying')
                sleep(3)
                self.put(local_path, remote_path)

    def delete(self, remote_path):
        print('>>> S3 :: Deleting', remote_path)
        s = self._request('DELETE', remote_path)
        if s:
            if self.debug:
                while True:
                    r = s.recv(4096)
                    print(r)
                    if not r:
                        break
            s.close()
        else:
            print('retrying')
            sleep(3)
            self.delete(remote_path)

    def copy(self, source_path, filename):
        self._add_header('x-amz-copy-source', '/' + self.bucket_name + source_path)
        s = self._request('PUT', filename)
        self._clear_headers()
        if s:
            if self.debug:
                while True:
                    r = s.recv(4096)
                    print(r)
                    if not r:
                        break
                        s.close()


    def url(self, filename):
        if filename:
            url = 'https://s3.amazonaws.com/' + self.bucket_name + filename
        return url
