from dataclasses import dataclass

@dataclass
class Point:
    x: int = 0
    y: int = 0
    label: str = ""
    id: int = 0
    points: list[str] = None 