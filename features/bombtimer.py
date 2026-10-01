from ext.datatypes import *
from functions import memfuncs
import globals
import win32api
import time

def BombTimerThread(SharedBombState, SharedOffsets):
    while True:
        try:
            processHandle = memfuncs.GetProcess("cs2.exe")
            if not processHandle:
                SharedBombState.bombPlanted = False
                SharedBombState.bombTimeLeft = -1
                time.sleep(1)
                continue

            clientBaseAddress = memfuncs.GetModuleBase(modulename="client.dll", process_object=processHandle)
            if not clientBaseAddress:
                SharedBombState.bombPlanted = False
                SharedBombState.bombTimeLeft = -1
                time.sleep(1)
                continue

            while True:
                gameRule = memfuncs.ProcMemHandler.ReadPointer(processHandle, clientBaseAddress + SharedOffsets.offset.dwGameRules)
                if not gameRule:
                    SharedBombState.bombPlanted = False
                    SharedBombState.bombTimeLeft = -1
                    time.sleep(0.05)
                    continue

                bombPlanted = memfuncs.ProcMemHandler.ReadBool(processHandle, gameRule + SharedOffsets.offset.m_bBombPlanted)
                if not bombPlanted:
                    SharedBombState.bombPlanted = False
                    SharedBombState.bombTimeLeft = -1
                    time.sleep(0.05)
                    continue

                plantedC4 = memfuncs.ProcMemHandler.ReadPointer(processHandle, clientBaseAddress + SharedOffsets.offset.dwPlantedC4)
                globalVars = memfuncs.ProcMemHandler.ReadPointer(processHandle, clientBaseAddress + SharedOffsets.offset.dwGlobalVars)
                bombTimeLeft = memfuncs.ProcMemHandler.ReadFloat(processHandle, plantedC4 + SharedOffsets.offset.m_flC4Blow) - memfuncs.ProcMemHandler.ReadFloat(processHandle, globalVars + 0x30)
                bombDefused = memfuncs.ProcMemHandler.ReadBool(processHandle, plantedC4 + SharedOffsets.offset.m_bBombDefused)

                SharedBombState.bombPlanted = not bombDefused and 0 < bombTimeLeft < 60
                SharedBombState.bombTimeLeft = bombTimeLeft if SharedBombState.bombPlanted else -1
                time.sleep(0.05)

        except Exception:
            try:
                SharedBombState.bombPlanted = False
                SharedBombState.bombTimeLeft = -1
            except:
                pass
            time.sleep(1)
            continue