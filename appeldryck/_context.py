import html

from . import _evaluator as evaluator


class Context:
    def eval(self, markup, raw=False):
        return evaluator.eval_page(markup, self, raw=raw)


def tag(name, body, block=False):
    brk = '\n' if block else ''
    return f'<{name}>{brk}{body}</{name}>\n'


class HtmlContext(Context):
    '''Base Appeldryck context for HTML output.

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
        return tag('em', body)

    def strong(self, body):
        return tag('strong', body)

    def href(self, target, body, title):
        title_attr = f' title="{escape(self.title)}"' if title else ''
        escaped_target = html.escape(quote(html.unescape(target),
                                           safe='/#:()*?=%@+,&'))
        return f'<a href="{escaped_target}"{title_attr}>{body}</a>'

    def br(self):
        return '<br />\n'

    def escape(self, text):
        return html.escape(html.unescape(text)).replace("&#x27;", "'")
