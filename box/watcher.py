import time
from watchdog.observers import Observer
from event_handler import EventHandler


class Watcher:

    def __init__(self, path, box):
        self.path = path
        self.box = box
        self.observer = Observer()
        self.observer.schedule(EventHandler(self.box), path=self.path, recursive=True)
        self.observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()

        self.observer.join()
