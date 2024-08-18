from dataclasses import dataclass
import math
from typing import List

@dataclass
class Vector3:
    x: float
    y: float
    z: float

@dataclass
class Vector2:
    x: float
    y: float

@dataclass
class Rectangle:
    Top: float
    Left: float
    Right: float
    Bottom: float
    
@dataclass
class Rectangle:
    Top: float
    Left: float
    Right: float
    Bottom: float

@dataclass
class Entity:
    Health: int
    Team: int
    Name: str
    Position: Vector2
    Bones: dict[str, Vector2]
    HeadPos: Vector3
    Distance: float
    Rect: Rectangle
    OnScreen: bool

@dataclass
class Offset:
    dwViewMatrix: int
    dwLocalPlayerPawn: int
    dwEntityList: int
    m_hPlayerPawn: int
    m_iHealth: int
    m_lifeState: int
    m_iTeamNum: int
    m_vOldOrigin: int
    m_pGameSceneNode: int
    m_modelState: int
    m_boneArray: int
    m_nodeToWorld: int
    m_sSanitizedPlayerName: int
    m_iIDEntIndex: int

@dataclass
class Matrix:
    matrix: List[List[float]]

def distance_vec3(v: Vector3, other: Vector3):
    return float(math.fabs(float(v.x) - float(other.x)) + math.fabs(float(v.y) - float(other.y)) + math.fabs(float(v.z) - float(other.z)))
