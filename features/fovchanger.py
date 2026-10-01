from ext.datatypes import *

from functions import memfuncs
from functions import calculations
from functions import gameinput

import globals
import win32api, win32gui
import time

def FovChangerThreadFunction(Options, Offsets):

	processHandle = memfuncs.GetProcess("cs2.exe")
	clientBaseAddress = memfuncs.GetModuleBase(modulename="client.dll", process_object=processHandle)

	FovOptions = Options.copy()
	lastOptionsUpdate = time.perf_counter()
	originalFOV = None

	while True:
		if time.perf_counter() - lastOptionsUpdate > 0.25:
			FovOptions = Options.copy()
			lastOptionsUpdate = time.perf_counter()

		try:
			localPlayer = memfuncs.ProcMemHandler.ReadPointer(processHandle, clientBaseAddress + Offsets.offset.dwLocalPlayerPawn)
			localHealth = memfuncs.ProcMemHandler.ReadInt(processHandle, localPlayer + Offsets.offset.m_iHealth) if localPlayer else 0
			if not 0 < localHealth <= 100:
				originalFOV = None
				time.sleep(0.1)
				continue

			if not FovOptions["EnableFovChanger"] and originalFOV is None:
				time.sleep(0.05)
				continue

			cameraServices = memfuncs.ProcMemHandler.ReadPointer(processHandle, localPlayer + Offsets.offset.m_pCameraServices)
			if not cameraServices:
				continue

			currentFOV = memfuncs.ProcMemHandler.ReadInt(processHandle, cameraServices + Offsets.offset.m_iFOV)
			isScopedDown = memfuncs.ProcMemHandler.ReadBool(processHandle, localPlayer + Offsets.offset.m_bIsScoped)

			if isScopedDown:
				pass
			elif FovOptions["EnableFovChanger"]:
				desiredFov = FovOptions["FovChangeSize"]
				if currentFOV != desiredFov:
					if originalFOV is None:
						originalFOV = currentFOV
					memfuncs.ProcMemHandler.WriteInt(processHandle, cameraServices + Offsets.offset.m_iFOVStart, desiredFov)
					memfuncs.ProcMemHandler.WriteInt(processHandle, cameraServices + Offsets.offset.m_iFOV, desiredFov)
			elif originalFOV is not None:
				memfuncs.ProcMemHandler.WriteInt(processHandle, cameraServices + Offsets.offset.m_iFOVStart, originalFOV)
				memfuncs.ProcMemHandler.WriteInt(processHandle, cameraServices + Offsets.offset.m_iFOV, originalFOV)
				originalFOV = None

		except:
			time.sleep(0.1)