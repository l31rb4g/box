#!/usr/bin/env python
import os
from yaml import load, dump
from s3 import Bucket


class Box:

    boxfile = '.box'

    def __init__(self, path):
        self.path = path
        self.bucket = Bucket()
        print(self.find_missing())

    def find_missing(self):
        bucket = self.bucket.ls()
        folder = self._list()
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
        return load(_content)


if __name__ == '__main__':
    Box('/media/storage/box')
