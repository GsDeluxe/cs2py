import ctypes
import win32api, win32gui, win32con

user32 = ctypes.WinDLL('user32', use_last_error=True)
SetWindowDisplayAffinity = user32.SetWindowDisplayAffinity
SetWindowDisplayAffinity.argtypes = ctypes.wintypes.HWND, ctypes.wintypes.DWORD
SetWindowDisplayAffinity.restype = ctypes.wintypes.BOOL
WDA_EXCLUDEFROMCAPTURE = 0x00000011
WDA_NONE = 0x00000000

HIDDEN = False
STREAMPROOF = False

def hide_dpg():
	global HIDDEN
	global STREAMPROOF
	hwnd = win32gui.FindWindow(None, "cs2py")
	if HIDDEN:
		win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
		if STREAMPROOF:
			SetWindowDisplayAffinity(hwnd, WDA_NONE)
			SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
		HIDDEN = False
	elif not HIDDEN:
		win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
		HIDDEN = True

def streamproof_toggle():
	global STREAMPROOF
	hwnd1 = win32gui.FindWindow(None, "cs2py")
	hwnd2 = win32gui.FindWindow(None, "ESP-Overlay")
	if STREAMPROOF:
		print("STREAMPROOF OFF")
		SetWindowDisplayAffinity(hwnd1, WDA_NONE)
		SetWindowDisplayAffinity(hwnd2, WDA_NONE)
		STREAMPROOF = False
	elif not STREAMPROOF:
		print("STREAMPROOF ON")
		SetWindowDisplayAffinity(hwnd1, WDA_EXCLUDEFROMCAPTURE)
		SetWindowDisplayAffinity(hwnd2, WDA_EXCLUDEFROMCAPTURE)
		STREAMPROOF = True