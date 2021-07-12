from . import _evaluator as evaluator

class Context:
    def eval(self, markup, raw=False):
        return evaluator.eval_page(markup, self, raw=raw)


class HtmlContext(Context):
    @evaluator.raw
    def heading(self, level, text):
        return f'<h{level}>{text}</h{level}>'



