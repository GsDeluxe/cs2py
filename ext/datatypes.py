from dataclasses import dataclass
from typing import Optional
from typing import List

@dataclass
class Vector3:
	x: float
	y: float
	z: float
	def __add__(self, other: 'Vector3') -> 'Vector3':return Vector3(x=self.x + other.x,y=self.y + other.y,z=self.z + other.z)
	def __sub__(self, other: 'Vector3') -> 'Vector3': return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
	def __mul__(self, scalar: float) -> 'Vector3': return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

@dataclass
class Vector2:
	x: float
	y: float
	def __add__(self, other: 'Vector2') -> 'Vector2': return Vector2(x=self.x + other.x,y=self.y + other.y)
	def __sub__(self, other: 'Vector2') -> 'Vector2': return Vector2(x=self.x - other.x, y=self.y - other.y)
	def __mul__(self, scalar: float) -> 'Vector2': return Vector2(x=self.x * scalar, y=self.y * scalar)

@dataclass
class Rectangle:
	Top: float
	Left: float
	Right: float
	Bottom: float


PLAYER_BONES = {
    "pelvis": 1,
    "spine_2": 2,
    "spine_1": 4,
    "neck_0": 6,
    "head": 7,
    "arm_upper_L": 9,
    "arm_lower_L": 10,
    "hand_L": 11,
    "arm_upper_R": 13,
    "arm_lower_R": 14,
    "hand_R": 15,
    "leg_upper_L": 17,
    "leg_lower_L": 18,
    "ankle_L": 19,
    "leg_upper_R": 20,
    "leg_lower_R": 21,
    "ankle_R": 22,
}

@dataclass
class Entity:
    Health: int = 100
    Team: int = 0
    Name: str = ""
    Position: Optional[Vector2] = None
    Bones: dict[str, Vector2] = None
    HeadPos: Optional[Vector3] = None
    Distance: float = 0.0
    Rect: Optional[Rectangle] = None
    OnScreen: bool = False

    pawnAddress: Optional[int] = None
    controllerAddress: Optional[int] = None
    origin: Optional[Vector3] = None
    view: Optional[Vector3] = None
    lifestate: int = 0
    head2d: Optional[Vector2] = None
    pixelDistance: float = 0.0


@dataclass
class Matrix:
	matrix: List[List[float]]