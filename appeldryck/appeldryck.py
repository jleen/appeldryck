from configparser import ConfigParser
import os
import subprocess
import sys
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class Dricker(FileSystemEventHandler):

    def __init__(self, transform, output_dir, ext):
        self.transform = transform
        self.output_dir = output_dir
        self.ext = ext

    def on_any_event(self, event):
        if not event.is_directory:
            if event.event_type != 'deleted':
                basename = os.path.basename(event.src_path)
                if self.ext:
                    basename = os.path.splitext(basename)[0] + '.' + self.ext
                dest = os.path.join(self.output_dir, basename)
                with open(dest, 'w') as out:
                    subprocess.Popen(self.transform + [event.src_path],
                                     stdout=out)
                print('Drack ' + dest)


def appeldryck():
    observer = Observer()

    drycker = ConfigParser()
    drycker.read('Dryckfile')

    for dryck in drycker:
        if dryck == 'DEFAULT':
            continue
        dest = drycker[dryck]['to']
        transform = drycker[dryck]['via'].split(' ')
        ext = drycker[dryck].get('ext', None)
        observer.schedule(Dricker(transform, dest, ext), dryck)

    print('Appeldricker...')
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
