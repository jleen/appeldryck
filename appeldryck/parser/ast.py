from dataclasses import dataclass
from typing import List


@dataclass
class Def:
    key: str
    val: str

@dataclass
class Element:
    pass

@dataclass
class Eval(Element):
    expr: str

@dataclass
class Apply(Element):
    func: str
    args: List[str]

@dataclass
class Link(Element):
    dest: str
    label: str

@dataclass
class Text(Element):
    text: str

@dataclass
class Soft(Element):
    pass

@dataclass
class Break(Element):
    pass

@dataclass
class Star(Element):
    text: str

@dataclass
class Paragraph:
    text: List[Element]

@dataclass
class Document:
    metatext: List[Def]
    text: List[Paragraph]
