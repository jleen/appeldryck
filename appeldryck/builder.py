import importlib
import importlib.util
import inspect
import overlay
import shutil

from pathlib import Path

import appeldryck
from . import evaluator
from . import renderer


SRC = 'site'
DEST = 'dist'

def load_module_from_file(src):
    # This is a little arcane, but we’re just loading the supplied Python module.
    # TODO: What does the module name actually matter for?
    loader = importlib.machinery.SourceFileLoader('project', src)
    spec = importlib.util.spec_from_loader('project', loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod

def build():
    '''The command line entry point.'''

    # The project may have supplied its own context definition.
    # If not, use a default HTML context.
    if not Path('./dryck.py').exists:
        ctx = appeldryck.HtmlContext()
    else:
        # Instantiate the first class definition we find in the dryck module.
        # TODO: Handle the case where we have “loose” functions instead of a class.
        mod = load_module_from_file('./dryck.py')
        # TODO: Probably we can use a lazy sequence here?
        ctx = [cls for _, cls in inspect.getmembers(mod) if inspect.isclass(cls)][0]()

    process_dir(Path(SRC), ctx)

    if hasattr(ctx, 'post'):
        ctx.post()


def process_dir(path: Path, ctx):
    items = sorted(list(path.iterdir()))

    # If there’s a _dryck.py in the current dir,
    # load its definitions into the top of the context stack.
    # I suppose this could happen in the same pass that loads the .dryck files
    # since .dryck evaluation is lazy, but this seems cleaner.
    for item in items:
        if item.is_file():
            if item.name == '_dryck.py':
                mod = load_module_from_file(str(item))
                # TODO: Is there a cleaner way to do this?
                ctx.__dict__.update(mod.__dict__)

    # Any .dryck file starting with _ is a function definition rather than a target.
    # Read them all into the top of the context stack.
    for item in items:
        if item.suffix == '.dryck' and item.name.startswith('_'):
            print(f'importing {item} into context')
            # If there are multiple extensions, e.g. .html.dryck, then this is a dryck template.
            # Otherwise it’s dryck markup.
            raw = len(item.suffixes) > 1
            add_file_to_context(item, ctx, raw)

    # Create the target directory for this source directory.
    destdir = Path(DEST) / path.relative_to(SRC)
    print(f'creating {destdir}')
    makedirs(destdir)

    # Render all the dryck files and copy all the static files in this directory.
    for item in items:
        if not item.is_file(): continue
        if item.name.startswith('_'): continue
        if item.suffix == '.dryck':
            try:
                if len(item.suffixes) == 1:
                    process(item, ctx)
                else:
                    preprocess(item, ctx)
            except Exception as e:
                e.add_note(f'while rendering {item} from the project tree')
                raise
        else:
            copy(item)

    # Recurse into any subdirectories.
    for item in items:
        if item.is_dir():
            # Loading _dryck files can produce __pycache__ in the project tree. Skip it!
            # TODO: Can we avoid producing them in the first place?
            if item.name == '__pycache__':
                continue
            else:
                class Subcontext: pass
                try:
                    process_dir(item, overlay.overlay(Subcontext, ctx))
                except Exception as e:
                    e.add_note(f'while rendering project directory {item}')
                    raise


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

def add_file_to_context(src, ctx, raw):
    name = src.stem.lstrip('_')
    setattr(ctx, name, curry_file_as_function(src, raw).__get__(ctx))

def curry_file_as_function(src, raw):
    @appeldryck.indented
    def run_template(self):
        if raw:
            return appeldryck.preprocess(self, src)
        else:
            return appeldryck.render(self, src)
    return run_template
