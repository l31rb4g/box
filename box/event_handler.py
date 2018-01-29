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

    def process(self, event):
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
        # print('------------------------------')

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        filename = re.sub(r'.*\/([^\/]+)$', r'\1', event.src_path)
        self.process(event)
        print('put', event.src_path, filename)
        self.bucket.put(event.src_path, filename)

    def on_moved(self, event):
        self.process(event)

    def on_deleted(self, event):
        self.process(event)
