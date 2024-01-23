import importlib
import importlib.util
import inspect
import os
import shutil

from pathlib import Path

import appeldryck


SRC = 'site'
DEST = 'dist'

def build():
    if not Path('./dryck.py').exists:
        ctx = appeldryck.HtmlContext()
    else:
        loader = importlib.machinery.SourceFileLoader('project', './dryck.py' )
        spec = importlib.util.spec_from_loader('project', loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        ctx = [cls for _, cls in inspect.getmembers(mod) if inspect.isclass(cls)][0]()

    the_walk = list(os.walk(SRC))

    # Preload _templates
    for root, dirs, files in the_walk:
        root = Path(root)

        for src in files:
            src = root / src
            if src.suffix == '.dryck' and src.name.startswith('_'):
                print(f'importing {src} into context')
                contextualize(src, ctx)

    for root, dirs, files in the_walk:
        root = Path(root)

        destdir = Path(DEST) / root.relative_to(SRC)
        print(f'creating {destdir}')
        makedirs(destdir)

        for src in files:
            src = root / src
            if src.name.startswith('_'): continue
            if src.suffix == '.dryck':
                dryck(src, ctx)
            else:
                copy(src)

    if hasattr(ctx, 'post'):
        ctx.post()

def makedirs(dir):
    os.makedirs(dir, exist_ok=True)

def copy(src):
    dest = Path(DEST) / src.relative_to(SRC)
    print(f'copying {src} to {dest}')
    shutil.copy(src, dest)

def dryck(src, ctx):
    dest = Path(DEST) / src.relative_to(SRC).with_suffix('')
    print(f'drycking {src} as {dest}')
    body = appeldryck.preprocess(ctx, src)
    with open(dest, 'w') as out:
        out.write(body)

def contextualize(src, ctx):
    name = src.stem.lstrip('_')
    setattr(ctx, name, make_template_runner(src).__get__(ctx))

def make_template_runner(src):
    def run_template(self):
        return appeldryck.render(self, src)
    return run_template
