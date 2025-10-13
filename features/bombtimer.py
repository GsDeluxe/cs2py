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

                SharedBombState.bombPlanted = True
                total_time = 40
                for elapsed in range(total_time):
                    bombPlanted = memfuncs.ProcMemHandler.ReadBool(processHandle, gameRule + SharedOffsets.offset.m_bBombPlanted)
                    if not bombPlanted:
                        SharedBombState.bombPlanted = False
                        SharedBombState.bombTimeLeft = -1
                        break

                    SharedBombState.bombTimeLeft = total_time - elapsed
                    win32api.Sleep(1000)
                if SharedBombState.bombPlanted:
                    SharedBombState.bombPlanted = False
                    SharedBombState.bombTimeLeft = -1

        except Exception:
            try:
                SharedBombState.bombPlanted = False
                SharedBombState.bombTimeLeft = -1
            except:
                pass
            time.sleep(1)
            continue