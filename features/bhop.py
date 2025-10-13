
from ext.datatypes import *
from functions import memfuncs
import globals
import win32api
import time


def Bhop_Update(processHandle, clientBaseAddress, Offsets):
    try:
        localPlayer = memfuncs.ProcMemHandler.ReadPointer(processHandle, clientBaseAddress + Offsets.offset.dwLocalPlayerController)
        if not localPlayer:
            return

        localPawn = memfuncs.ProcMemHandler.ReadInt(processHandle, localPlayer + Offsets.offset.m_hPlayerPawn)
        if not localPawn:
            return

        entityList = memfuncs.ProcMemHandler.ReadPointer(processHandle, clientBaseAddress + Offsets.offset.dwEntityList)
        listEntry = memfuncs.ProcMemHandler.ReadPointer(processHandle, entityList + (0x8 * ((localPawn & 0x7FFF) >> 9) + 0x10))
        localPawn = memfuncs.ProcMemHandler.ReadPointer(processHandle, listEntry + (120 * (localPawn & 0x1FF)))
        
        if localPawn:
            flags = memfuncs.ProcMemHandler.ReadInt(processHandle, localPawn + Offsets.offset.m_fFlags)
            if win32api.GetAsyncKeyState(0x20) and flags & (1 << 0):
                memfuncs.ProcMemHandler.WriteInt(processHandle, clientBaseAddress + Offsets.offset.ButtonJump, 65537)
                time.sleep(0.01)
                memfuncs.ProcMemHandler.WriteInt(processHandle, clientBaseAddress + Offsets.offset.ButtonJump, 256)
    except Exception as e:
        print(e)