import ctypes
import time
import random
import serial

from ext.datatypes import *
from functions import calculations
from globals import *

def LeftClick():
    time.sleep(random.randint(10, 30) / 1000.0)
    ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0) # MOUSEEVENTF_LEFTDOWN 
    time.sleep(random.randint(10, 50) / 1000.0)
    ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0) # MOUSEEVENTF_LEFTUP 

def LeftClickArduino(handle):
    time.sleep(random.randint(10, 30) / 1000.0)
    handle.write(f"down\n".encode())
    time.sleep(random.randint(10, 50) / 1000.0)
    handle.write(f"up\n".encode())

def moveMouseToLocation(pos: Vector2):
    if pos.x < 0.0 and pos.y < 0.0:
        return

    center_of_screen = Vector2(SCREEN_WIDTH / 2.0, SCREEN_HEIGHT / 2.0)
    dx = int(pos.x - center_of_screen.x)
    dy = int(pos.y - center_of_screen.y)

    ctypes.windll.user32.mouse_event(0x0001, dx, dy, 0, 0)  # MOUSEEVENTF_MOVE

def getCurrentMousePosition():
    pos = win32api.GetCursorPos()
    if pos:
        return Vector2(pos[0], pos[1])
    return Vector2(0,0)

def moveMouseToLocationArdunio(pos: Vector2, handle=None):
    if pos.x < 0.0 and pos.y < 0.0:
        return

    center_of_screen = Vector2(SCREEN_WIDTH / 2.0, SCREEN_HEIGHT / 2.0)

    dx = int(pos.x - center_of_screen.x)
    dy = int(pos.y - center_of_screen.y)

    handle.write(f"move {dx},{dy}\n".encode())