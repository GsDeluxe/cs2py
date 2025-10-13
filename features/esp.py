from ext.datatypes import *
from functions import memfuncs
from functions import calculations
from functions import gameinput
import globals
import win32api, win32gui
import pyMeow as pme
import time
import concurrent.futures

boneConnections = [
	('head', 'neck_0'), ('neck_0', 'spine_1'), ('spine_1', 'spine_2'), ('spine_2', 'pelvis'),
	('pelvis', 'leg_upper_L'), ('leg_upper_L', 'leg_lower_L'), ('leg_lower_L', 'ankle_L'),
	('pelvis', 'leg_upper_R'), ('leg_upper_R', 'leg_lower_R'), ('leg_lower_R', 'ankle_R'),
	('spine_2', 'arm_upper_L'), ('arm_upper_L', 'arm_lower_L'), ('arm_lower_L', 'hand_L'),
	('spine_2', 'arm_upper_R'), ('arm_upper_R', 'arm_lower_R'), ('arm_lower_R', 'hand_R')
]

def draw_name(pme, player_name, x, y, color="#FFFFFF", font_size=12):
	if player_name:
		pme.draw_text(player_name, x, y, fontSize=font_size, color=pme.get_color(color))

def draw_distance(pme, x, y, distance, color="#FFFFFF", font_size=12):
	pme.draw_text(f"{distance:.1f}m", x, y, fontSize=font_size, color=pme.get_color(color))

def draw_health_bar(pme, health, x, y, height, bar_width=6, background_color="#303030", health_color="#90EE90", outline_color="#505050"):
	pme.draw_rectangle(x - bar_width - 5, y, bar_width, height, color=pme.get_color(background_color))
	health_percentage = min(1.0, health / 100.0)
	filled_height = height * health_percentage
	pme.draw_rectangle(x - bar_width - 5, y + (height - filled_height), bar_width, filled_height, color=pme.get_color(health_color))
	pme.draw_rectangle_lines(x - bar_width - 5, y, bar_width, height, color=pme.get_color(outline_color), lineThick=1)

def draw_tracer(pme, start_x, start_y, end_x, end_y, color, thickness=1.5):
	if end_y != -1:
		pme.draw_line(start_x, start_y, end_x, end_y, color=pme.get_color(color), thick=thickness)

def draw_skeleton(pme, bones, bone_connections, color):
	for start_bone, end_bone in bone_connections:
		if start_bone in bones and end_bone in bones:
			start = bones[start_bone]
			end = bones[end_bone]
			offset_x = (end.x - start.x)
			offset_y = (end.y - start.y)
			pme.draw_line(start.x + offset_x, start.y + offset_y, end.x - offset_x, end.y - offset_y, color=pme.get_color(color), thick=1)

def draw_box(pme, rect_left, rect_top, rect_width, rect_height, color):
	pme.draw_rectangle_lines(rect_left, rect_top, rect_width, rect_height, color=pme.get_color(color), lineThick=1.0)


def ESP_Update(processHandle, clientBaseAddress, Options, Offsets, SharedBombState):
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
	except:
		pass

	pme.begin_drawing()

	for i in range(64):
		try:
			ListEntry = memfuncs.ProcMemHandler.ReadPointer(processHandle, EntityList + (8 * (i & 0x7FFF) >> 9) + 16)
			if not ListEntry:
				continue

			controller = memfuncs.ProcMemHandler.ReadPointer(processHandle, ListEntry + 120 * (i & 0x1FF))
			if not controller or controller == localPlayerEnt_controllerAddress:
				continue

			pawnHandle = memfuncs.ProcMemHandler.ReadInt(processHandle, controller + Offsets.offset.m_hPlayerPawn)
			if not pawnHandle:
				continue

			ListEntry2 = memfuncs.ProcMemHandler.ReadPointer(processHandle, EntityList + 0x8 * ((pawnHandle & 0x7FFF) >> 9) + 0x10)
			if not ListEntry2:
				continue

			pawn = memfuncs.ProcMemHandler.ReadPointer(processHandle, ListEntry2 + 0x78 * (pawnHandle & 0x1FF))
			if not pawn or pawn == localPlayerEnt_pawnAddress:
				continue

			health = memfuncs.ProcMemHandler.ReadInt(processHandle, pawn + Offsets.offset.m_iHealth)
			team = memfuncs.ProcMemHandler.ReadInt(processHandle, controller + Offsets.offset.m_iTeamNum)
			lifeState = memfuncs.ProcMemHandler.ReadInt(processHandle, pawn + Offsets.offset.m_lifeState)

			if lifeState != 256 or (Options["EnableESPTeamCheck"] and team == localPlayerEnt_Team):
				continue

			sceneNode = memfuncs.ProcMemHandler.ReadPointer(processHandle, pawn + Offsets.offset.m_pGameSceneNode)
			boneMatrix = memfuncs.ProcMemHandler.ReadPointer(processHandle, sceneNode + Offsets.offset.m_modelState + 0x80)
			origin = memfuncs.ProcMemHandler.ReadVec(processHandle, pawn + Offsets.offset.m_vOldOrigin)

			entity_head = memfuncs.ProcMemHandler.ReadVec(processHandle, boneMatrix + (6 * 32))
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

			if Options["EnableESPBoxRendering"]:
				draw_box(pme, rect_left, rect_top, rect_width, rect_height, color=color)

			if Options["EnableESPNameText"]:
				EntityNameAddress = memfuncs.ProcMemHandler.ReadPointer(processHandle, controller + Offsets.offset.m_sSanitizedPlayerName)
				name = memfuncs.ProcMemHandler.ReadString(processHandle, EntityNameAddress, 64) if EntityNameAddress else "?"
				draw_name(pme, name.strip(), rect_left + rect_width / 2, rect_top - 20)

			if Options["EnableESPDistanceText"]:
				draw_distance(pme, rect_left + rect_width / 2, rect_top - 40, distance)

			if Options["EnableESPHealthBarRendering"]:
				draw_health_bar(pme, health, rect_left, rect_top, rect_height)

			if Options["EnableESPTracerRendering"]:
				draw_tracer(pme, globals.SCREEN_WIDTH / 2, globals.SCREEN_HEIGHT, rect_center_x, rect_center_y, color=color)

			if Options["EnableESPSkeletonRendering"]:
				bone_array = memfuncs.ProcMemHandler.ReadPointer(processHandle, sceneNode + Offsets.offset.m_modelState + Offsets.offset.m_boneArray)
				if not bone_array:
					continue

				bones = {}
				for bone_name, bone_index in PLAYER_BONES.items():
					bone_pos = memfuncs.ProcMemHandler.ReadVec(processHandle, bone_array + bone_index * 32)
					bones[bone_name] = calculations.world_to_screen(viewMatrix, bone_pos)

				draw_skeleton(pme, bones, boneConnections, color=color)
		except:
			continue

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

			text_width = pme.measure_text(bomb_text, int(font_size))
			background_width = text_width + 20
			background_height = text_height + 15

			y_position = globals.SCREEN_HEIGHT // 2 + y_offset
			
			pme.draw_rectangle(10, y_position, background_width, background_height, background_color)
			pme.draw_text(bomb_text, 20, y_position + 10, fontSize=font_size, color=text_color)
	except Exception:
		pass

	pme.end_drawing()