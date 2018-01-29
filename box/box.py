#!/usr/bin/env python
from watcher import Watcher
from s3 import Bucket

class Box:

    def __init__(self, path):
        self.path = path
        self.bucket = Bucket()
        self.watcher = Watcher(path, self.bucket)


if __name__ == '__main__':
    Box('/media/storage/box')
