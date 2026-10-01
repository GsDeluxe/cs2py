from ext.datatypes import *
from functions import memfuncs
from functions import calculations
from functions import gameinput
import globals
import win32api, win32gui
import pyMeow as pme
import time
import struct
import concurrent.futures
import os
import math

boneConnections = [
	('head', 'neck_0'), ('neck_0', 'spine_1'), ('spine_1', 'spine_2'), ('spine_2', 'pelvis'),
	('pelvis', 'leg_upper_L'), ('leg_upper_L', 'leg_lower_L'), ('leg_lower_L', 'ankle_L'),
	('pelvis', 'leg_upper_R'), ('leg_upper_R', 'leg_lower_R'), ('leg_lower_R', 'ankle_R'),
	('spine_2', 'arm_upper_L'), ('arm_upper_L', 'arm_lower_L'), ('arm_lower_L', 'hand_L'),
	('spine_2', 'arm_upper_R'), ('arm_upper_R', 'arm_lower_R'), ('arm_lower_R', 'hand_R')
]

BONE_READ_SIZE = (max(PLAYER_BONES.values()) + 1) * 32

GRENADE_TIMERS = {
	"smokegrenade_projectile": ("Smoke", 21.0, "#C8C8C8"),
}

WEAPON_ICONS = {
	1: "A", 2: "B", 3: "C", 4: "D", 32: "E", 36: "F", 61: "G", 30: "H", 63: "I", 64: "J",
	17: "K", 24: "L", 26: "M", 33: "N", 34: "O", 19: "P", 13: "Q", 10: "R", 16: "S", 60: "T",
	8: "U", 39: "V", 7: "W", 11: "X", 38: "Y", 9: "Z",
	59: "[", 42: "]",
	512: "0", 500: "2", 505: "2", 506: "3", 507: "4", 508: "5", 509: "6", 514: "7", 515: "8", 516: "9",
	40: "a", 25: "b", 29: "c", 27: "d", 35: "e", 28: "f", 14: "g", 31: "h",
	43: "i", 44: "j", 45: "k", 46: "l", 47: "m", 48: "n",
	49: "o", 50: "p", 55: "r",
	23: "x",
}

designerNames = {}
grenadeEntities = []
lastGrenadeScan = 0.0
lastLocalController = 0
loadedFonts = set()
FONT_ID = 0
WEAPON_FONT_ID = 1
TEXT_SHADOW = pme.fade_color(pme.get_color("#000000"), 0.8)

def load_font(pme, font_path, font_id=FONT_ID):
	if os.path.exists(font_path):
		pme.load_font(font_path, font_id)
		loadedFonts.add(font_id)

def draw_text(pme, text, x, y, font_size, color, font_id=FONT_ID):
	x, y = round(x), round(y)
	if font_id in loadedFonts:
		pme.draw_font(font_id, text, x + 1, y + 1, font_size, 1, TEXT_SHADOW)
		pme.draw_font(font_id, text, x, y, font_size, 1, color)
	else:
		pme.draw_text(text, x + 1, y + 1, fontSize=font_size, color=TEXT_SHADOW)
		pme.draw_text(text, x, y, fontSize=font_size, color=color)

def measure_text(pme, text, font_size, font_id=FONT_ID):
	return pme.measure_font(font_id, text, font_size, 1)["x"] if font_id in loadedFonts else pme.measure_text(text, int(font_size))

def get_health_color(health):
	health_percentage = max(0.0, min(1.0, health / 100.0))
	return f"#{int(255 * min(1.0, 2 - 2 * health_percentage)):02X}{int(255 * min(1.0, 2 * health_percentage)):02X}50"

def draw_name(pme, player_name, center_x, y, color="#FFFFFF", font_size=12):
	if player_name:
		draw_text(pme, player_name, center_x - measure_text(pme, player_name, font_size) / 2, y, font_size, pme.get_color(color))

def draw_distance(pme, center_x, y, distance, color="#C8C8C8", font_size=12):
	distance_text = f"{distance:.0f}m"
	draw_text(pme, distance_text, center_x - measure_text(pme, distance_text, font_size) / 2, y, font_size, pme.get_color(color))

def draw_info(pme, lines, x, y, font_size=12):
	for index, (line, color) in enumerate(lines):
		draw_text(pme, line, x, y + index * (font_size + 1), font_size, pme.get_color(color))

def draw_weapon(pme, weapon_icon, center_x, y, color="#FFFFFF", font_size=14):
	if weapon_icon and WEAPON_FONT_ID in loadedFonts:
		draw_text(pme, weapon_icon, center_x - measure_text(pme, weapon_icon, font_size, WEAPON_FONT_ID) / 2, y, font_size, pme.get_color(color), WEAPON_FONT_ID)

def draw_thick_circle(pme, center_x, center_y, radius, color, thickness=1.0):
	ring_count = max(1, round(thickness * 2) - 1)
	for ring in range(ring_count):
		pme.draw_circle_lines(center_x, center_y, radius + (ring - (ring_count - 1) / 2) * 0.5, color)

def draw_health_bar(pme, health, x, y, height, bar_width=6, background_color="#303030", health_color="#90EE90", outline_color="#000000"):
	bar_x, y, bar_width, height = round(x - bar_width - 4), round(y), max(1, round(bar_width)), round(height)
	pme.draw_rectangle(bar_x - 1, y - 1, bar_width + 2, height + 2, color=pme.get_color(outline_color))
	pme.draw_rectangle(bar_x, y, bar_width, height, color=pme.get_color(background_color))
	health_percentage = max(0.0, min(1.0, health / 100.0))
	filled_height = round(height * health_percentage)
	pme.draw_rectangle(bar_x, y + (height - filled_height), bar_width, filled_height, color=pme.get_color(health_color))

def draw_tracer(pme, start_x, start_y, end_x, end_y, color, thickness=1.5):
	if end_y != -1:
		pme.draw_line(start_x, start_y, end_x, end_y, color=pme.get_color(color), thick=thickness)

def draw_skeleton(pme, bones, bone_connections, color, thickness=1.0):
	for start_bone, end_bone in bone_connections:
		if start_bone in bones and end_bone in bones:
			start = bones[start_bone]
			end = bones[end_bone]
			if start.x <= -1 or end.x <= -1:
				continue
			offset_x = (end.x - start.x)
			offset_y = (end.y - start.y)
			pme.draw_line(start.x + offset_x, start.y + offset_y, end.x - offset_x, end.y - offset_y, color=pme.get_color(color), thick=thickness)

def draw_head(pme, head_top, head_bottom, color, thickness=1.0):
	if head_top.x <= -1 or head_bottom.x <= -1:
		return
	radius = (head_bottom.y - head_top.y) / 2
	if radius <= 0:
		return
	draw_thick_circle(pme, (head_top.x + head_bottom.x) / 2, head_top.y + radius, radius, pme.get_color(color), thickness)

def draw_box(pme, rect_left, rect_top, rect_width, rect_height, color, thickness=1.0):
	pme.draw_rectangle_lines(rect_left, rect_top, rect_width, rect_height, color=pme.get_color(color), lineThick=thickness)

def draw_corner_box(pme, rect_left, rect_top, rect_width, rect_height, color, thickness=1.0):
	corner_length = min(rect_width, rect_height) * 0.25
	rect_right = rect_left + rect_width
	rect_bottom = rect_top + rect_height
	for x, y, direction_x, direction_y in ((rect_left, rect_top, 1, 1), (rect_right, rect_top, -1, 1), (rect_left, rect_bottom, 1, -1), (rect_right, rect_bottom, -1, -1)):
		pme.draw_line(x, y, x + corner_length * direction_x, y, color=pme.get_color(color), thick=thickness)
		pme.draw_line(x, y, x, y + corner_length * direction_y, color=pme.get_color(color), thick=thickness)

def draw_box_fill(pme, rect_left, rect_top, rect_width, rect_height, color, alpha):
	pme.draw_rectangle(rect_left, rect_top, rect_width, rect_height, color=pme.fade_color(pme.get_color(color), alpha))

def draw_grenade_timer(pme, label, time_left, duration, x, y, color, font_size=14):
	timer_text = f"{label} {time_left:.1f}s"
	text_width = measure_text(pme, timer_text, font_size)
	bar_width = max(text_width, 60)
	pme.draw_rectangle(x - bar_width / 2 - 4, y - 4, bar_width + 8, font_size + 14, color=pme.fade_color(pme.get_color("#000000"), 0.6))
	draw_text(pme, timer_text, x - text_width / 2, y, font_size, pme.get_color("#FFFFFF"))
	pme.draw_rectangle(x - bar_width / 2, y + font_size + 2, bar_width * min(1.0, time_left / duration), 3, color=pme.get_color(color))


def GetEntityFromHandle(processHandle, ListEntries, handle):
	ListEntry = ListEntries[(handle & 0x7FFF) >> 9]
	if not ListEntry:
		return 0
	return memfuncs.ProcMemHandler.ReadPointer(processHandle, ListEntry + 0x70 * (handle & 0x1FF))

def GetWeaponIcon(processHandle, ListEntries, pawn, Offsets):
	weaponServices = memfuncs.ProcMemHandler.ReadPointer(processHandle, pawn + Offsets.offset.m_pWeaponServices)
	if not weaponServices:
		return ""

	weapon = GetEntityFromHandle(processHandle, ListEntries, memfuncs.ProcMemHandler.ReadUInt(processHandle, weaponServices + Offsets.offset.m_hActiveWeapon))
	if not weapon:
		return ""

	weaponId = memfuncs.ProcMemHandler.ReadUShort(processHandle, weapon + Offsets.offset.m_AttributeManager + Offsets.offset.m_Item + Offsets.offset.m_iItemDefinitionIndex)
	return WEAPON_ICONS.get(weaponId, "]" if weaponId >= 500 else "")

def UpdateGrenadeEntities(processHandle, ListEntries, Offsets):
	global grenadeEntities, lastGrenadeScan
	if time.perf_counter() - lastGrenadeScan < 0.25:
		return
	lastGrenadeScan = time.perf_counter()

	nameIndex = Offsets.offset.m_designerName // 8
	foundEntities = []
	for ListEntry in ListEntries:
		if not ListEntry:
			continue
		try:
			identities = memoryview(memfuncs.ProcMemHandler.ReadBytes(processHandle, ListEntry, 512 * 0x70)).cast("Q").tolist()
		except:
			continue

		for index in range(0, len(identities), 14):
			entity = identities[index]
			namePointer = identities[index + nameIndex]
			if not entity or not namePointer:
				continue

			if namePointer not in designerNames:
				try:
					designerNames[namePointer] = memfuncs.ProcMemHandler.ReadString(processHandle, namePointer, 32)
				except:
					designerNames[namePointer] = ""

			if designerNames[namePointer] in GRENADE_TIMERS:
				foundEntities.append((entity, designerNames[namePointer]))
	grenadeEntities = foundEntities

def DrawGrenadeTimers(processHandle, clientBaseAddress, ListEntries, viewMatrix, Offsets):
	UpdateGrenadeEntities(processHandle, ListEntries, Offsets)
	if not grenadeEntities:
		return

	globalVars = memfuncs.ProcMemHandler.ReadPointer(processHandle, clientBaseAddress + Offsets.offset.dwGlobalVars)
	currentTime = memfuncs.ProcMemHandler.ReadFloat(processHandle, globalVars + 0x30)

	for entity, designerName in grenadeEntities:
		try:
			label, duration, color = GRENADE_TIMERS[designerName]
			if not memfuncs.ProcMemHandler.ReadBool(processHandle, entity + Offsets.offset.m_bDidSmokeEffect):
				continue
			tickBegin = memfuncs.ProcMemHandler.ReadInt(processHandle, entity + Offsets.offset.m_nSmokeEffectTickBegin)
			position = memfuncs.ProcMemHandler.ReadVec(processHandle, entity + Offsets.offset.m_vSmokeDetonationPos)

			timeLeft = duration - (currentTime - tickBegin / 64.0)
			if tickBegin <= 0 or not 0 < timeLeft <= duration:
				continue

			screen = calculations.world_to_screen(viewMatrix, position)
			if screen.x <= -1 or screen.y <= -1:
				continue

			draw_grenade_timer(pme, label, timeLeft, duration, screen.x, screen.y, color)
		except:
			continue


def ESP_Update(processHandle, clientBaseAddress, Options, Offsets, SharedBombState):
	global lastLocalController
	if win32gui.GetWindowText(win32gui.GetForegroundWindow()) != "Counter-Strike 2":
			pme.end_drawing()
			return

	try:
		localPlayerEnt_pawnAddress = memfuncs.ProcMemHandler.ReadPointer(processHandle, clientBaseAddress + Offsets.offset.dwLocalPlayerPawn)
		localPlayerEnt_controllerAddress = memfuncs.ProcMemHandler.ReadPointer(processHandle, clientBaseAddress + Offsets.offset.dwLocalPlayerController)
		localPlayerEnt_Team = memfuncs.ProcMemHandler.ReadInt(processHandle, localPlayerEnt_pawnAddress + Offsets.offset.m_iTeamNum)
		localPlayerEnt_origin = memfuncs.ProcMemHandler.ReadVec(processHandle, localPlayerEnt_pawnAddress + Offsets.offset.m_vOldOrigin)

		viewMatrix = memfuncs.ProcMemHandler.ReadMatrix(processHandle, clientBaseAddress + Offsets.offset.dwViewMatrix)
		EntityList = memfuncs.ProcMemHandler.ReadPointer(processHandle, clientBaseAddress + Offsets.offset.dwEntityList)
		ListEntries = struct.unpack("64Q", memfuncs.ProcMemHandler.ReadBytes(processHandle, EntityList + 0x10, 64 * 8))
		Controllers = memoryview(memfuncs.ProcMemHandler.ReadBytes(processHandle, ListEntries[0], 65 * 0x70)).cast("Q")[::14].tolist()

		if localPlayerEnt_controllerAddress != lastLocalController:
			lastLocalController = localPlayerEnt_controllerAddress
			designerNames.clear()
	except:
		Controllers = []

	pme.begin_drawing()

	for controller in Controllers[1:]:
		try:
			if not controller or controller == localPlayerEnt_controllerAddress:
				continue

			pawnHandle = memfuncs.ProcMemHandler.ReadInt(processHandle, controller + Offsets.offset.m_hPlayerPawn)
			if not pawnHandle:
				continue

			pawn = GetEntityFromHandle(processHandle, ListEntries, pawnHandle)
			if not pawn or pawn == localPlayerEnt_pawnAddress:
				continue

			health = memfuncs.ProcMemHandler.ReadInt(processHandle, pawn + Offsets.offset.m_iHealth)
			team = memfuncs.ProcMemHandler.ReadInt(processHandle, controller + Offsets.offset.m_iTeamNum)
			lifeState = memfuncs.ProcMemHandler.ReadInt(processHandle, pawn + Offsets.offset.m_lifeState)

			if lifeState != 256 or (Options["EnableESPTeamCheck"] and team == localPlayerEnt_Team):
				continue

			sceneNode = memfuncs.ProcMemHandler.ReadPointer(processHandle, pawn + Offsets.offset.m_pGameSceneNode)
			boneArray = memfuncs.ProcMemHandler.ReadPointer(processHandle, sceneNode + Offsets.offset.m_modelState + Offsets.offset.m_boneArray)
			if not boneArray:
				continue
			boneData = memfuncs.ProcMemHandler.ReadBytes(processHandle, boneArray, BONE_READ_SIZE)
			origin = memfuncs.ProcMemHandler.ReadVec(processHandle, pawn + Offsets.offset.m_vOldOrigin)

			entity_head = Vector3(*struct.unpack_from("fff", boneData, 6 * 32))
			screen_head = calculations.world_to_screen(viewMatrix, Vector3(entity_head.x, entity_head.y, entity_head.z + 7))
			screen_feet = calculations.world_to_screen(viewMatrix, origin)
			box_top = calculations.world_to_screen(viewMatrix, Vector3(origin.x, origin.y, origin.z + 70))

			if screen_head.x <= -1 or screen_feet.y <= -1 or screen_head.x >= globals.SCREEN_WIDTH or screen_head.y >= globals.SCREEN_HEIGHT:
				continue

			distance = calculations.distance_vec3(origin, localPlayerEnt_origin)
			if distance < 35:
				continue

			box_height = screen_feet.y - box_top.y
			rect_left = screen_feet.x - box_height / 4
			rect_top = box_top.y
			rect_width = box_height / 2
			rect_height = box_height
			rect_center_x = rect_left + rect_width / 2
			rect_center_y = rect_top + rect_height / 2

			color = Options["T_color"] if team == 2 else Options["CT_color"]
			text_size = max(10, min(12, rect_height / 14))
			bottom_y = rect_top + rect_height + 3

			if Options["EnableESPBoxFill"]:
				draw_box_fill(pme, rect_left, rect_top, rect_width, rect_height, Options["BoxFill_color"], Options["ESPBoxFillAlpha"])

			if Options["EnableESPBoxRendering"]:
				if Options["ESPBoxStyle"] == "Cornered":
					draw_corner_box(pme, rect_left, rect_top, rect_width, rect_height, color=color, thickness=Options["ESPBoxThickness"])
				else:
					draw_box(pme, rect_left, rect_top, rect_width, rect_height, color=color, thickness=Options["ESPBoxThickness"])

			if Options["EnableESPNameText"]:
				EntityNameAddress = memfuncs.ProcMemHandler.ReadPointer(processHandle, controller + Offsets.offset.m_sSanitizedPlayerName)
				name = memfuncs.ProcMemHandler.ReadString(processHandle, EntityNameAddress, 64) if EntityNameAddress else "?"
				draw_name(pme, name.strip(), rect_center_x, rect_top - text_size - 3, font_size=text_size)

			if Options["EnableESPHealthBarRendering"]:
				draw_health_bar(pme, health, rect_left, rect_top, rect_height, bar_width=max(2, min(6, rect_height / 35)))

			info_lines = []
			if Options["EnableESPHealthText"]:
				info_lines.append((f"{health}HP", get_health_color(health)))

			if Options["EnableESPArmorText"] or Options["EnableESPFlagsText"]:
				itemServices = memfuncs.ProcMemHandler.ReadPointer(processHandle, pawn + Offsets.offset.m_pItemServices)

			if Options["EnableESPArmorText"]:
				armor = memfuncs.ProcMemHandler.ReadInt(processHandle, pawn + Offsets.offset.m_ArmorValue)
				helmet = itemServices and memfuncs.ProcMemHandler.ReadBool(processHandle, itemServices + Offsets.offset.m_bHasHelmet)
				if armor > 0:
					info_lines.append((f"HK {armor}" if helmet else f"K {armor}", "#8AB4F8"))

			if Options["EnableESPMoneyText"]:
				moneyServices = memfuncs.ProcMemHandler.ReadPointer(processHandle, controller + Offsets.offset.m_pInGameMoneyServices)
				if moneyServices:
					info_lines.append((f"${memfuncs.ProcMemHandler.ReadInt(processHandle, moneyServices + Offsets.offset.m_iAccount)}", "#85BB65"))

			if Options["EnableESPFlagsText"]:
				if itemServices and memfuncs.ProcMemHandler.ReadBool(processHandle, itemServices + Offsets.offset.m_bHasDefuser):
					info_lines.append(("KIT", "#4FC3F7"))
				if memfuncs.ProcMemHandler.ReadBool(processHandle, pawn + Offsets.offset.m_bIsScoped):
					info_lines.append(("ZOOM", "#FFD54F"))
				if memfuncs.ProcMemHandler.ReadBool(processHandle, pawn + Offsets.offset.m_bIsDefusing):
					info_lines.append(("DEFUSE", "#FF6B6B"))

			if info_lines:
				draw_info(pme, info_lines, rect_left + rect_width + 4, rect_top, font_size=text_size)

			if Options["EnableESPWeaponText"]:
				icon_size = max(10, min(16, rect_height / 9))
				draw_weapon(pme, GetWeaponIcon(processHandle, ListEntries, pawn, Offsets), rect_center_x, bottom_y, font_size=icon_size)
				bottom_y += icon_size + 2

			if Options["EnableESPDistanceText"]:
				draw_distance(pme, rect_center_x, bottom_y, math.dist((origin.x, origin.y, origin.z), (localPlayerEnt_origin.x, localPlayerEnt_origin.y, localPlayerEnt_origin.z)) * 0.0254, font_size=text_size)

			if Options["EnableESPTracerRendering"]:
				draw_tracer(pme, globals.SCREEN_WIDTH / 2, globals.SCREEN_HEIGHT, rect_center_x, rect_center_y, color=color)

			if Options["EnableESPHeadCircle"]:
				head_pos = Vector3(*struct.unpack_from("fff", boneData, PLAYER_BONES["head"] * 32))
				head_top = calculations.world_to_screen(viewMatrix, Vector3(head_pos.x, head_pos.y, head_pos.z + 7))
				head_bottom = calculations.world_to_screen(viewMatrix, Vector3(head_pos.x, head_pos.y, head_pos.z - 5))
				draw_head(pme, head_top, head_bottom, color=color, thickness=Options["ESPSkeletonThickness"])

			if Options["EnableESPSkeletonRendering"]:
				bones = {}
				for bone_name, bone_index in PLAYER_BONES.items():
					bone_pos = Vector3(*struct.unpack_from("fff", boneData, bone_index * 32))
					bones[bone_name] = calculations.world_to_screen(viewMatrix, bone_pos)

				draw_skeleton(pme, bones, boneConnections, color=color, thickness=Options["ESPSkeletonThickness"])
		except:
			continue

	if Options["EnableESPGrenadeTimers"] and Controllers:
		try:
			DrawGrenadeTimers(processHandle, clientBaseAddress, ListEntries, viewMatrix, Offsets)
		except:
			pass

	if Options["EnableFOVCircle"]:
		pme.draw_circle_lines(globals.SCREEN_WIDTH // 2, globals.SCREEN_HEIGHT // 2, Options["AimbotFOV"], pme.get_color(Options["FOV_color"]))

	try:
		if Options["EnableESPBombTimer"]:
			time_left = SharedBombState.bombTimeLeft

			if SharedBombState.bombPlanted:
				if time_left < 0:
					bomb_text = "Bomb Planted\nTime: --"
					text_height = 70
					y_offset = -30
				else:
					bomb_text = f"Bomb Planted\n{int(time_left)}s until detonation"
					text_height = 70
					y_offset = -30
			else:
				bomb_text = "Bomb Not Planted"
				text_height = 30
				y_offset = 15

			font_size = 25.0
			text_color = pme.get_color("#ffffff")
			background_color = pme.fade_color(pme.get_color("#000000"), 0.6)

			text_width = measure_text(pme, bomb_text, font_size)
			background_width = text_width + 20
			background_height = text_height + 15

			y_position = globals.SCREEN_HEIGHT // 2 + y_offset

			pme.draw_rectangle(10, y_position, background_width, background_height, background_color)
			draw_text(pme, bomb_text, 20, y_position + 10, font_size, text_color)
	except Exception:
		pass



	pme.end_drawing()