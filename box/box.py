#!/usr/bin/env python
import os
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

        self.watcher = Watcher(path, self)

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
                _list.append({
                    'filename': f,
                    'size': os.path.getsize(self.path + '/' + f)
                })
        return _list

    def find_missing(self):
        bucket = self.load_bucket()
        folder = self.load_folder()
        missing = {
            'folder': [],
            'bucket': []
        }
        for bf in bucket:
            found = False
            for ff in folder:
                if ff == bf:
                    found = True
            if not found:
                missing['folder'].append(bf)
        for ff in folder:
            found = False
            for bf in bucket:
                if ff == bf:
                    found = True
            if not found:
                missing['bucket'].append(ff)
        return missing

    def sync(self):
        missing = self.find_missing()
        print('Missing:')
        print(missing)
        for mf in missing['folder']:
            self.bucket.get(mf['filename'], self.path + '/' + mf['filename'], mf['size'])
        for mf in missing['bucket']:
            self.bucket.put(self.path + '/' + mf['filename'], mf['filename'])

        print('\nAll synchronized!')


if __name__ == '__main__':
    Box('/media/storage/box')
