#!/usr/bin/env python
import os
from yaml import load, dump
from watcher import Watcher
from s3 import Bucket
from subprocess import call

class Box:

    def __init__(self, path):
        self.path = path
        self.bucket = Bucket()
        self._loadfile()
        self.watcher = Watcher(path, self)

    def _loadfile(self):
        filepath = self.path + '/.box'
        if not os.path.isfile(filepath):
            call(['touch', filepath])
        with open(filepath) as f:
            print(f)
            filelist = load(f)
            print(filelist)

    def _addfile(self):
        pass



if __name__ == '__main__':
    Box('/media/storage/box')
