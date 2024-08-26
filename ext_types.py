from dataclasses import dataclass
import math
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

	pawnAddress: int
	controllerAddress: int
	origin: Vector3
	view: Vector3
	lifestate: int
	distance: float
	head2d: Vector2
	pixelDistance: float


@dataclass
class Offset:
	dwViewMatrix: int
	dwLocalPlayerPawn: int
	dwEntityList: int
	dwLocalPlayerController: int
	dwViewAngles: int
	dwGameRules: int

	ButtonJump: int
	
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
	m_flFlashMaxAlpha: int
	m_fFlags: int
	m_iFOV: int
	m_pCameraServices: int
	m_bIsScoped: int

	m_vecViewOffset: int
	m_entitySpottedState: int 
	m_bSpotted: int 
	m_bBombPlanted: int

@dataclass
class Matrix:
	matrix: List[List[float]]

def distance_vec3(v: Vector3, other: Vector3):
	return float(math.fabs(float(v.x) - float(other.x)) + math.fabs(float(v.y) - float(other.y)) + math.fabs(float(v.z) - float(other.z)))

def distance_vec2(v: Vector2, other: Vector2) -> float:
	return float(math.fabs(float(v.x) - float(other.x)) + math.fabs(float(v.y) - float(other.y)))