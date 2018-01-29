import time
from watchdog.observers import Observer
from event_handler import EventHandler


class Watcher:

    def __init__(self, path, bucket):
        self.path = path
        self.bucket = bucket
        self.observer = Observer()
        self.observer.schedule(EventHandler(self.bucket), path=self.path, recursive=True)
        self.observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()

        self.observer.join()
