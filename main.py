import globals
from functions import memfuncs, autoupdate

from features import aimbot
from features import combined

from features import rcs
from features import esp
from features import bombtimer
from features import fovchanger
from features import bhop
from features import discodrpc

from GUI import gui_mainloop
from GUI import gui_util

import multiprocessing
import threading

import serial
import serial.tools.list_ports

import win32con, win32process, win32api
import keyboard, os, json

keyboard.add_hotkey("end", callback=lambda: os._exit(0))
keyboard.add_hotkey("insert", callback=lambda: gui_util.hide_dpg())
keyboard.add_hotkey("home", callback=lambda: gui_util.streamproof_toggle())

class ManagedConfig:
	def __init__(self, managed_dict, save_function):
		self._dict = managed_dict
		self._save_function = save_function

	def update(self, *args, **kwargs):
		self._dict.update(*args, **kwargs)
		self._save_function(self._dict)

	def __setitem__(self, key, value):
		self._dict[key] = value
		self._save_function(self._dict)

	def __getitem__(self, key):
		return self._dict[key]

	def __delitem__(self, key):
		del self._dict[key]
		self._save_function(self._dict)

	def __contains__(self, key):
		return key in self._dict

	def get(self, key, default=None):
		return self._dict.get(key, default)

	def items(self):
		return self._dict.items()

	def keys(self):
		return self._dict.keys()

	def values(self):
		return self._dict.values()

	def __repr__(self):
		return repr(self._dict)
	
def SaveConfig(options):
	with open(globals.SAVE_FILE, 'w') as fp:
		json.dump(dict(options), fp, indent=4)

def LoadConfig():
	if not os.path.exists(globals.SAVE_FILE):
		with open(globals.SAVE_FILE, "w") as fp:
			json.dump(globals.CHEAT_SETTINGS, fp, indent=4)
	else:
		with open(globals.SAVE_FILE, "r") as fp:
			globals.CHEAT_SETTINGS = json.load(fp)

if __name__ == "__main__":

	print("          ____              \n  ___ ___|___ \\ _ __  _   _ \n / __/ __| __) | '_ \\| | | |\n| (__\\__ \\/ __/| |_) | |_| |\n \\___|___/_____| .__/ \\__, |\n               |_|    |___/ \n\n             - By GsDeluxe")
	
	autoupdate.check_and_update()

	win32process.SetPriorityClass(win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, win32api.GetCurrentProcessId()), win32process.HIGH_PRIORITY_CLASS)
	multiprocessing.freeze_support()

	COM_PORT = None
	use_arduino = input("Use Arduino? [Y/N]: ")
	if use_arduino.upper() == "Y":
		for index, port in enumerate([port.device for port in serial.tools.list_ports.comports()]):
			print(f"[{index}] {port}")
		COM_PORT = input("Select COM Port: ")

		ARDUINO_HANDLE = serial.Serial([port.device for port in serial.tools.list_ports.comports()][int(COM_PORT)], 9600)
	else:
		ARDUINO_HANDLE = None

	ProcessObject = memfuncs.GetProcess("cs2.exe")
	ClientModuleAddress = memfuncs.GetModuleBase(modulename="client.dll", process_object=ProcessObject)

	LoadConfig()

	Manager = multiprocessing.Manager()
	SharedOptions_M = Manager.dict(globals.CHEAT_SETTINGS)
	SharedOptions = ManagedConfig(SharedOptions_M, save_function=SaveConfig)

	SharedOffsets = Manager.Namespace()
	SharedOffsets.offset  = globals.GAME_OFFSETS

	GUI_proc = multiprocessing.Process(target=gui_mainloop.run_gui, args=(SharedOptions,))
	GUI_proc.start()

	esp.pme.overlay_init(title="ESP-Overlay")
	fps = esp.pme.get_monitor_refresh_rate()
	esp.pme.set_fps(fps)
	width, height = esp.pme.get_screen_width(), esp.pme.get_screen_height()

	FOV_proc = multiprocessing.Process(target=fovchanger.FovChangerThreadFunction, args=(SharedOptions, SharedOffsets,))
	FOV_proc.start()

	SharedBombState = Manager.Namespace()
	SharedBombState.bombPlanted = False
	SharedBombState.bombTimeLeft = -1
	Bomb_proc = multiprocessing.Process(target=bombtimer.BombTimerThread, args=(SharedBombState, SharedOffsets,))
	Bomb_proc.daemon = True
	Bomb_proc.start()

	discord_rpc_proc = multiprocessing.Process(target=discodrpc.DiscordRpcThread, args=(SharedOptions, ))
	discord_rpc_proc.daemon = True
	discord_rpc_proc.start()

	while esp.pme.overlay_loop():
		esp.ESP_Update(ProcessObject, ClientModuleAddress, SharedOptions, SharedOffsets, SharedBombState)

		if SharedOptions["EnableAimbot"] and win32api.GetAsyncKeyState(SharedOptions["AimbotKey"]) & 0x8000:
			aimbot.Aimbot_Update(ProcessObject, ClientModuleAddress, SharedOffsets, SharedOptions, ARDUINO_HANDLE=ARDUINO_HANDLE)

		if SharedOptions["EnableBhop"]:
			bhop.Bhop_Update(ProcessObject, ClientModuleAddress, SharedOffsets)

		combined.Triggerbot_AntiFlash_Update(ProcessObject, ClientModuleAddress, SharedOffsets, SharedOptions)
		rcs.RecoilControl_Update(ProcessObject, ClientModuleAddress, SharedOffsets, SharedOptions, ARDUINO_HANDLE=ARDUINO_HANDLE)
