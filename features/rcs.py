from ext.datatypes import *
from functions import memfuncs, gameinput, calculations
import globals
import win32api, win32gui, time
import math

oldPunch_x = 0.0
oldPunch_y = 0.0

def RecoilControl_Update(processHandle, clientBaseAddress, Offsets, Options, ARDUINO_HANDLE):
	global oldPunch_x, oldPunch_y

	try:
		if win32gui.GetWindowText(win32gui.GetForegroundWindow()) != "Counter-Strike 2":
			return
		
		if not Options["EnableRecoilControl"]:
			return

		localPlayer = memfuncs.ProcMemHandler.ReadPointer(processHandle, clientBaseAddress + Offsets.offset.dwLocalPlayerPawn)
		if not localPlayer:
			return

		shotsFired = memfuncs.ProcMemHandler.ReadInt(processHandle, localPlayer + Offsets.offset.m_iShotsFired)
		aimPunch_x = memfuncs.ProcMemHandler.ReadFloat(processHandle, localPlayer + Offsets.offset.m_aimPunchAngle)
		aimPunch_y = memfuncs.ProcMemHandler.ReadFloat(processHandle, localPlayer + Offsets.offset.m_aimPunchAngle + 0x4)

		sensitivityBase = memfuncs.ProcMemHandler.ReadPointer(processHandle, clientBaseAddress + Offsets.offset.dwSensitivity)
		sensitivity = memfuncs.ProcMemHandler.ReadFloat(processHandle, sensitivityBase + Offsets.offset.dwSensitivity_sensitivity)

		if 1 < shotsFired < 999999 and not globals.RCS_CTRL_BY_AIMBOT:
			deltaX = (aimPunch_x - oldPunch_x) * -1.0
			deltaY = (aimPunch_y - oldPunch_y) * -1.0

			moveX = (deltaY * 2.0 / sensitivity) / -0.022
			moveY = (deltaX * 2.0 / sensitivity) / 0.022

			currentMouse = gameinput.getCurrentMousePosition()
			targetMouse = Vector2(currentMouse.x + moveX, currentMouse.y + moveY)

			smoothFactor = max(1.0, min(float(Options["RecoilControlSmoothing"]), 3.0))
			delta = Vector2(targetMouse.x - currentMouse.x, targetMouse.y - currentMouse.y)

			smoothedMove = Vector2(delta.x / smoothFactor, delta.y / smoothFactor)
			nextMouse = Vector2(currentMouse.x + smoothedMove.x, currentMouse.y + smoothedMove.y)

			if ARDUINO_HANDLE is not None:
				gameinput.moveMouseToLocationArdunio(nextMouse, handle=ARDUINO_HANDLE)
			else:
				gameinput.moveMouseToLocation(nextMouse)

			oldPunch_x = aimPunch_x
			oldPunch_y = aimPunch_y
		else:
			oldPunch_x = 0.0
			oldPunch_y = 0.0

	except Exception as e:
		print(f"RCS error: {e}")
