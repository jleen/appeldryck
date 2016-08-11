import sys
import time
import subprocess

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class BeableHandler(FileSystemEventHandler):

    def __init__(self, transform, output_dir):
        self.transform = transform
        self.output_dir = output_dir

    def on_any_event(self, event):
        if not event.is_directory:
            if event.event_type == 'deleted':
                print('Goodbye files!')
            else:
                print(self.transform + [event.src_path])


def alchemiter():
    observer = Observer()
    observer.schedule(BeableHandler(['cat'], 'build'), 'html')
    observer.schedule(BeableHandler(['sass'], 'build/css'), 'sass')
    observer.schedule(BeableHandler(
            ['babel', '--presets',
             '/usr/local/lib/node_modules/babel-preset-es2015'],
            'build'), 'js')
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
