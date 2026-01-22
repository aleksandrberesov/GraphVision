from dataclasses import dataclass

@dataclass
class PointPosition:
    x: int = 0
    y: int = 0

@dataclass
class Point:
    x: int = 0
    y: int = 0
    id: int = 0    
    label: str = ""
    rear: str = ""  
    ahead: list[str] = None  
    title: str = ""
