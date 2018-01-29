import re
from watchdog.events import PatternMatchingEventHandler


class EventHandler(PatternMatchingEventHandler):
    patterns = ['*']

    def __init__(self, bucket=None, patterns=None, ignore_patterns=None,
                 ignore_directories=False, case_sensitive=False):
        self.bucket = bucket
        super(PatternMatchingEventHandler, self).__init__()
        self._patterns = patterns
        self._ignore_patterns = ignore_patterns
        self._ignore_directories = ignore_directories
        self._case_sensitive = case_sensitive

    def _process(self, event):
        """
        event.event_type
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        """
        # the file will be processed there
        # print(event.src_path, event.event_type)  # print now only for degug
        # print(event.__dict__)
        # print(event.event_type, event.src_path, filename)

        filename = self._filename(event.src_path)

        if event.event_type == 'created':
            print('put', event.src_path, filename)
            self.bucket.put(event.src_path, filename)

        elif event.event_type == 'deleted':
            print('deleted', event.src_path, filename)
            self.bucket.delete(filename)

    def _filename(self, path):
        return re.sub(r'.*\/([^\/]+)$', r'\1', path)

    def on_modified(self, event):
        self._process(event)

    def on_created(self, event):
        self._process(event)

    def on_moved(self, event):
        self._process(event)

    def on_deleted(self, event):
        self._process(event)
