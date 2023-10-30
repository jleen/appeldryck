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
    text: List[Element]

@dataclass
class Block:
    pass

@dataclass
class Raw(Block):
    text: List[Element]

@dataclass
class Paragraph(Block):
    text: List[Element]

@dataclass
class Item:
    text: List[Element]

@dataclass
class Itemized(Block):
    items: List[Item]
    ordered: bool

@dataclass
class Document:
    metatext: List[Def]
    text: List[Block]
