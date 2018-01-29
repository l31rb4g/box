import re
import socket
import datetime
import base64
import hmac
import os.path
from hashlib import sha1
from time import sleep


class Bucket:

    bucket_name = ''
    access_key = ''
    secret_key = ''
    s3_subdomain = 's3'

    more_headers = ''
    debug = True

    def __init__(self, env='local'):
        self.method = None
        self.path = None
        self.type = ''
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

    def _request(self, method='GET', path='/', filename=None):
        self.method = method
        if path == '/':
            path = ''
        self.path = path
        self.date = datetime.datetime.utcnow()
        zone = 'UTC'
        self.date = self.date.strftime('%a, %d %b %Y %H:%M:%S ') + zone
        hostname = self.s3_subdomain + '.amazonaws.com'
        hostname = self.bucket_name + '.' + hostname
        is_put = method == 'PUT' and os.path.exists(filename)
        self.is_put = is_put
        is_delete = method == 'DELETE'

        headers = self.method + ' /' + self.path + ' HTTP/1.0\n'
        headers += 'Host: ' + hostname + '\n'
        headers += 'Date: ' + self.date + '\n'
        headers += 'Authorization: ' + self.auth().decode() + '\n'
        headers += 'Connection: close\n'
        headers += self.more_headers
        if is_put:
            filesize = str(os.path.getsize(filename))
            headers += 'Content-type: ' + self.type + '\n'
            headers += 'Content-length: ' + filesize + '\n'
        if is_delete:
            headers += 'Content-type: application/octet-stream\n'
        headers += '\n'

        s = socket.socket()
        s.settimeout(30)
        try:
            s.connect((hostname, 80))
        except Exception as e:
            print('Unable to connect')
            return False
        s.send(headers.encode())

        if is_put:
            f = open(filename, 'rb')
            headers += '--- data ---\n\n'
            for chunk in f:
                try:
                    s.send(chunk)
                except Exception as e:
                    print('unable to send data')
                    return False
            f.close()
            try:
                s.send(b'\n\n')
            except Exception as e:
                print(e)
                print('unable to end upload')
                return False

        if self.debug:
            print(headers + '\n--------------\n')
            r = ''
            l = s.recv(4096)
            while l:
                r += l.decode()
                try:
                    l = s.recv(4096)
                except:
                    pass
            print(r)
            print('\n--------------\n')

        return s

    def auth(self):
        if not self.type and self.is_put:
            self.type = 'application/octet-stream'
        if re.findall('\?', self.path):
            self.path = re.findall('([^\?]+)\?(.*)', self.path)[0][0]
        r = self.method + '\n\n' + self.type + '\n' + self.date + '\n' + '/' + self.bucket_name + '/' + self.path

        if self.debug:
            print('\n============\n' + r + '\n============\n')

        r = base64.b64encode(hmac.new(
            self.secret_key.encode(),
            r.encode(),
            sha1).digest())
        r = b'AWS ' + self.access_key.encode() + b':' + r
        return r

    def add_header(self, key, value):
        header = key + ': ' + value + '\n'
        self.more_headers += header

    def split_header(self, r):
        l = r.split('\r\n\r\n')
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
        r = ''
        l = s.recv(4096)
        while l:
            r += l.decode()
            l = s.recv(4096)
        s.close()

        content = []
        r = self.split_header(r)
        if r[1]:
            r = r[1]
            r = r.split('</Contents>')
            for l in r:
                if re.findall('<Contents>', l):
                    c = l.split('<Contents>')[1]
                    key = re.findall('<Key>(.*)</Key>', c)[0]
                    size = re.findall('<Size>(.*)</Size>', c)
                    if size:
                        size = int(size[0])
                        if size > 0:
                            filename = re.findall('(.*)/([^/]+)$', key)
                            if filename:
                                filename = filename[0][1]
                            else:
                                filename = key
                            obj = {
                                'key': key,
                                'size': size,
                                'url': self.url('/' + key),
                                'filename': filename
                            }
                            content.append(obj)
        else:
            if self.debug:
                print(r[0])

        return content

    def get(self, remote_path, local_path):
        s = self._request('GET', remote_path)
        r = ''
        l = s.recv(4096)
        while l:
            r += l
            l = s.recv(4096)
        if os.path.isdir(local_path):
            filename = re.findall('^(.*)/([^/]+)$', remote_path)[0][1]
            local_path += '/' + filename
        a = open(local_path, 'wb')
        content = self.split_header(r)[1]
        a.write(content)
        a.close()
        s.close()
        if re.findall('<Code>NoSuchKey</Code>', content):
            return False
        return local_path

    def put(self, local_path, remote_path):
        s = self._request('PUT', remote_path, local_path)
        if s:
            s.close()
        else:
            print('retrying')
            sleep(3)
            self.put(local_path, remote_path)

    def delete(self, remote_path):
        s = self._request('DELETE', remote_path)
        if s:
            s.close()
        else:
            print('retrying')
            sleep(3)
            self.delete(remote_path)

    def file_exists(self, remote_path):
        r = self.ls(remote_path)
        return len(r) > 0

    def move(self, old_path, new_path):
        """
        This method get a file in s3 with a old path and
        put this same file with a new_path
        old_path = '/media/audios/1.mp3'
        new_path = '/media/audios/1.ogg'
        return new_path
        """
        temp_path = '/tmp/%s' % os.path.basename(old_path)
        self.get(old_path,  temp_path)
        self.put(temp_path, new_path)
        self.delete(old_path)
        return new_path

    def url(self, filename):
        if filename:
            url = 'https://s3.amazonaws.com/' + self.bucket_name + filename
        return url
