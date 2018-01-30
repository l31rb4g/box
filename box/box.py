import os
import re
from yaml import load, dump
from watcher import Watcher
from s3 import Bucket
from subprocess import call

class Box:

    def __init__(self, path):
        self.path = path
        self.filepath = self.path + '/.box'
        if not os.path.isfile(self.filepath):
            call(['touch', self.filepath])

        self.bucket = Bucket()
        self.sync()

        self.watcher = Watcher(self.path, self)

    def load_bucket(self):
        ls = self.bucket.ls()
        return ls

    def load_file(self):
        with open(self.filepath) as f:
            r = f.read()
        return r

    def save_file(self, content):
        with open(self.filepath, 'w') as f:
            f.write(content)

    def load_folder(self):
        _files = os.listdir(self.path)
        _list = []
        for f in _files:
            if f != '.box':
                if os.path.isdir(self.path + '/' + f):
                    f += '/'
                _list.append({
                    'filename': f,
                    'size': os.path.getsize(self.path + '/' + f)
                })
        return _list

    def find_missing(self):
        bucket = self.load_bucket()
        folder = self.load_folder()
        print('bucket')
        print(bucket)
        print('folder')
        print(folder)
        missing = {
            'folder': [],
            'bucket': []
        }
        for bf in bucket:
            found = False
            for ff in folder:
                if ff['filename'] == bf['filename']:
                    found = True
            if not found:
                missing['folder'].append(bf)
        for ff in folder:
            found = False
            for bf in bucket:
                if ff['filename'] == bf['filename']:
                    found = True
            if not found:
                missing['bucket'].append(ff)
        return missing

    def sync(self):
        missing = self.find_missing()
        print('Missing:')
        print(missing)
        for mf in missing['folder']:
            filepath = self.path + '/' + mf['filename']
            if re.findall('/$', mf['filename']) and not os.path.isdir(filepath):
                os.mkdir(filepath)
            else:
                self.bucket.get(mf['filename'], filepath, mf['size'])

        for mf in missing['bucket']:
            filepath = self.path + '/' + mf['filename']
            if os.path.isdir(filepath):
                self.bucket.mkdir(mf['filename'])
            else:
                self.bucket.put(filepath, mf['filename'])

        print('\nAll synchronized!')


if __name__ == '__main__':
    Box('/media/storage/box')
