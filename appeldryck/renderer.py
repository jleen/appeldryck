import os
from pathlib import Path
import sys

from . import context
from . import evaluator


def _render_file(env, filename, raw):
    if not isinstance(filename, Path):
        filename = Path(filename)
    raw_text = filename.read_text()
    return _render_string(env, raw_text, raw, filename)


def _render_string(env, raw_text, raw, filename):
    try:
        if hasattr(env, 'replace'):
            for (old, new) in env.replace.items():
                raw_text = raw_text.replace(old, new)

        # Evaluate the page markup and put it in the context.
        env.body = evaluator.eval_page(raw_text, env, raw, name=filename)
        return env.body
    except evaluator.SuppressPageGenerationException:
        # The page can cancel its own production.
        return None


def markup(env, filename):
    '''Run the given file in page mode.'''
    try:
        return _render_file(env, filename, False)
    except evaluator.DryckException as e:
        # Suppress callstack for parser internals.
        raise evaluator.DryckException(e) from e.__cause__


def preprocess(env, filename):
    '''Run the given file in preprocessor mode.'''
    # If we were passed a dict, it's safe to assume we wanted a generic
    # Context object, since we're in preprocessor mode.
    if type(env) is dict:
        ctx = context.Context()
        ctx.__dict__ |= env
        env = ctx
    try:
        return _render_file(env, filename, True)
    except evaluator.DryckException as e:
        # Suppress callstack for parser internals.
        raise evaluator.DryckException(e) from e.__cause__


def render(env, page_filename, template_filename=[], out_filename=None):
    '''Easy mode: Run the given file in page mode, injecting the result into each of the
    supplied templates, turduckenwise. Snarf up the global namespace into the context,
    and allow specifying an output filename for convenience.'''
    try:
        # Add the global dict to the context, to keep simple projects simple.
        env.__dict__.update(sys.modules['__main__'].__dict__)

        if page_filename:
            # Add the page filename to the context.
            env.filename = os.path.splitext(page_filename)[0]

            if markup(env, page_filename) == None:
                return

        if not isinstance(template_filename, list):
            template_filename = [template_filename]

        for f in template_filename:
            preprocess(env, f)

        if out_filename:
            Path(out_filename).write_text(env.body)

        return env.body
    except evaluator.DryckException as e:
        # Suppress callstack for parser internals.
        raise evaluator.DryckException(e) from e.__cause__
