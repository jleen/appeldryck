import html
import os

from . import evaluator


class Context:
    def eval(self, markup, raw=False, tight=False):
        return evaluator.eval_page(markup, self, raw=raw, tight=tight)

    def suppress(self):
        raise evaluator.SuppressPageGenerationException()


def tag(name, body, block=False, inline=False):
    brk = '\n' if block else ''
    line = '\n' if not inline else ''
    return f'<{name}>{brk}{body}</{name}>{line}'


class HtmlContext(Context):
    '''Base dryck context for HTML output.

    Defines rendering for basic markdown tags that any dryck will need.

    This is about half the logic from marko.HTMLRenderer.
    The rest is in HtmlContext.
    '''

    def heading(self, level, body):
        return tag(f'h{level}', body)

    def p(self, body):
        return tag('p', body)

    def ol(self, body, start=None):
        start_attr = start if start != None else ''
        return f'<ol{start_attr}>\n{body}</ol>\n'

    def ul(self, body):
        return tag('ul', body)

    def li(self, body):
        return tag('li', body)

    def blockquote(self, body):
        return tag('blockquote', body, block=True)

    def hr(self):
        return '<hr />\n'

    def em(self, body):
        return tag('em', body, inline=True)

    def strong(self, body):
        return tag('strong', body, inline=True)

    def href(self, target, body, title):
        title_attr = f' title="{self.escape(self.title)}"' if title else ''
        escaped_target = html.escape(self.quote(html.unescape(target),
                                           safe='/#:()*?=%@+,&'))
        return f'<a href="{escaped_target}"{title_attr}>{body}</a>'

    def br(self):
        return '<br />\n'

    def escape(self, text):
        return html.escape(html.unescape(text)).replace("&#x27;", "'")


class LaTeXContext(Context):
    '''Base dryck context for LaTeX output.'''

    # The convention is that each emitted block element should assume
    # that it has been given a fresh line to begin on, and it should
    # provide such for its following block element.

    def heading(self, level, body):
        return '\\section{' + body + '}\n\n'

    def p(self, body):
        return f'{body}\n\n'

    def ol(self, body, start=None):
        # TODO: start_attr = start if start != None else ''
        return '\\begin{enumerate}\n' + body + '\\end{enumerate}\n\n'

    def ul(self, body):
        return '\\begin{itemize}\n' + body + '\\end{itemize}\n\n'

    def li(self, body):
        return f'\\item {body}\n'

    def blockquote(self, body):
        return '\\begin{blockquote}\n' + body + '\\end{blockquote}\n\n'

    def hr(self):
        raise Exception('hr not implemented')

    def em(self, body):
        return '{\\it ' + body + '}'

    def strong(self, body):
        return '{\\bf ' + body + '}'

    def href(self, target, body, title):
        raise Exception('href not implemented')

    def br(self):
        # Emit a \\ at the end of the line, to perform a hard TeX linebreak.
        return '\\\\\n'

    def escape(self, text):
        text = text.replace('#', r'\#')
        text = text.replace('&', r'\&')
        text = text.replace('_', r'\_')
        text = text.replace('^', r'\^')
        text = text.replace('%', r'\%')
        text = text.replace('$', '\\$')
        text = text.replace('~', r'\char`\~')
        return text


def templates(sources):
    '''A decorator to specify that a context exposes the named template files
    as functions.'''
    def decorator(clazz):
        for source in sources:
            def create_run_template(source):
                def run_template(self):
                    return evaluator.render(self, source)
                return run_template
            name = os.path.basename(source).split('.')[0]
            setattr(clazz, name, create_run_template(source))
        return clazz
    return decorator
