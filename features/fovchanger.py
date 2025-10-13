from ext.datatypes import *

from functions import memfuncs
from functions import calculations
from functions import gameinput

import globals
import win32api, win32gui

def FovChangerThreadFunction(Options, Offsets):

	processHandle = memfuncs.GetProcess("cs2.exe")
	clientBaseAddress = memfuncs.GetModuleBase(modulename="client.dll", process_object=processHandle)

	while True:
		

		localPlayer = memfuncs.ProcMemHandler.ReadPointer(processHandle, clientBaseAddress + Offsets.offset.dwLocalPlayerPawn)
		if (not localPlayer): continue

		try:
			cameraServices = memfuncs.ProcMemHandler.ReadPointer(processHandle, localPlayer + Offsets.offset.m_pCameraServices)
			currentFOV = memfuncs.ProcMemHandler.ReadInt(processHandle, cameraServices + Offsets.offset.m_iFOV)
			isScopedDown = memfuncs.ProcMemHandler.ReadBool(processHandle, localPlayer + Offsets.offset.m_bIsScoped)

			if ( not isScopedDown or currentFOV != Options["FovChangeSize"] or Options["EnableFovChanger"]):
			
				memfuncs.ProcMemHandler.WriteInt(processHandle, cameraServices + Offsets.offset.m_iFOV, Options["FovChangeSize"])
			else:
				pass
				memfuncs.ProcMemHandler.WriteInt(processHandle, cameraServices + Offsets.offset.m_iFOV, 90)

			if Options["EnableAntiFlashbang"]:
				memfuncs.ProcMemHandler.WriteFloat(processHandle, localPlayer + Offsets.offset.m_flFlashMaxAlpha, 255.0)
				continue
			else:
				memfuncs.ProcMemHandler.WriteFloat(processHandle, localPlayer + Offsets.offset.m_flFlashMaxAlpha, 0.0)

			if (win32gui.GetWindowText(win32gui.GetForegroundWindow()) == "Counter-Strike 2" and Options["EnableTriggerbot"] and (win32api.GetAsyncKeyState(Options["TriggerbotKey"]) or not Options["EnableTriggerbotKeyCheck"])):
				localPlayerID = memfuncs.ProcMemHandler.ReadInt(processHandle, localPlayer + Offsets.offset.m_iIDEntIndex)
				if (localPlayerID > 0):
					entityList = memfuncs.ProcMemHandler.ReadPointer(processHandle, clientBaseAddress + Offsets.offset.dwEntityList)
					entityListEntry = memfuncs.ProcMemHandler.ReadPointer(processHandle, entityList + 0x8 * (localPlayerID >> 9) + 0x10)
					TargetEntity = memfuncs.ProcMemHandler.ReadPointer(processHandle, entityListEntry + 120 * (localPlayerID & 0x1FF))

					TargetEntityTeam = memfuncs.ProcMemHandler.ReadInt(processHandle, TargetEntity + Offsets.offset.m_iTeamNum)
					localPlayerTeam = memfuncs.ProcMemHandler.ReadInt(processHandle, localPlayer + Offsets.offset.m_iTeamNum)

					if not Options["EnableTriggerbotTeamCheck"] or TargetEntityTeam != localPlayerTeam:
						TargetEntityHP = memfuncs.ProcMemHandler.ReadInt(processHandle, TargetEntity + Offsets.offset.m_iHealth)
						if (TargetEntityHP > 0):
							if not win32api.GetAsyncKeyState(0x01):
								gameinput.LeftClick()

		except:
			pass