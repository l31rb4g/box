#!/usr/bin/env python
import os
from yaml import load, dump
from s3 import Bucket


class Box:

    boxfile = '.box'

    def __init__(self, path):
        self.path = path
        # _content = self._walk()
        # self._write_boxfile(dump(_content))
        # self.bucket = Bucket()
        # print(self.bucket.ls())
        self._list()

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
        print(_l)

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
