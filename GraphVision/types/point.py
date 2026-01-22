from dataclasses import dataclass

@dataclass
class PointPosition:
    x: int = 0
    y: int = 0

@dataclass
class Point:
    x: int = 0
    y: int = 0
    label: str = ""
    title: str = ""
    id: int = 0
    points: list[str] = None 