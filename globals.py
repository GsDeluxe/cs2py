import win32api
from ext import offsets
from ext.datatypes import *
import os

SCREEN_WIDTH = win32api.GetSystemMetrics(0)
SCREEN_HEIGHT = win32api.GetSystemMetrics(1)


GAME_OFFSETS = offsets.get_offsets()

SAVE_FILE = os.path.join(os.getcwd(), "settings.json")

CHEAT_SETTINGS = {
    "EnableAntiFlashbang": False,
    "EnableFovChanger": False,
    "FovChangeSize": 90,
	
    "EnableAimbot": True,
	"EnableAimbotPrediction": True,
    "EnableAimbotTeamCheck": False,
    "EnableAimbotVisibilityCheck": False,
    "AimbotFOV": 75,
    "AimbotSmoothing": 1,
    "AimPosition": "Head",
    "AimbotKey": 6,
	
    "EnableRecoilControl": False,
    "RecoilControlSmoothing": 1.0,

    "EnableTriggerbot": True,
    "EnableTriggerbotKeyCheck": True,
    "TriggerbotKey": 17,
    "EnableTriggerbotTeamCheck": False,

    "EnableESPDistanceRendering": True,
    "EnableESPTeamCheck": False,
    "EnableESPSkeletonRendering": True,
    "EnableESPBoxRendering": False,
    "EnableESPTracerRendering": False,
    "EnableESPNameText": False,
    "EnableESPHealthBarRendering": True,
    "EnableESPHealthText": False,
    "EnableESPDistanceText": False,
    "EnableFOVCircle": True,

    "EnableESPBombTimer": False,
    
    "CT_color": "#0000FF",
    "T_color": "#FF0000",
    "FOV_color": "#FFFFFF",

    "EnableBhop": False,

    "EnableDiscordRPC": True,
}


RCS_CTRL_BY_AIMBOT = False