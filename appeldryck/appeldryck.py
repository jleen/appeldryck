import os
import sys
import time
import subprocess

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


DRYCKER = [
        ['html', 'build', ['cat']],
        ['sass', 'build/css', ['sass']],
        ['js', 'build', ['babel', '--presets',
                         '/usr/local/lib/node_modules/babel-preset-es2015']]
]


class Dricker(FileSystemEventHandler):

    def __init__(self, transform, output_dir):
        self.transform = transform
        self.output_dir = output_dir

    def on_any_event(self, event):
        if not event.is_directory:
            if event.event_type != 'deleted':
                dest = os.path.join(self.output_dir,
                                    os.path.basename(event.src_path))
                with open(dest, 'w') as out:
                    subprocess.Popen(self.transform + [event.src_path],
                                     stdout=out)
                print('Drack ' + dest)


def appeldryck():
    print('Appeldricker...')
    observer = Observer()
    for [src, dest, transform] in DRYCKER:
        observer.schedule(Dricker(transform, dest), src)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
