#!/usr/bin/env python
import os
import re
from yaml import load, dump
from s3 import Bucket
from watcher import Watcher


class Box:

    boxfile = '.box'

    def __init__(self, path):
        self.path = path
        self.bucket = Bucket()
        self.sync()
        self.watcher = Watcher(self.path, self)

    def _list(self):
        _l = []
        for (dirpath, dirnames, filenames) in os.walk(self.path):
            for f in filenames:
                if f != '.box':
                    _path = dirpath.replace(self.path, '')
                    if _path:
                        _path = _path[1:] + '/'
                        if _path not in _l:
                            _l.append(_path)
                    _l.append(_path + f)
        return _l

    def _walk(self):
        _list = {}
        for (dirpath, dirnames, filenames) in os.walk(self.path):
            if dirpath == self.path:
                dirpath = '.'
            else:
                dirpath = dirpath.replace(self.path + '/', '')
            paths = dirpath.split('/')
            cwd = _list
            for p in paths:
                if p not in cwd:
                    cwd[p] = filenames if p == '.' else {'.': filenames}
                cwd = cwd[p]
        return _list

    def _write_boxfile(self, content):
        _head = '# ' + ('=' * 41) + ' #'
        _head += "\n# Auto-generated file. Please do not edit.  #\n"
        _head += '# ' + ('=' * 41) + ' #\n\n'
        with open(self.path + '/' + self.boxfile, 'w') as f:
            content = _head + content
            f.write(content)

    def _read_boxfile(self):
        _content = None
        with open(self.path + '/' + self.boxfile, 'r') as f:
            _content = f.read()
        return _content

    def find_missing(self):
        bucket = self.bucket.ls()
        folder = self._list()
        missing = {
            'folder': [],
            'bucket': []
        }
        for bf in bucket:
            if bf not in folder:
                missing['folder'].append(bf)
        for ff in folder:
            if ff not in bucket:
                if not re.findall('/$', ff):
                    missing['bucket'].append(ff)
        return missing

    def sync(self):
        missing = self.find_missing()
        print('>>> Box :: Missing files:', missing)
        for mf in missing['folder']:
            filepath = self.path + '/' + mf
            if re.findall('/$', mf) and not os.path.isdir(filepath):
                print('>>> Box :: Creating directory', filepath)
                os.mkdir(filepath)
            else:
                print('>>> Box :: Downloading', mf)
                self._create_dirs(filepath)
                self.bucket.get(mf, filepath)

        for mf in missing['bucket']:
            filepath = self.path + '/' + mf
            if not os.path.isdir(filepath):
                print('>>> Box :: Uploading', mf)
                self.bucket.put(filepath, mf)

        print('>>> Box :: Synchronized!')


    def _create_dirs(self, filepath):
        path = '/'.join(filepath.split('/')[0:-1])
        if not os.path.isdir(path):
            print('>>> Box :: Creating directories for', path)
            os.makedirs(path)
