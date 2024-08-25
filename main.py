import ctypes
import pymem
import time
import threading
import pyMeow as pme
import pymem.exception
from win32gui import GetWindowText, GetForegroundWindow
import offsets
import os
import keyboard
from random import uniform
from pynput.mouse import Controller, Button

import customtkinter as ctk
from tkinter import BooleanVar, StringVar
from CTkColorPicker import AskColor
import webbrowser

from ext_types import * 
from memfuncs import memfunc


# Load the DLLs
user32 = ctypes.WinDLL('user32.dll')
kernel32 = ctypes.WinDLL('kernel32')
kernel32.ReadProcessMemory.argtypes = [ctypes.wintypes.HANDLE,ctypes.wintypes.LPCVOID,ctypes.wintypes.LPVOID,ctypes.wintypes.SIZE,ctypes.POINTER(ctypes.wintypes.SIZE)]
kernel32.ReadProcessMemory.restype = ctypes.wintypes.BOOL

bones = {
	"head": 6,
	"neck_0": 5,
	"spine_1": 4,
	"spine_2": 2,
	"pelvis": 0,
	"arm_upper_L": 8,
	"arm_lower_L": 9,
	"hand_L": 10,
	"arm_upper_R": 13,
	"arm_lower_R": 14,
	"hand_R": 15,
	"leg_upper_L": 22,
	"leg_lower_L": 23,
	"ankle_L": 24,
	"leg_upper_R": 25,
	"leg_lower_R": 26,
	"ankle_R": 27,
	}

team_check: bool = False
skeleton_rendering: bool = True
box_rendering: bool = True
tracer_rendering: bool = True
name_rendering: bool = True
health_bar_rendering: bool = True
health_text_rendering: bool = True

t_color: str = "#8A2BE2"
ct_color: str = "#8A2BE2"

mouse = Controller()
enable_triggerbot: bool = False
triggerbot_key: str = "shift"
triggerbot_team_check: bool = False

anti_flashbang: bool = False
enable_bhop: bool = False
player_fov: int = 105
fov_changer_option: bool = False
enable_bomb_timer: bool = True; bomb_time_left: int = -1; bombPlanted: bool = False

enable_aimbot: bool = True
aimbot_team_check: bool = True
visibility_check: bool = False
enable_aimbot_fov: bool = False
aimbot_fov: float = 400
aimbot_smoothness: float = 2.0
aim_position = bones["head"]

def world_to_screen(view_matrix: Matrix, position: Vector3):
	mat = view_matrix.matrix

	x, y, z = position.x, position.y, position.z

	screen_x = (mat[0][0] * x + mat[0][1] * y + mat[0][2] * z + mat[0][3])
	screen_y = (mat[1][0] * x + mat[1][1] * y + mat[1][2] * z + mat[1][3])
	w = (mat[3][0] * x + mat[3][1] * y + mat[3][2] * z + mat[3][3])
	
	if w < 0.01:
		return -1.0, -1.0
	
	invw = 1.0 / w
	screen_x *= invw
	screen_y *= invw
	
	user32 = ctypes.WinDLL('user32')
	width = user32.GetSystemMetrics(0)
	height = user32.GetSystemMetrics(1)
	
	width_float = float(width)
	height_float = float(height)
	
	x = width_float / 2.0
	y = height_float / 2.0
	
	x += 0.5 * screen_x * width_float + 0.5
	y -= 0.5 * screen_y * height_float + 0.5
	
	return x, y

def calculate_angles(from_: Vector3, to: Vector3) -> Vector2:
	yaw = 0.0
	pitch = 0.0

	deltaX = to.x - from_.x
	deltaY = to.y - from_.y
	deltaZ = to.z - from_.z

	yaw = math.atan2(deltaY, deltaX) * 180 / math.pi
	distance = math.sqrt(math.pow(deltaX,2) + math.pow(deltaY, 2))
	pitch = -(math.atan2(deltaZ, distance) * 180 / math.pi)

	return Vector2(yaw, pitch)

def get_entities_info(mem: memfunc, client_dll: int, screen_width: int, screen_height: int, offsets: Offset, team_check: bool) -> List[Entity]:
	entities = []

	entity_list = mem.ReadPointer(client_dll, offsets.dwEntityList)

	if not entity_list:
		return entities

	local_player_p = mem.ReadPointer(client_dll, offsets.dwLocalPlayerPawn)
	if not local_player_p:
		return entities

	local_player_game_scene = mem.ReadPointer(local_player_p, offsets.m_pGameSceneNode)
	if not local_player_game_scene:
		return entities

	local_player_scene_origin = mem.ReadVec(local_player_game_scene, offsets.m_nodeToWorld)
	view_matrix_flat = mem.ReadMatrix(client_dll + offsets.dwViewMatrix)
	view_matrix = Matrix([
		[view_matrix_flat[0], view_matrix_flat[1], view_matrix_flat[2], view_matrix_flat[3]],
		[view_matrix_flat[4], view_matrix_flat[5], view_matrix_flat[6], view_matrix_flat[7]],
		[view_matrix_flat[8], view_matrix_flat[9], view_matrix_flat[10], view_matrix_flat[11]],
		[view_matrix_flat[12], view_matrix_flat[13], view_matrix_flat[14], view_matrix_flat[15]]])

	for i in range(64):
		temp_entity = Entity(
			Health=0,
			Team=0,
			Name="",
			Position=Vector2(0, 0),
			Bones={},
			HeadPos=Vector3(0, 0, 0),
			Distance=0,
			Rect=Rectangle(0, 0, 0, 0),
			OnScreen=False,
			pawnAddress=None,
			controllerAddress=None,
			origin=None,
			lifestate=None,
			distance=None,
			head2d=None,
			pixelDistance=None,
			view=None
		)
		entity_bones = {}

		# Read list entry
		list_entry = mem.ReadPointer(entity_list, (8 * (i & 0x7FFF) >> 9) + 16)
		if not list_entry:
			continue

		# Read entity controller
		entity_controller = mem.ReadPointer(list_entry, 120 * (i & 0x1FF))
		if not entity_controller:
			continue

		# Read entity controller pawn
		entity_controller_pawn = mem.ReadPointer(entity_controller, offsets.m_hPlayerPawn)
		if not entity_controller_pawn:
			continue

		# Read list entry again
		list_entry = mem.ReadPointer(entity_list, (0x8 * ((entity_controller_pawn & 0x7FFF) >> 9) + 16))
		if not list_entry:
			continue

		# Read entity pawn
		entity_pawn = mem.ReadPointer(list_entry, 120 * (entity_controller_pawn & 0x1FF))
		if not entity_pawn or entity_pawn == local_player_p:
			continue

		# Read entity life state
		entity_life_state = mem.ReadInt(entity_pawn, offsets.m_lifeState)
		if entity_life_state != 256:
			continue

		# Read entity team
		entity_team = mem.ReadInt(entity_pawn, offsets.m_iTeamNum)
		if entity_team == 0:
			continue

		if team_check:
			local_team = mem.ReadInt(local_player_p, offsets.m_iTeamNum)
			if local_team == entity_team:
				continue

		# Read entity health
		entity_health = mem.ReadInt(entity_pawn, offsets.m_iHealth)
		if entity_health < 1 or entity_health > 100:
			continue

		# Read entity name address
		entity_name_address = mem.ReadPointer(entity_controller, offsets.m_sSanitizedPlayerName)
		if not entity_name_address:
			continue

		# Read entity name
		entity_name = mem.ReadString(entity_name_address, 64)
		if not entity_name:
			continue

		sanitized_name = ''.join(c for c in entity_name if c.isalnum() or c in ' .,!')

		# Read game scene
		game_scene = mem.ReadPointer(entity_pawn, offsets.m_pGameSceneNode)
		if not game_scene:
			continue

		# Read entity bone array
		entity_bone_array = mem.ReadPointer(game_scene, offsets.m_modelState + offsets.m_boneArray)
		if not entity_bone_array:
			continue

		# Read entity origin
		entity_origin = mem.ReadVec(entity_pawn, offsets.m_vOldOrigin)
		if not entity_origin:
			continue

		# Process bone array
		for bone_name, bone_index in bones.items():
			current_bone = mem.ReadVec(entity_bone_array, bone_index * 32)
			if bone_name == "head":
				entity_head = current_bone

			bone_x, bone_y = world_to_screen(view_matrix, current_bone)
			entity_bones[bone_name] = Vector2(bone_x, bone_y)

		entity_head_top = Vector3(entity_head.x, entity_head.y, entity_head.z + 7)
		entity_head_bottom = Vector3(entity_head.x, entity_head.y, entity_head.z - 5)
		screen_pos_head_x, screen_pos_head_top_y = world_to_screen(view_matrix, entity_head_top)
		_, screen_pos_head_bottom_y = world_to_screen(view_matrix, entity_head_bottom)
		screen_pos_feet_x, screen_pos_feet_y = world_to_screen(view_matrix, entity_origin)
		entity_box_top = Vector3(entity_origin.x, entity_origin.y, entity_origin.z + 70)
		_, screen_pos_box_top = world_to_screen(view_matrix, entity_box_top)

		
		if screen_pos_head_x <= -1 or screen_pos_feet_y <= -1 or screen_pos_head_x >= screen_width or screen_pos_head_top_y >= screen_height:
			OnScreen = False
		OnScreen = True

		box_height = screen_pos_feet_y - screen_pos_box_top

		temp_entity.Health = entity_health
		temp_entity.Team = entity_team
		temp_entity.Name = sanitized_name
		temp_entity.Distance = distance_vec3(entity_origin, local_player_scene_origin)
		temp_entity.Position = Vector2(screen_pos_feet_x, screen_pos_feet_y)
		temp_entity.Bones = entity_bones
		temp_entity.HeadPos = Vector3(screen_pos_head_x, screen_pos_head_top_y, screen_pos_head_bottom_y)
		temp_entity.Rect = Rectangle(screen_pos_box_top, screen_pos_feet_x - box_height / 4, screen_pos_feet_x + box_height / 4, screen_pos_feet_y)
		temp_entity.OnScreen = OnScreen

		entities.append(temp_entity)

	return entities


def get_offsets() -> Offset:
	offsets_obj = Offset(
		dwViewMatrix=offsets.Client().offset("dwViewMatrix"),
		dwLocalPlayerPawn=offsets.Client().offset("dwLocalPlayerPawn"),
		dwEntityList=offsets.Client().offset("dwEntityList"),
		dwLocalPlayerController=offsets.Client().offset("dwLocalPlayerController"),
		dwViewAngles = offsets.Client().offset("dwViewAngles"),
		dwGameRules = offsets.Client().offset("dwGameRules"),

		ButtonJump=offsets.Client().button("jump"),
		
		m_hPlayerPawn=offsets.Client().get("CCSPlayerController", "m_hPlayerPawn"),
		m_iHealth=offsets.Client().get("C_BaseEntity", "m_iHealth"),
		m_lifeState=offsets.Client().get("C_BaseEntity", "m_lifeState"),
		m_iTeamNum=offsets.Client().get("C_BaseEntity", "m_iTeamNum"),
		m_vOldOrigin=offsets.Client().get("C_BasePlayerPawn", "m_vOldOrigin"),
		m_pGameSceneNode=offsets.Client().get("C_BaseEntity", "m_pGameSceneNode"),
		m_modelState=offsets.Client().get("CSkeletonInstance", "m_modelState"),
		m_boneArray=128,
		m_nodeToWorld=offsets.Client().get("CGameSceneNode", "m_nodeToWorld"),
		m_sSanitizedPlayerName=offsets.Client().get("CCSPlayerController", "m_sSanitizedPlayerName"),
		m_iIDEntIndex=offsets.Client().get("C_CSPlayerPawnBase", "m_iIDEntIndex"),
		m_flFlashMaxAlpha=offsets.Client().get("C_CSPlayerPawnBase", "m_flFlashMaxAlpha"),
		m_fFlags=offsets.Client().get("C_BaseEntity", "m_fFlags"),
		m_iFOV=offsets.Client().get("CCSPlayerBase_CameraServices", "m_iFOV"),
		m_pCameraServices=offsets.Client().get("C_BasePlayerPawn", "m_pCameraServices"),
		m_bIsScoped=offsets.Client().get("C_CSPlayerPawn", "m_bIsScoped"),
		m_vecViewOffset = offsets.Client().get("C_BaseModelEntity", "m_vecViewOffset"),
		m_entitySpottedState = offsets.Client().get("C_CSPlayerPawn", "m_entitySpottedState"),
		m_bSpotted = offsets.Client().get("EntitySpottedState_t", "m_bSpotted"),
		m_bBombPlanted = offsets.Client().get("C_CSGameRules", "m_bBombPlanted"),

	)

	return offsets_obj

def draw_box(pme, rect_left, rect_top, rect_width, rect_height, team):
	pme.draw_rectangle_lines(rect_left, rect_top, rect_width, rect_height, color=pme.get_color(t_color if team == 3 else ct_color), lineThick=1.0)

def draw_name(pme, player_name, text_x, text_y):
	if player_name:
		pme.draw_text(player_name, text_x, text_y, fontSize=15.0, color=pme.get_color("#ffffff"))

def draw_health_bar(pme, health, rect_left, rect_top, rect_height):
	if health > 0:
		health_bar_width = 5
		health_bar_height = rect_height
		health_bar_x = rect_left - health_bar_width - 5
		health_bar_y = rect_top
		
		health_percentage = min(1.0, health / 100.0)
		filled_height = health_bar_height * health_percentage

		# Draw filled health bar
		pme.draw_rectangle(health_bar_x, health_bar_y + (health_bar_height - filled_height), health_bar_width, filled_height, color=pme.get_color("#ff0000"))
		# Draw health bar border
		pme.draw_rectangle_lines(health_bar_x, health_bar_y, health_bar_width, health_bar_height, color=pme.get_color("#ffffff"), lineThick=1.0)
		
def draw_health_text(pme, health, rect_left, rect_top, rect_height):
	if health > 0:
		health_bar_width = 5
		health_bar_x = rect_left - health_bar_width - 5
		# Draw health number
		health_text = str(health)
		text_x = health_bar_x + health_bar_width / 2
		text_y = rect_top + rect_height + 5
		pme.draw_text(health_text, text_x, text_y, fontSize=20.0, color=pme.get_color("#ffffff"))

def draw_tracer(pme, start_pos_x, start_pos_y, rect_center_x, rect_center_y, team):
	if rect_center_y != -1:
		pme.draw_line(start_pos_x, start_pos_y, rect_center_x, rect_center_y, color=pme.get_color(t_color if team == 3 else ct_color), thick=2.0)

def draw_bones(pme, bones, bone_connections, team):
	for start_bone, end_bone in bone_connections:
		if start_bone in bones and end_bone in bones:
			pme.draw_line(bones[start_bone].x, bones[start_bone].y, bones[end_bone].x, bones[end_bone].y, color=pme.get_color(t_color if team == 3 else ct_color), thick=2.0)

def triggerbot_thread(memf, client, offsets):
	while True:
		try:
			if not GetWindowText(GetForegroundWindow()) == "Counter-Strike 2" or enable_triggerbot == False:
				time.sleep(0.1)
				continue

			if keyboard.is_pressed(triggerbot_key):
				player = memf.ReadPointer(client, offsets.dwLocalPlayerPawn)
				entityId = memf.ReadInt(player, offsets.m_iIDEntIndex)

				if entityId > 0:
					entList = memf.ReadPointer(client, offsets.dwEntityList)
					entEntry = memf.ReadPointer(entList, 0x8 * (entityId >> 9) + 0x10)
					entity = memf.ReadPointer(entEntry, 120 * (entityId & 0x1FF))

					entityTeam = memf.ReadInt(entity, offsets.m_iTeamNum)
					playerTeam = memf.ReadInt(player, offsets.m_iTeamNum)

					if not triggerbot_team_check or entityTeam != playerTeam:
						entityHp = memf.ReadInt(entity, offsets.m_iHealth)
						if entityHp > 0:
							if not user32.GetAsyncKeyState(0x01) < 0:
								time.sleep(uniform(0.01, 0.03))
								mouse.press(Button.left)
								time.sleep(uniform(0.01, 0.05))
								mouse.release(Button.left)

				time.sleep(0.03)
			else:
				time.sleep(0.1)
		except KeyboardInterrupt:
			break
		except:
			pass

def anti_flash_thread(memf: memfunc, client, offsets):
	while True:
		time.sleep(0.1)

		try:
			if anti_flashbang:
				player_pos = memf.ReadPointer(client, offsets.dwLocalPlayerPawn)
				if player_pos:
					memf.WriteFloat(player_pos, 0.0, offsets.m_flFlashMaxAlpha)
			else:
				memf.WriteFloat(player_pos, 255.0, offsets.m_flFlashMaxAlpha)
		except KeyboardInterrupt:
			break
		except:
			pass

def bhop_thread(memf, client, offsets):
	while True:
		try:
			entity_list = memf.ReadPointer(client, offsets.dwEntityList)
			local_player = memf.ReadPointer(client, offsets.dwLocalPlayerController)
			local_pawn = memf.ReadInt(local_player, offsets.m_hPlayerPawn)
			list_entry2 = memf.ReadPointer(entity_list, 0x8 * ((local_pawn & 0x7FFF) >> 9) + 16)
			local_player = memf.ReadPointer(list_entry2, 120 * (local_pawn & 0x1FF))

			if local_player and enable_bhop:
				flags = memf.ReadInt(local_player, offsets.m_fFlags)
				if user32.GetAsyncKeyState(0x20) and flags & (1 << 0): # check space and if on ground
					memf.WriteInt(client, 65537, offsets.ButtonJump)
					time.sleep(0.1)
					memf.WriteInt(client, 256, offsets.ButtonJump)
			time.sleep(0.01)
		except KeyboardInterrupt:
			break
		except Exception as e:
			pass


def fov_changer_thread(memf: memfunc, client, offsets):
	while True:
		try:
			local_player_p = memf.ReadPointer(client, offsets.dwLocalPlayerPawn)
			camera_services = memf.ReadPointer(local_player_p, offsets.m_pCameraServices)
			current_fov = memf.ReadInt(camera_services, offsets.m_iFOV)
			is_scoped = memf.ReadBool(local_player_p, offsets.m_bIsScoped)

			if fov_changer_option:
				if not is_scoped:
					memf.WriteInt(camera_services, player_fov, offsets.m_iFOV)
			else:
				if current_fov != 105:
					memf.WriteInt(camera_services, 105, offsets.m_iFOV)
				
		except KeyboardInterrupt:
			break
		except Exception as e:
			print(e)
			pass
		time.sleep(0.001)

def check_in_game(memf, client, offsets):
	game_not_in_memory = True
	while True:
		try:
			get_entities_info(memf, client, user32.GetSystemMetrics(0), user32.GetSystemMetrics(1), offsets, False)
			if game_not_in_memory:
				print("[+] Game is in memory, proceeding...")
			break
		except pymem.exception.MemoryReadError as e:
			if game_not_in_memory:
				print("[*] Game not in memory. Waiting...")
				game_not_in_memory = False 
			time.sleep(1) 

def bomb_timer_thread(memf: memfunc, client, offsets: Offset):
	global bomb_time_left, bombPlanted

	while True:
		gameRule = memf.ReadPointer(client, offsets.dwGameRules)
		if gameRule:
			bombPlanted = memf.ReadBool(gameRule, offsets.m_bBombPlanted)
			if bombPlanted:
				for i in range(40):
					bombPlanted = memf.ReadBool(gameRule, offsets.m_bBombPlanted)
					if not bombPlanted:
						break

					bomb_time_left = 40 - i
					time.sleep(1)
			else:
				bomb_time_left = -1
				bombPlanted = False
		time.sleep(0.01)

def aimbot_thread(memf, client, offsets):
	entities = []
	localPlayer = Entity(
		Health=0,
		Team=0,
		Name="",
		Position=Vector2(0, 0),
		Bones={},
		HeadPos=Vector3(0, 0, 0),
		Distance=0,
		Rect=Rectangle(0, 0, 0, 0),
		OnScreen=False,
		pawnAddress=None,
		controllerAddress=None,
		origin=None,
		lifestate=None,
		distance=None,
		head2d=None,
		pixelDistance=None,
		view=None
	)
	while True:
		try:
			entities.clear()
			entityList = memf.ReadPointer(client, offsets.dwEntityList)

			localPlayer.pawnAddress = memf.ReadPointer(client, offsets.dwLocalPlayerPawn)
			localPlayer.team = memf.ReadInt(localPlayer.pawnAddress, offsets.m_iTeamNum)
			localPlayer.origin = memf.ReadVec(localPlayer.pawnAddress, offsets.m_vOldOrigin)
			localPlayer.view = memf.ReadVec(localPlayer.pawnAddress, offsets.m_vecViewOffset)
			localPlayer.HeadPos = None
			localPlayer.head2d = None

			for i in range(64): 
				ListEntry = memf.ReadPointer(entityList, (8 * (i & 0x7FFF) >> 9) + 16)

				if not ListEntry: continue

				currentController = memf.ReadPointer(ListEntry, 120 * (i & 0x1FF))
				if not currentController: continue

				pawnHandle = memf.ReadInt(currentController, offsets.m_hPlayerPawn)
				if not pawnHandle: continue

				listEntry2 = memf.ReadPointer(entityList, 0x8 * ((pawnHandle & 0x7FFF) >> 9) + 0x10)
				
				currentPawn = memf.ReadPointer(listEntry2, 0x78 * (pawnHandle & 0x1FF))
				if not currentPawn or currentPawn == localPlayer.pawnAddress: continue

				sceneNode = memf.ReadPointer(currentPawn, offsets.m_pGameSceneNode)
				boneMatrix = memf.ReadPointer(sceneNode, offsets.m_modelState + 0x80)

				health = memf.ReadInt(currentPawn, offsets.m_iHealth)
				team = memf.ReadInt(currentPawn, offsets.m_iTeamNum)
				lifestate = memf.ReadUInt(currentPawn, offsets.m_lifeState)
				spotted = memf.ReadBool(currentPawn, offsets.m_entitySpottedState + offsets.m_bSpotted)

				if visibility_check and not spotted:
					continue

				if lifestate != 256:
					continue

				if aimbot_team_check and localPlayer.team == team:
					continue

				temp_entity = Entity(
					Health=0,
					Team=0,
					Name="",
					Position=Vector2(0, 0),
					Bones={},
					HeadPos=Vector3(0, 0, 0),
					Distance=0,
					Rect=Rectangle(0, 0, 0, 0),
					OnScreen=False,
					pawnAddress=None,
					controllerAddress=None,
					origin=None,
					lifestate=None,
					distance=None,
					head2d=None,
					pixelDistance=None,
					view=None
				)
				temp_entity.pawnAddress = currentPawn
				temp_entity.controllerAddress = currentController
				temp_entity.health = health
				temp_entity.lifestate = lifestate
				temp_entity.team = team
				temp_entity.origin = memf.ReadVec(currentPawn, offsets.m_vOldOrigin)
				temp_entity.view = memf.ReadVec(currentPawn, offsets.m_vecViewOffset)
				temp_entity.distance = distance_vec3(temp_entity.origin, localPlayer.origin)
				temp_entity.head = memf.ReadVec(boneMatrix, aim_position * 32) # 6 is the head id in the bone matrix and 32 is the step
				
				view_matrix_flat = memf.ReadMatrix(client + offsets.dwViewMatrix)
				viewMatrix = Matrix([
					[view_matrix_flat[0], view_matrix_flat[1], view_matrix_flat[2], view_matrix_flat[3]],
					[view_matrix_flat[4], view_matrix_flat[5], view_matrix_flat[6], view_matrix_flat[7]],
					[view_matrix_flat[8], view_matrix_flat[9], view_matrix_flat[10], view_matrix_flat[11]],
					[view_matrix_flat[12], view_matrix_flat[13], view_matrix_flat[14], view_matrix_flat[15]]])

				w2sx, w2sy = world_to_screen(viewMatrix, temp_entity.head)
				temp_entity.head2d = Vector2(w2sx, w2sy)

				temp_entity.pixelDistance = distance_vec2(temp_entity.head2d, Vector2(user32.GetSystemMetrics(0) / 2, user32.GetSystemMetrics(1) / 2))
				entities.append(temp_entity)

			entities = sorted(entities, key=lambda o: o.distance)

			if len(entities) > 0 and user32.GetAsyncKeyState(0x06) & 0x8000 and enable_aimbot:
				playerView = Vector3.__add__(localPlayer.origin, localPlayer.view)
				# entityView = Vector3.__add__(entities[0].origin, entities[0].view)

				if entities[0].pixelDistance < aimbot_fov or enable_aimbot_fov == False:
					newAngles = calculate_angles(playerView, entities[0].head)
					newAnglesVec3 = Vector3(newAngles.y, newAngles.x, 0.0)

					memf.WriteVec(client, newAnglesVec3, offsets.dwViewAngles)
		except KeyboardInterrupt:
			break
		except:
			pass

def main():
	try:
		pm = pymem.Pymem("cs2.exe")
	except:
		print("[-] Error CS2 Procces Not Found")
		os._exit(0)
	
	client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
	memf = memfunc(proc=pm)
	
	print("[*] Getting Offsets")
	offsets = get_offsets()

	threading.Thread(target=GUI, daemon=True).start()
	threading.Thread(target=triggerbot_thread, args=(memf, client, offsets), daemon=True).start()
	threading.Thread(target=anti_flash_thread, args=(memf, client, offsets), daemon=True).start()
	threading.Thread(target=bhop_thread, args=(memf, client, offsets), daemon=True).start()
	threading.Thread(target=fov_changer_thread, args=(memf, client, offsets), daemon=True).start()
	threading.Thread(target=bomb_timer_thread, args=(memf, client, offsets), daemon=True).start()
	threading.Thread(target=aimbot_thread, args=(memf, client, offsets), daemon=True).start()

	print("[+] GUI Initialized")

	check_in_game(memf, client, offsets)

	if not GetWindowText(GetForegroundWindow()) == "Counter-Strike 2":
		print("[*] Change Window to CS2 to Show GUI")

	pme.overlay_init(title="cs2py")
	fps = pme.get_monitor_refresh_rate()
	pme.set_fps(fps)
	pme.gui_fade(0.9)
	width, height = pme.get_screen_width(), pme.get_screen_height()

	bone_connections = [
		('head', 'neck_0'),
		('neck_0', 'spine_1'),
		('spine_1', 'spine_2'),
		('spine_2', 'pelvis'),
		('pelvis', 'leg_upper_L'),
		('leg_upper_L', 'leg_lower_L'),
		('leg_lower_L', 'ankle_L'),
		('pelvis', 'leg_upper_R'),
		('leg_upper_R', 'leg_lower_R'),
		('leg_lower_R', 'ankle_R'),
		('arm_upper_L', 'arm_lower_L'),
		('arm_lower_L', 'hand_L'),
		('arm_upper_R', 'arm_lower_R'),
		('arm_lower_R', 'hand_R')
	]

	while pme.overlay_loop():
		pme.begin_drawing()

		if GetWindowText(GetForegroundWindow()) == "Counter-Strike 2":

			try:
				entities = get_entities_info(mem=memf, client_dll=client, screen_width=user32.GetSystemMetrics(0), screen_height=user32.GetSystemMetrics(1), offsets=offsets, team_check=team_check)
			except pymem.exception.MemoryReadError:
				print("[-] Error Reading Game")
				check_in_game(memf, client, offsets)
				continue

			for entity in entities:
				if entity.Distance < 35:
					continue

				rect_left = entity.Rect.Left
				rect_top = entity.Rect.Top
				rect_width = entity.Rect.Right - entity.Rect.Left
				rect_height = entity.Rect.Bottom - entity.Rect.Top
				rect_center_x = rect_left + rect_width / 2
				rect_center_y = rect_top + rect_height / 2
				start_pos_x, start_pos_y = width / 2, height

				# Check feature flags
				if entity.OnScreen:
					if box_rendering:
						draw_box(pme, rect_left, rect_top, rect_width, rect_height, entity.Team)

					if name_rendering:
						draw_name(pme, entity.Name, rect_left + rect_width / 2, rect_top - 15)

					if health_bar_rendering:
						draw_health_bar(pme, entity.Health, rect_left, rect_top, rect_height)

					if health_text_rendering:
						draw_health_text(pme, entity.Health, rect_left, rect_top, rect_height)

					if skeleton_rendering:
						draw_bones(pme, entity.Bones, bone_connections, entity.Team)

				if tracer_rendering:
					draw_tracer(pme, start_pos_x, start_pos_y, rect_center_x, rect_center_y, entity.Team)

				if enable_aimbot_fov:
					pme.draw_circle_lines(user32.GetSystemMetrics(0) // 2, user32.GetSystemMetrics(1) // 2, aimbot_fov, pme.get_color("#ffffff"))

				if enable_bomb_timer:
					if bombPlanted:
						bomb_text = f"Bomb Planted \n{str(bomb_time_left)}s until detonation"
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
					y_position = user32.GetSystemMetrics(1) // 2 + y_offset
					pme.draw_rectangle(10, y_position, background_width, background_height, background_color)
					pme.draw_text(bomb_text, 20, y_position + 10, fontSize=font_size, color=text_color)

		pme.end_drawing()

def GUI():
	def team_pick_color():
		color = AskColor().get()
		global team_color
		team_color = color
		team_color_button.configure(fg_color=color)

	def enemy_pick_color():
		color = AskColor().get()
		global enemy_color
		enemy_color = color
		enemy_color_button.configure(fg_color=color)

	def checkbox_action(var_name, var):
		globals()[var_name] = var.get()

	def on_closing():
		os._exit(0)

	def start_recording_key():
		triggerbot_key_var.set("Press a key...")
		keyboard.hook(on_key_event)

	def fov_slider_action(value):
		global player_fov
		player_fov = int(value)
		fov_value_label.configure(text=f"FOV: {int(float(value))}")

	def on_key_event(event):
		global triggerbot_key
		if event.event_type == keyboard.KEY_DOWN:
			triggerbot_key = event.name
			triggerbot_key_var.set(f"Trigger Key: {triggerbot_key}")
			keyboard.unhook_all()

	root = ctk.CTk()
	tabview = ctk.CTkTabview(root)
	tabview.pack(padx=10, pady=10, expand=True, fill="both")

	# ESP Tab
	tab_main = tabview.add("ESP")

	checkbox_1_var = ctk.BooleanVar(value=skeleton_rendering)
	checkbox_1 = ctk.CTkCheckBox(master=tab_main, text="Skeleton Rendering", variable=checkbox_1_var,
								 command=lambda: checkbox_action('skeleton_rendering', checkbox_1_var))
	checkbox_1.pack(padx=10, pady=5, anchor="w")

	checkbox_2_var = ctk.BooleanVar(value=box_rendering)
	checkbox_2 = ctk.CTkCheckBox(master=tab_main, text="Box Rendering", variable=checkbox_2_var,
								 command=lambda: checkbox_action('box_rendering', checkbox_2_var))
	checkbox_2.pack(padx=10, pady=5, anchor="w")

	checkbox_3_var = ctk.BooleanVar(value=tracer_rendering)
	checkbox_3 = ctk.CTkCheckBox(master=tab_main, text="Tracer Rendering", variable=checkbox_3_var,
								 command=lambda: checkbox_action('tracer_rendering', checkbox_3_var))
	checkbox_3.pack(padx=10, pady=5, anchor="w")

	checkbox_4_var = ctk.BooleanVar(value=name_rendering)
	checkbox_4 = ctk.CTkCheckBox(master=tab_main, text="Name Rendering", variable=checkbox_4_var,
								 command=lambda: checkbox_action('name_rendering', checkbox_4_var))
	checkbox_4.pack(padx=10, pady=5, anchor="w")

	checkbox_5_var = ctk.BooleanVar(value=health_bar_rendering)
	checkbox_5 = ctk.CTkCheckBox(master=tab_main, text="Health Bar Rendering", variable=checkbox_5_var,
								 command=lambda: checkbox_action('health_bar_rendering', checkbox_5_var))
	checkbox_5.pack(padx=10, pady=5, anchor="w")

	checkbox_6_var = ctk.BooleanVar(value=health_text_rendering)
	checkbox_6 = ctk.CTkCheckBox(master=tab_main, text="Health Text Rendering", variable=checkbox_6_var,
								 command=lambda: checkbox_action('health_text_rendering', checkbox_6_var))
	checkbox_6.pack(padx=10, pady=5, anchor="w")

	checkbox_7_var = ctk.BooleanVar(value=team_check)
	checkbox_7 = ctk.CTkCheckBox(master=tab_main, text="Team Check", variable=checkbox_7_var,
								 command=lambda: checkbox_action('team_check', checkbox_7_var))
	checkbox_7.pack(padx=10, pady=5, anchor="w")

	global enemy_color_button
	enemy_color_button = ctk.CTkButton(master=tab_main, text="Choose Terrorist Color", command=enemy_pick_color, fg_color=enemy_color, width=300)
	enemy_color_button.pack(padx=30, pady=10, anchor="w")

	global team_color_button
	team_color_button = ctk.CTkButton(master=tab_main, text="Choose Counter Terrorist Color", command=team_pick_color, fg_color=team_color, width=300)
	team_color_button.pack(padx=30, pady=10, anchor="w")

	# Triggerbot Tab
	tab_triggerbot = tabview.add("Triggerbot")

	triggerbot_enable_var = ctk.BooleanVar(value=enable_triggerbot)
	triggerbot_checkbox = ctk.CTkCheckBox(master=tab_triggerbot, text="Enable Triggerbot", variable=triggerbot_enable_var,
										  command=lambda: checkbox_action('enable_triggerbot', triggerbot_enable_var))
	triggerbot_checkbox.pack(padx=10, pady=5, anchor="w")

	triggerbot_team_check_var = ctk.BooleanVar(value=triggerbot_team_check)
	triggerbot_team_check_checkbox = ctk.CTkCheckBox(master=tab_triggerbot, text="Enable Team Check", variable=triggerbot_team_check_var,
													command=lambda: checkbox_action('triggerbot_team_check', triggerbot_team_check_var))
	triggerbot_team_check_checkbox.pack(padx=10, pady=5, anchor="w")

	global triggerbot_key_var
	triggerbot_key_var = StringVar(value=f"Trigger Key: {triggerbot_key}")
	triggerbot_key_button = ctk.CTkButton(master=tab_triggerbot, textvariable=triggerbot_key_var, width=200, command=start_recording_key)
	triggerbot_key_button.pack(padx=10, pady=5, anchor="w")

	# Misc Tab
	tab_misc = tabview.add("Misc")

	anti_flashbang_var = ctk.BooleanVar(value=anti_flashbang)
	anti_flashbang_checkbox = ctk.CTkCheckBox(master=tab_misc, text="Enable Anti Flashbang", variable=anti_flashbang_var,
											  command=lambda: checkbox_action('anti_flashbang', anti_flashbang_var))
	anti_flashbang_checkbox.pack(padx=10, pady=5, anchor="w")

	enable_bhop_var = ctk.BooleanVar(value=enable_bhop)
	enable_bhop_checkbox = ctk.CTkCheckBox(master=tab_misc, text="Enable Bhop", variable=enable_bhop_var,
										command=lambda: checkbox_action('enable_bhop', enable_bhop_var))
	enable_bhop_checkbox.pack(padx=10, pady=5, anchor="w")

	fov_changer_var = ctk.BooleanVar(value=fov_changer_option)
	fov_changer_checkbox = ctk.CTkCheckBox(master=tab_misc, text="Enable FOV Changer", variable=fov_changer_var,
										  command=lambda: checkbox_action('fov_changer_option', fov_changer_var))
	fov_changer_checkbox.pack(padx=10, pady=5, anchor="w")

	fov_slider = ctk.CTkSlider(master=tab_misc, from_=30, to=170, number_of_steps=141, command=fov_slider_action)
	fov_slider.pack(side="left", padx=(0, 10), pady=5) 

	fov_value_label = ctk.CTkLabel(master=tab_misc,text=f"FOV: {int(fov_slider.get())}")
	fov_value_label.pack(side="left", padx=(10, 0), pady=5)

	root.resizable(False, False)
	root.title("cs2py")
	root.protocol("WM_DELETE_WINDOW", on_closing)
	root.mainloop()

if __name__ == "__main__":
	print("          ____              \n  ___ ___|___ \\ _ __  _   _ \n / __/ __| __) | '_ \\| | | |\n| (__\\__ \\/ __/| |_) | |_| |\n \\___|___/_____| .__/ \\__, |\n               |_|    |___/ \n\n             - By GsDeluxe")
	main()
