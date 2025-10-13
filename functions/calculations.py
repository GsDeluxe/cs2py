import math
from ext.datatypes import *
from globals import *

def distance_vec3(v: Vector3, other: Vector3):
	return float(math.fabs(float(v.x) - float(other.x)) + math.fabs(float(v.y) - float(other.y)) + math.fabs(float(v.z) - float(other.z)))

def distance_vec2(v: Vector2, other: Vector2) -> float:
	return float(math.fabs(float(v.x) - float(other.x)) + math.fabs(float(v.y) - float(other.y)))

def world_to_screen(view_matrix: Matrix, position: Vector3):
    mat = view_matrix.matrix

    x, y, z = position.x, position.y, position.z

    screen_x = mat[0][0] * x + mat[0][1] * y + mat[0][2] * z + mat[0][3]
    screen_y = mat[1][0] * x + mat[1][1] * y + mat[1][2] * z + mat[1][3]
    w = mat[3][0] * x + mat[3][1] * y + mat[3][2] * z + mat[3][3]

    if w < 0.01:
        return Vector2(-1.0, -1.0)

    invw = 1.0 / w
    
    screen_x *= invw
    screen_y *= invw
    
    width_float = float(SCREEN_WIDTH)
    height_float = float(SCREEN_HEIGHT)

    x = (width_float / 2.0) + (0.5 * screen_x * width_float) + 0.5
    y = (height_float / 2.0) - (0.5 * screen_y * height_float) + 0.5

    return Vector2(x, y)


def calculate_angles(from_: Vector3, to: Vector3) -> Vector2:
	yaw = 0.0
	pitch = 0.0

	deltaX = to.x - from_.x
	deltaY = to.y - from_.y
	deltaZ = to.z - from_.z

	yaw = math.atan2(deltaY, deltaX) * 180 / math.pi
	distance = math.sqrt(math.pow(deltaX,2) + math.pow(deltaY, 2))
	pitch = -(math.atan2(deltaZ, distance) * 180 / math.pi)

	return Vector2(yaw, pitch)