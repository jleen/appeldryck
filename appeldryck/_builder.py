from configparser import ConfigParser
import os
import stat
import subprocess
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class Dricker(FileSystemEventHandler):
    def __init__(self, transform, output_dir, ext):
        self.transform = transform
        self.output_dir = output_dir
        self.ext = ext

    def on_any_event(self, event):
        if not event.is_directory and event.type != 'deleted':
            drick(event.src_path, self.output_dir, self.transform, self.ext)


def get_dest(src, output_dir, ext):
    basename = os.path.basename(src)
    if ext:
        basename = os.path.splitext(basename)[0] + '.' + ext
    return os.path.join(output_dir, basename)


def drick(src, output_dir, transform, ext):
    dest = get_dest(src, output_dir, ext)
    with open(dest, 'w') as out:
        subprocess.Popen(transform + [src], stdout=out)
    print('Drack ' + dest)


def build():
    dryckfile = ConfigParser()
    dryckfile.read('Dryckfile')

    drycker = [{'from': key, **dryckfile[key]}
               for key in dryckfile if key != 'DEFAULT']

    for dryck in drycker:
        for file in os.listdir(dryck['from']):
            src = os.path.join(dryck['from'], file)
            ext = dryck.get('ext', None)
            dest = get_dest(src, dryck['to'], ext)
            if os.stat(src)[stat.ST_CTIME] > os.stat(dest)[stat.ST_CTIME]:
                drick(src, dryck['to'], dryck['via'].split(' '), ext)

    drick_and_stay_resident = True
    if drick_and_stay_resident:
        dsr(drycker)


def dsr(drycker):
    observer = Observer()

    for dryck in drycker:
        dest = dryck['to']
        transform = dryck['via'].split(' ')
        ext = dryck.get('ext', None)
        observer.schedule(Dricker(transform, dest, ext), dryck)

    print('Dricker...')
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
