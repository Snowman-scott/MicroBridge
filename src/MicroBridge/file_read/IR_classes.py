from datetime import datetime
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int

@dataclass
class Annot:
    id: str
    cords: list[Point]

@dataclass
class Metadata:
    creationDate: datetime

@dataclass
class AnnotFile:
    anos: list[Annot]
    md: Metadata
