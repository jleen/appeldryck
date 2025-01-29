import importlib
import importlib.util
import inspect
import shutil

from pathlib import Path

import appeldryck
from . import evaluator
from . import renderer


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

    the_walk = list(Path(SRC).walk())

    # Preload _templates
    for root, _, files in the_walk:
        for src in files:
            src = root / src
            if src.suffix == '.dryck' and src.name.startswith('_'):
                print(f'importing {src} into context')
                # If there are multiple extensions, e.g. .html.dryck, then this is a template.
                raw = len(src.suffixes) > 1
                contextualize(src, ctx, raw)

    for root, _, files in the_walk:
        destdir = Path(DEST) / root.relative_to(SRC)
        print(f'creating {destdir}')
        makedirs(destdir)

        for src in files:
            src = root / src
            if src.name.startswith('_'): continue
            if src.suffix == '.dryck':
                if len(src.suffixes) == 1:
                    process(src, ctx)
                else:
                    preprocess(src, ctx)
            else:
                copy(src)

    if hasattr(ctx, 'post'):
        ctx.post()

def makedirs(dir):
    Path(dir).mkdir(exist_ok=True)

def copy(src):
    dest = Path(DEST) / src.relative_to(SRC)
    print(f'copying {src} to {dest}')
    shutil.copy(src, dest)

def process(src, ctx):
    # We need to process the markup first, in order to get the template name.
    ctx.body = indented_string(renderer.markup(ctx, src))
    dest = Path(DEST) / src.relative_to(SRC).with_suffix(Path(ctx.template).suffix)
    # TODO: Approximately nothing about the next line is good.
    # HAHAHA ctx.template needs to be looked up as a function
    template_fn = getattr(ctx, ctx.template)
    body = evaluator.apply_func(template_fn, [], ctx, raw=True, indent=0)
    print(f'drycking {src} as {dest}')
    with open(dest, 'w') as out:
        out.write(body)

def indented_string(text):
    '''Wrap a string in a function that is annotated as indented.'''
    @appeldryck.indented
    def indented_wrapper():
        return text
    return indented_wrapper

def preprocess(src, ctx):
    dest = Path(DEST) / src.relative_to(SRC).with_suffix('')
    print(f'drycking {src} as {dest}')
    body = appeldryck.preprocess(ctx, src)
    with open(dest, 'w') as out:
        out.write(body)

def contextualize(src, ctx, raw):
    name = src.stem.lstrip('_')
    setattr(ctx, name, make_template_runner(src, raw).__get__(ctx))

def make_template_runner(src, raw):
    @appeldryck.indented
    def run_template(self):
        if raw:
            return appeldryck.preprocess(self, src)
        else:
            return appeldryck.render(self, src)
    return run_template
