from ext.datatypes import *

from functions import memfuncs
from functions import calculations
from functions import gameinput

import globals
import win32api, win32gui

def Triggerbot_AntiFlash_Update(processHandle, clientBaseAddress, Offsets, Options):
	localPlayer = memfuncs.ProcMemHandler.ReadPointer(processHandle, clientBaseAddress + Offsets.offset.dwLocalPlayerPawn)
	if (not localPlayer): return

	try:
		if Options["EnableAntiFlashbang"]:
			memfuncs.ProcMemHandler.WriteFloat(processHandle, localPlayer + Offsets.offset.m_flFlashMaxAlpha, 255.0)
			return
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