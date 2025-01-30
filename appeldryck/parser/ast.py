from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Node:
    linespan: Tuple[int, int]
    lexspan: Tuple[int, int]

@dataclass
class Def(Node):
    key: str
    val: str

@dataclass
class Element(Node):
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
class Block(Node):
    pass

@dataclass
class Heading(Block):
    text: List[Element]
    level: int

@dataclass
class Raw(Block):
    text: List[Element]

@dataclass
class Paragraph(Block):
    text: List[Element]

@dataclass
class Item(Node):
    text: List[Element]

@dataclass
class Itemized(Block):
    items: List[Item]
    ordered: bool

@dataclass
class Document(Node):
    metatext: List[Def]
    text: List[Block]
