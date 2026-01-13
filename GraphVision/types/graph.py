from dataclasses import dataclass

from .point import Point

@dataclass
class Graph:
    points: list[Point] = None