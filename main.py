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
from pynput.mouse import Controller, Button, Listener

import customtkinter as ctk
from tkinter import BooleanVar, StringVar
from CTkColorPicker import AskColor
import webbrowser
from  pypresence import Presence

from ext_types import * 
from memfuncs import memfunc


# Load Windows DLLs
user32 = ctypes.WinDLL('user32.dll')
kernel32 = ctypes.WinDLL('kernel32')
kernel32.ReadProcessMemory.argtypes = [ctypes.wintypes.HANDLE,ctypes.wintypes.LPCVOID,ctypes.wintypes.LPVOID,ctypes.wintypes.SIZE,ctypes.POINTER(ctypes.wintypes.SIZE)]
kernel32.ReadProcessMemory.restype = ctypes.wintypes.BOOL

# Bone indices mapping
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

# ESP settings
team_check: bool = False
skeleton_rendering: bool = True
box_rendering: bool = True
tracer_rendering: bool = True
name_rendering: bool = True
health_bar_rendering: bool = True
health_text_rendering: bool = True

# ESP colors
t_color: str = "#8A2BE2"
ct_color: str = "#39FF14"

# Triggerbot settings
mouse = Controller()
enable_triggerbot: bool = False
enable_triggerbot_keycheck: bool = True
triggerbot_key: str = "shift"
triggerbot_team_check: bool = False

# Misc settings
anti_flashbang: bool = False
enable_bhop: bool = False
player_fov: int = 105
fov_changer_option: bool = False
enable_bomb_timer: bool = False
bomb_time_left: int = -1
bombPlanted: bool = False
discord_presence_enabled: bool = True

# Aimbot settings
enable_aimbot: bool = False
aimbot_team_check: bool = True
visibility_check: bool = False
enable_aimbot_fov: bool = False
aimbot_fov: float = 400
aimbot_smoothness: int = 0
aim_position = bones["head"]

# Screen dimensions
SCREEN_WIDTH = user32.GetSystemMetrics(0)
SCREEN_HEIGHT = user32.GetSystemMetrics(1)

def world_to_screen(view_matrix: Matrix, position: Vector3):
    """Convert 3D world coordinates to 2D screen coordinates"""
    try:
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
        
        width_float = float(SCREEN_WIDTH)
        height_float = float(SCREEN_HEIGHT)
        
        x = width_float / 2.0
        y = height_float / 2.0
        
        x += 0.5 * screen_x * width_float + 0.5
        y -= 0.5 * screen_y * height_float + 0.5
        
        return x, y
        
    except Exception as e:
        print(f"Error in world_to_screen: {e}")
        return -1.0, -1.0

def calculate_angles(from_: Vector3, to: Vector3) -> Vector2:
    """Calculate yaw and pitch angles between two 3D points"""
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
    """Get information about all entities in the game"""
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
    """Get game offsets"""
    oc = offsets.Client()
    offsets_obj = Offset(
        dwViewMatrix=oc.offset("dwViewMatrix"),
        dwLocalPlayerPawn=oc.offset("dwLocalPlayerPawn"),
        dwEntityList=oc.offset("dwEntityList"),
        dwLocalPlayerController=oc.offset("dwLocalPlayerController"),
        dwViewAngles = oc.offset("dwViewAngles"),
        dwGameRules = oc.offset("dwGameRules"),

        ButtonJump=oc.button("jump"),
        
        m_hPlayerPawn=oc.get("CCSPlayerController", "m_hPlayerPawn"),
        m_iHealth=oc.get("C_BaseEntity", "m_iHealth"),
        m_lifeState=oc.get("C_BaseEntity", "m_lifeState"),
        m_iTeamNum=oc.get("C_BaseEntity", "m_iTeamNum"),
        m_vOldOrigin=oc.get("C_BasePlayerPawn", "m_vOldOrigin"),
        m_pGameSceneNode=oc.get("C_BaseEntity", "m_pGameSceneNode"),
        m_modelState=oc.get("CSkeletonInstance", "m_modelState"),
        m_boneArray=128,
        m_nodeToWorld=oc.get("CGameSceneNode", "m_nodeToWorld"),
        m_sSanitizedPlayerName=oc.get("CCSPlayerController", "m_sSanitizedPlayerName"),
        m_iIDEntIndex=oc.get("C_CSPlayerPawnBase", "m_iIDEntIndex"),
        m_flFlashMaxAlpha=oc.get("C_CSPlayerPawnBase", "m_flFlashMaxAlpha"),
        m_fFlags=oc.get("C_BaseEntity", "m_fFlags"),
        m_iFOV=oc.get("CCSPlayerBase_CameraServices", "m_iFOV"),
        m_pCameraServices=oc.get("C_BasePlayerPawn", "m_pCameraServices"),
        m_bIsScoped=oc.get("C_CSPlayerPawn", "m_bIsScoped"),
        m_vecViewOffset = oc.get("C_BaseModelEntity", "m_vecViewOffset"),
        m_entitySpottedState = oc.get("C_CSPlayerPawn", "m_entitySpottedState"),
        m_bSpotted = oc.get("EntitySpottedState_t", "m_bSpotted"),
        m_bBombPlanted = oc.get("C_CSGameRules", "m_bBombPlanted"),

    )

    return offsets_obj

def draw_box(pme, rect_left, rect_top, rect_width, rect_height, team):
    """Draw ESP box"""
    pme.draw_rectangle_lines(rect_left, rect_top, rect_width, rect_height, color=pme.get_color(t_color if team == 2 else ct_color), lineThick=1.0)

def draw_name(pme, player_name, text_x, text_y):
    """Draw player name"""
    if player_name:
        pme.draw_text(player_name, text_x, text_y, fontSize=15.0, color=pme.get_color("#ffffff"))

def draw_health_bar(pme, health, rect_left, rect_top, rect_height):
    """Draw health bar"""
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
    """Draw health text"""
    if health > 0:
        health_bar_width = 5
        health_bar_x = rect_left - health_bar_width - 5
        # Draw health number
        health_text = str(health)
        text_x = health_bar_x + health_bar_width / 2
        text_y = rect_top + rect_height + 5
        pme.draw_text(health_text, text_x, text_y, fontSize=20.0, color=pme.get_color("#ffffff"))

def draw_tracer(pme, start_pos_x, start_pos_y, rect_center_x, rect_center_y, team):
    """Draw tracer line"""
    if rect_center_y != -1:
        pme.draw_line(start_pos_x, start_pos_y, rect_center_x, rect_center_y, color=pme.get_color(t_color if team == 2 else ct_color), thick=2.0)

def draw_bones(pme, bones, bone_connections, team):
    """Draw skeleton bones"""
    for start_bone, end_bone in bone_connections:
        if start_bone in bones and end_bone in bones:
            pme.draw_line(bones[start_bone].x, bones[start_bone].y, bones[end_bone].x, bones[end_bone].y, color=pme.get_color(t_color if team == 2 else ct_color), thick=2.0)

def triggerbot_thread(memf, client, offsets):
    """Triggerbot functionality"""
    while True:
        try:
            if not GetWindowText(GetForegroundWindow()) == "Counter-Strike 2" or enable_triggerbot == False:
                time.sleep(0.1)
                continue

            if keyboard.is_pressed(triggerbot_key) or enable_triggerbot_keycheck == False:
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
    """Anti-flash functionality"""
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
    """Bunny hop functionality"""
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
    """FOV changer functionality"""
    while True:
        try:
            local_player_p = memf.ReadPointer(client, offsets.dwLocalPlayerPawn)
            camera_services = memf.ReadPointer(local_player_p, offsets.m_pCameraServices)
            current_fov = memf.ReadInt(camera_services, offsets.m_iFOV)
            is_scoped = memf.ReadBool(local_player_p, offsets.m_bIsScoped)

            if fov_changer_option:
                if not is_scoped and current_fov != player_fov:
                    memf.WriteInt(camera_services, player_fov, offsets.m_iFOV)
            else:
                if current_fov != 105:
                    memf.WriteInt(camera_services, 105, offsets.m_iFOV)
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            pass

def check_in_game(memf, client, offsets):
    """Check if game is running"""
    game_not_in_memory = True
    while True:
        try:
            get_entities_info(memf, client, SCREEN_WIDTH, SCREEN_HEIGHT, offsets, False)
            if game_not_in_memory:
                print("[+] Game is in memory, proceeding...")
            break
        except pymem.exception.MemoryReadError as e:
            if game_not_in_memory:
                print("[*] Game not in memory. Waiting...")
                game_not_in_memory = False 
            time.sleep(1) 

def bomb_timer_thread(memf: memfunc, client, offsets: Offset):
    """Bomb timer functionality"""
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
    """Aimbot functionality"""
    def lerp(start, end, t): return start + (end - start) * t
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
            entity_list = memf.ReadPointer(client, offsets.dwEntityList)

            localPlayer.pawnAddress = memf.ReadPointer(client, offsets.dwLocalPlayerPawn)
        except:
            localPlayer.Team = memf.ReadInt(localPlayer.pawnAddress, offsets.m_iTeamNum)
            localPlayer.origin = memf.ReadVec(localPlayer.pawnAddress, offsets.m_vOldOrigin)
            localPlayer.view = memf.ReadVec(localPlayer.pawnAddress, offsets.m_vecViewOffset)
            localPlayer.HeadPos = None
            localPlayer.head2d = None

            for i in range(64): 
                ListEntry = memf.ReadPointer(entity_list, (8 * (i & 0x7FFF) >> 9) + 16)

                if not ListEntry: continue

                currentController = memf.ReadPointer(ListEntry, 120 * (i & 0x1FF))
                if not currentController: continue

                pawnHandle = memf.ReadInt(currentController, offsets.m_hPlayerPawn)
                if not pawnHandle: continue

                listEntry2 = memf.ReadPointer(entity_list, (0x8 * ((pawnHandle & 0x7FFF) >> 9) + 16))
                
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

                if aimbot_team_check and localPlayer.Team == team:
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
                mat = Matrix([
                    [view_matrix_flat[0], view_matrix_flat[1], view_matrix_flat[2], view_matrix_flat[3]],
                    [view_matrix_flat[4], view_matrix_flat[5], view_matrix_flat[6], view_matrix_flat[7]], 
                    [view_matrix_flat[8], view_matrix_flat[9], view_matrix_flat[10], view_matrix_flat[11]],
                    [view_matrix_flat[12], view_matrix_flat[13], view_matrix_flat[14], view_matrix_flat[15]]
                ]).matrix

                w2sx, w2sy = world_to_screen(mat, temp_entity.head)
                temp_entity.head2d = Vector2(w2sx, w2sy)

                temp_entity.pixelDistance = distance_vec2(temp_entity.head2d, Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
                entities.append(temp_entity)

            entities = sorted(entities, key=lambda o: o.distance)

            # Check if aimbot should be activated
            if len(entities) > 0 and user32.GetAsyncKeyState(0x06) & 0x8000 and enable_aimbot:
                # Calculate screen coordinates from world coordinates using view matrix
                screen_x = (mat[0][0] * x + mat[0][1] * y + mat[0][2] * z + mat[0][3])
                screen_y = (mat[1][0] * x + mat[1][1] * y + mat[1][2] * z + mat[1][3])
                w = (mat[3][0] * x + mat[3][1] * y + mat[3][2] * z + mat[3][3])
                
                # Check if point is behind camera
                if w < 0.01:
                    return -1.0, -1.0
                
                # Perform perspective divide
                invw = 1.0 / w
                screen_x *= invw 
                screen_y *= invw
                
                # Convert normalized coordinates to screen space
                width_float = float(SCREEN_WIDTH)
                height_float = float(SCREEN_HEIGHT)
                
                # Calculate screen center
                x = width_float / 2.0
                y = height_float / 2.0
                
                # Apply screen transform
                x += 0.5 * screen_x * width_float + 0.5
                y -= 0.5 * screen_y * height_float + 0.5
                
                return x, y

# Calculate aim angles between two 3D points
def calculate_angles(from_: Vector3, to: Vector3) -> Vector2:
    deltaX = to.x - from_.x
    deltaY = to.y - from_.y
    deltaZ = to.z - from_.z

    # Calculate yaw angle in degrees
    yaw = math.atan2(deltaY, deltaX) * 180 / math.pi
    
    # Calculate pitch angle in degrees using distance in XY plane
    distance = math.sqrt(deltaX * deltaX + deltaY * deltaY)
    pitch = -(math.atan2(deltaZ, distance) * 180 / math.pi)

    return Vector2(yaw, pitch)

# Get information about all valid entities in the game
def get_entities_info(mem: memfunc, client_dll: int, screen_width: int, screen_height: int, offsets: Offset, team_check: bool) -> List[Entity]:
    entities = []

    # Get entity list pointer
    entity_list = mem.ReadPointer(client_dll, offsets.dwEntityList)
    if not entity_list:
        return entities

    # Get local player info
    local_player_p = mem.ReadPointer(client_dll, offsets.dwLocalPlayerPawn)
    if not local_player_p:
        return entities

    local_player_game_scene = mem.ReadPointer(local_player_p, offsets.m_pGameSceneNode)
    if not local_player_game_scene:
        return entities

    local_player_scene_origin = mem.ReadVec(local_player_game_scene, offsets.m_nodeToWorld)

    # Get view matrix for world to screen calculations
    view_matrix_flat = mem.ReadMatrix(client_dll + offsets.dwViewMatrix)
    view_matrix = Matrix([
        [view_matrix_flat[0], view_matrix_flat[1], view_matrix_flat[2], view_matrix_flat[3]],
        [view_matrix_flat[4], view_matrix_flat[5], view_matrix_flat[6], view_matrix_flat[7]],
        [view_matrix_flat[8], view_matrix_flat[9], view_matrix_flat[10], view_matrix_flat[11]],
        [view_matrix_flat[12], view_matrix_flat[13], view_matrix_flat[14], view_matrix_flat[15]]])

    # Iterate through possible entity slots
    for i in range(64):
        # Initialize empty entity
        temp_entity = Entity(
            Health=0, Team=0, Name="",
            Position=Vector2(0, 0), Bones={},
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

        # Entity validation chain
        list_entry = mem.ReadPointer(entity_list, (8 * (i & 0x7FFF) >> 9) + 16)
        if not list_entry:
            continue

        entity_controller = mem.ReadPointer(list_entry, 120 * (i & 0x1FF))
        if not entity_controller:
            continue

        entity_controller_pawn = mem.ReadPointer(entity_controller, offsets.m_hPlayerPawn)
        if not entity_controller_pawn:
            continue

        list_entry = mem.ReadPointer(entity_list, (0x8 * ((entity_controller_pawn & 0x7FFF) >> 9) + 16))
        if not list_entry:
            continue

        entity_pawn = mem.ReadPointer(list_entry, 120 * (entity_controller_pawn & 0x1FF))
        if not entity_pawn or entity_pawn == local_player_p:
            continue

        # Check entity state and properties
        entity_life_state = mem.ReadInt(entity_pawn, offsets.m_lifeState)
        if entity_life_state != 256:
            continue

        entity_team = mem.ReadInt(entity_pawn, offsets.m_iTeamNum)
        if entity_team == 0:
            continue

        if team_check:
            local_team = mem.ReadInt(local_player_p, offsets.m_iTeamNum)
            if local_team == entity_team:
                continue

        entity_health = mem.ReadInt(entity_pawn, offsets.m_iHealth)
        if entity_health < 1 or entity_health > 100:
            continue

        # Get entity name
        entity_name_address = mem.ReadPointer(entity_controller, offsets.m_sSanitizedPlayerName)
        if not entity_name_address:
            continue

        entity_name = mem.ReadString(entity_name_address, 64)
        if not entity_name:
            continue

        sanitized_name = ''.join(c for c in entity_name if c.isalnum() or c in ' .,!')

        # Get bone data
        game_scene = mem.ReadPointer(entity_pawn, offsets.m_pGameSceneNode)
        if not game_scene:
            continue

        entity_bone_array = mem.ReadPointer(game_scene, offsets.m_modelState + offsets.m_boneArray)
        if not entity_bone_array:
            continue

        entity_origin = mem.ReadVec(entity_pawn, offsets.m_vOldOrigin)
        if not entity_origin:
            continue

        # Process bones and calculate screen positions
        for bone_name, bone_index in bones.items():
            current_bone = mem.ReadVec(entity_bone_array, bone_index * 32)
            if bone_name == "head":
                entity_head = current_bone

            bone_x, bone_y = world_to_screen(view_matrix, current_bone)
            entity_bones[bone_name] = Vector2(bone_x, bone_y)

        # Calculate box dimensions
        entity_head_top = Vector3(entity_head.x, entity_head.y, entity_head.z + 7)
        entity_head_bottom = Vector3(entity_head.x, entity_head.y, entity_head.z - 5)
        screen_pos_head_x, screen_pos_head_top_y = world_to_screen(view_matrix, entity_head_top)
        _, screen_pos_head_bottom_y = world_to_screen(view_matrix, entity_head_bottom)
        screen_pos_feet_x, screen_pos_feet_y = world_to_screen(view_matrix, entity_origin)
        entity_box_top = Vector3(entity_origin.x, entity_origin.y, entity_origin.z + 70)
        _, screen_pos_box_top = world_to_screen(view_matrix, entity_box_top)

        # Check if entity is on screen
        OnScreen = not (screen_pos_head_x <= -1 or screen_pos_feet_y <= -1 or 
                       screen_pos_head_x >= screen_width or screen_pos_head_top_y >= screen_height)

        box_height = screen_pos_feet_y - screen_pos_box_top

        # Populate entity data
        temp_entity.Health = entity_health
        temp_entity.Team = entity_team
        temp_entity.Name = sanitized_name
        temp_entity.Distance = distance_vec3(entity_origin, local_player_scene_origin)
        temp_entity.Position = Vector2(screen_pos_feet_x, screen_pos_feet_y)
        temp_entity.Bones = entity_bones
        temp_entity.HeadPos = Vector3(screen_pos_head_x, screen_pos_head_top_y, screen_pos_head_bottom_y)
        temp_entity.Rect = Rectangle(screen_pos_box_top, screen_pos_feet_x - box_height / 4, 
                                   screen_pos_feet_x + box_height / 4, screen_pos_feet_y)
        temp_entity.OnScreen = OnScreen

        entities.append(temp_entity)

    return entities

# Get game offsets from offset class
def get_offsets() -> Offset:
    oc = offsets.Client()
    offsets_obj = Offset(
        dwViewMatrix=oc.offset("dwViewMatrix"),
        dwLocalPlayerPawn=oc.offset("dwLocalPlayerPawn"),
        dwEntityList=oc.offset("dwEntityList"),
        dwLocalPlayerController=oc.offset("dwLocalPlayerController"),
        dwViewAngles = oc.offset("dwViewAngles"),
        dwGameRules = oc.offset("dwGameRules"),

        ButtonJump=oc.button("jump"),
        
        m_hPlayerPawn=oc.get("CCSPlayerController", "m_hPlayerPawn"),
        m_iHealth=oc.get("C_BaseEntity", "m_iHealth"),
        m_lifeState=oc.get("C_BaseEntity", "m_lifeState"),
        m_iTeamNum=oc.get("C_BaseEntity", "m_iTeamNum"),
        m_vOldOrigin=oc.get("C_BasePlayerPawn", "m_vOldOrigin"),
        m_pGameSceneNode=oc.get("C_BaseEntity", "m_pGameSceneNode"),
        m_modelState=oc.get("CSkeletonInstance", "m_modelState"),
        m_boneArray=128,
        m_nodeToWorld=oc.get("CGameSceneNode", "m_nodeToWorld"),
        m_sSanitizedPlayerName=oc.get("CCSPlayerController", "m_sSanitizedPlayerName"),
        m_iIDEntIndex=oc.get("C_CSPlayerPawnBase", "m_iIDEntIndex"),
        m_flFlashMaxAlpha=oc.get("C_CSPlayerPawnBase", "m_flFlashMaxAlpha"),
        m_fFlags=oc.get("C_BaseEntity", "m_fFlags"),
        m_iFOV=oc.get("CCSPlayerBase_CameraServices", "m_iFOV"),
        m_pCameraServices=oc.get("C_BasePlayerPawn", "m_pCameraServices"),
        m_bIsScoped=oc.get("C_CSPlayerPawn", "m_bIsScoped"),
        m_vecViewOffset = oc.get("C_BaseModelEntity", "m_vecViewOffset"),
        m_entitySpottedState = oc.get("C_CSPlayerPawn", "m_entitySpottedState"),
        m_bSpotted = oc.get("EntitySpottedState_t", "m_bSpotted"),
        m_bBombPlanted = oc.get("C_CSGameRules", "m_bBombPlanted"),
    )

    return offsets_obj

# Drawing functions for ESP features
def draw_box(pme, rect_left, rect_top, rect_width, rect_height, team):
    color = t_color if team == 2 else ct_color
    pme.draw_rectangle_lines(rect_left, rect_top, rect_width, rect_height, 
                           color=pme.get_color(color), lineThick=1.0)

def draw_name(pme, player_name, text_x, text_y):
    if player_name:
        pme.draw_text(player_name, text_x, text_y, fontSize=15.0, 
                     color=pme.get_color("#ffffff"))

def draw_health_bar(pme, health, rect_left, rect_top, rect_height):
    if health <= 0:
        return
        
    # Health bar dimensions
    bar_width = 5
    bar_height = rect_height
    bar_x = rect_left - bar_width - 5
    bar_y = rect_top
    
    # Calculate filled portion
    health_percentage = min(1.0, health / 100.0)
    filled_height = bar_height * health_percentage

    # Draw filled bar and border
    pme.draw_rectangle(bar_x, bar_y + (bar_height - filled_height), 
                      bar_width, filled_height, color=pme.get_color("#ff0000"))
    pme.draw_rectangle_lines(bar_x, bar_y, bar_width, bar_height,
                           color=pme.get_color("#ffffff"), lineThick=1.0)
        
def draw_health_text(pme, health, rect_left, rect_top, rect_height):
    if health <= 0:
        return
        
    bar_width = 5
    bar_x = rect_left - bar_width - 5
    
    # Position text below health bar
    text_x = bar_x + bar_width / 2
    text_y = rect_top + rect_height + 5
    pme.draw_text(str(health), text_x, text_y, fontSize=20.0, 
                 color=pme.get_color("#ffffff"))

def draw_tracer(pme, start_pos_x, start_pos_y, rect_center_x, rect_center_y, team):
    if rect_center_y != -1:
        color = t_color if team == 2 else ct_color
        pme.draw_line(start_pos_x, start_pos_y, rect_center_x, rect_center_y, 
                     color=pme.get_color(color), thick=2.0)

def draw_bones(pme, bones, bone_connections, team):
    color = t_color if team == 2 else ct_color
    for start_bone, end_bone in bone_connections:
        if start_bone in bones and end_bone in bones:
            pme.draw_line(bones[start_bone].x, bones[start_bone].y,
                         bones[end_bone].x, bones[end_bone].y,
                         color=pme.get_color(color), thick=2.0)

# Game feature threads
def triggerbot_thread(memf, client, offsets):
    while True:
        try:
            # Skip if not in CS2 or triggerbot disabled
            if not GetWindowText(GetForegroundWindow()) == "Counter-Strike 2" or not enable_triggerbot:
                time.sleep(0.1)
                continue

            if keyboard.is_pressed(triggerbot_key) or not enable_triggerbot_keycheck:
                player = memf.ReadPointer(client, offsets.dwLocalPlayerPawn)
                entityId = memf.ReadInt(player, offsets.m_iIDEntIndex)

                if entityId > 0:
                    # Get entity info
                    entList = memf.ReadPointer(client, offsets.dwEntityList)
                    entEntry = memf.ReadPointer(entList, 0x8 * (entityId >> 9) + 0x10)
                    entity = memf.ReadPointer(entEntry, 120 * (entityId & 0x1FF))

                    entityTeam = memf.ReadInt(entity, offsets.m_iTeamNum)
                    playerTeam = memf.ReadInt(player, offsets.m_iTeamNum)

                    # Check team and fire
                    if not triggerbot_team_check or entityTeam != playerTeam:
                        entityHp = memf.ReadInt(entity, offsets.m_iHealth)
                        if entityHp > 0 and not user32.GetAsyncKeyState(0x01) < 0:
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
            # Get local player
            entity_list = memf.ReadPointer(client, offsets.dwEntityList)
            local_player = memf.ReadPointer(client, offsets.dwLocalPlayerController)
            local_pawn = memf.ReadInt(local_player, offsets.m_hPlayerPawn)
            list_entry2 = memf.ReadPointer(entity_list, 0x8 * ((local_pawn & 0x7FFF) >> 9) + 16)
            local_player = memf.ReadPointer(list_entry2, 120 * (local_pawn & 0x1FF))

            if local_player and enable_bhop:
                flags = memf.ReadInt(local_player, offsets.m_fFlags)
                # Check space key and ground flag
                if user32.GetAsyncKeyState(0x20) and flags & (1 << 0):
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
                if not is_scoped and current_fov != player_fov:
                    memf.WriteInt(camera_services, player_fov, offsets.m_iFOV)
            else:
                if current_fov != 105:
                    memf.WriteInt(camera_services, 105, offsets.m_iFOV)
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            pass

def check_in_game(memf, client, offsets):
    game_not_in_memory = True
    while True:
        try:
            get_entities_info(memf, client, SCREEN_WIDTH, SCREEN_HEIGHT, offsets, False)
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
                # Count down from 40 seconds
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
    def lerp(start, end, t): 
        return start + (end - start) * t

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
            entity_list = memf.ReadPointer(client, offsets.dwEntityList)

            # Get local player info
            localPlayer.pawnAddress = memf.ReadPointer(client, offsets.dwLocalPlayerPawn)
            localPlayer.Team = memf.ReadInt(localPlayer.pawnAddress, offsets.m_iTeamNum)
            localPlayer.origin = memf.ReadVec(localPlayer.pawnAddress, offsets.m_vOldOrigin)
            localPlayer.view = memf.ReadVec(localPlayer.pawnAddress, offsets.m_vecViewOffset)
            localPlayer.HeadPos = None
            localPlayer.head2d = None

            # Loop through entities
            for i in range(64):
                ListEntry = memf.ReadPointer(entity_list, (8 * (i & 0x7FFF) >> 9) + 16)
                if not ListEntry: continue

                currentController = memf.ReadPointer(ListEntry, 120 * (i & 0x1FF))
                if not currentController: continue

                pawnHandle = memf.ReadInt(currentController, offsets.m_hPlayerPawn)
                if not pawnHandle: continue

                listEntry2 = memf.ReadPointer(entity_list, (0x8 * ((pawnHandle & 0x7FFF) >> 9) + 16))
                
                currentPawn = memf.ReadPointer(listEntry2, 0x78 * (pawnHandle & 0x1FF))
                if not currentPawn or currentPawn == localPlayer.pawnAddress: continue

                # Get entity info
                sceneNode = memf.ReadPointer(currentPawn, offsets.m_pGameSceneNode)
                boneMatrix = memf.ReadPointer(sceneNode, offsets.m_modelState + 0x80)

                health = memf.ReadInt(currentPawn, offsets.m_iHealth)
                team = memf.ReadInt(currentPawn, offsets.m_iTeamNum)
                lifestate = memf.ReadUInt(currentPawn, offsets.m_lifeState)
                spotted = memf.ReadBool(currentPawn, offsets.m_entitySpottedState + offsets.m_bSpotted)

                # Skip if not visible or dead
                if visibility_check and not spotted:
                    continue

                if lifestate != 256:
                    continue

                if aimbot_team_check and localPlayer.Team == team:
                    continue

                # Create entity object
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

                # Set entity properties
                temp_entity.pawnAddress = currentPawn
                temp_entity.controllerAddress = currentController
                temp_entity.health = health
                temp_entity.lifestate = lifestate
                temp_entity.team = team
                temp_entity.origin = memf.ReadVec(currentPawn, offsets.m_vOldOrigin)
                temp_entity.view = memf.ReadVec(currentPawn, offsets.m_vecViewOffset)
                temp_entity.distance = distance_vec3(temp_entity.origin, localPlayer.origin)
                temp_entity.head = memf.ReadVec(boneMatrix, aim_position * 32)

                # World to screen conversion
                view_matrix_flat = memf.ReadMatrix(client + offsets.dwViewMatrix)
                mat = Matrix([
                    [view_matrix_flat[0], view_matrix_flat[1], view_matrix_flat[2], view_matrix_flat[3]],
                    [view_matrix_flat[4], view_matrix_flat[5], view_matrix_flat[6], view_matrix_flat[7]],
                    [view_matrix_flat[8], view_matrix_flat[9], view_matrix_flat[10], view_matrix_flat[11]],
                    [view_matrix_flat[12], view_matrix_flat[13], view_matrix_flat[14], view_matrix_flat[15]]
                ]).matrix

                w2sx, w2sy = world_to_screen(mat, temp_entity.head)
                temp_entity.head2d = Vector2(w2sx, w2sy)

                temp_entity.pixelDistance = distance_vec2(temp_entity.head2d, 
                                                        Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
                entities.append(temp_entity)

            # Sort by distance
            entities = sorted(entities, key=lambda o: o.distance)

            # Aimbot logic
            if len(entities) > 0 and user32.GetAsyncKeyState(0x06) & 0x8000 and enable_aimbot:
                playerView = Vector3.__add__(localPlayer.origin, localPlayer.view)

                if entities[0].pixelDistance < aimbot_fov or not enable_aimbot_fov:
                    newAngles = calculate_angles(playerView, entities[0].head)
                    target_angles = Vector3(newAngles.y, newAngles.x, 0.0)

                    if aimbot_smoothness > 0:
                        current_angles = memf.ReadVec(client, offsets.dwViewAngles)
                        smoothed_angles = lerp(current_angles, target_angles, aimbot_smoothness / 20.0)
                        memf.WriteVec(client, smoothed_angles, offsets.dwViewAngles)
                    else:
                        memf.WriteVec(client, target_angles, offsets.dwViewAngles)

        except Exception as e:
            print(f"Error in aimbot thread: {e}")
            time.sleep(0.1)
            continue

def discord_rpc_thread():
    presence = Presence(1277586728517107744)
    presence.connect()
    presence_active = False
    
    while True:
        if discord_presence_enabled:
            if not presence_active:
                try:
                    presence.update(
                        state="github.com/GsDeluxe/cs2py",
                        details="FREE CS2 CHEAT",
                        start=int(time.time()),
                        large_image="cs2py",
                        large_text="cs2py", 
                        small_image="github",
                        small_text="GsDeluxe on GitHub",
                        buttons=[{'label': 'GitHub', 'url': 'https://github.com/GsDeluxe/cs2py'}]
                    )
                except Exception as e:
                    print(f"Discord RPC error: {e}")
                    time.sleep(1)
                    continue
            presence_active = True
            time.sleep(1)

def main():
    try:
        pm = pymem.Pymem("cs2.exe")
    except:
        print("[-] Error CS2 Process Not Found")
        os._exit(0)
    
    client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
    memf = memfunc(proc=pm)
    
    print("[*] Getting Offsets")
    offsets = get_offsets()

    # Start threads
    threading.Thread(target=GUI, daemon=True).start()
    threading.Thread(target=discord_rpc_thread, daemon=True).start()
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

    # Initialize overlay
    pme.overlay_init(title="cs2py")
    fps = pme.get_monitor_refresh_rate()
    pme.set_fps(fps)
    pme.gui_fade(0.9)
    width, height = pme.get_screen_width(), pme.get_screen_height()

    # Define bone connections for skeleton ESP
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

    # Main render loop
    while pme.overlay_loop():
        try:
            pme.begin_drawing()

            if GetWindowText(GetForegroundWindow()) == "Counter-Strike 2":
                try:
                    entities = get_entities_info(mem=memf, client_dll=client, 
                                              screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT,
                                              offsets=offsets, team_check=team_check)
                except pymem.exception.MemoryReadError:
                    print("[-] Error Reading Game")
                    check_in_game(memf, client, offsets)
                    continue

                # Draw ESP for each entity
                for entity in entities:
                    if entity.Distance < 35:
                        continue

                    # Calculate rectangle dimensions
                    rect_left = entity.Rect.Left
                    rect_top = entity.Rect.Top
                    rect_width = entity.Rect.Right - entity.Rect.Left
                    rect_height = entity.Rect.Bottom - entity.Rect.Top
                    rect_center_x = rect_left + rect_width / 2
                    rect_center_y = rect_top + rect_height / 2
                    start_pos_x, start_pos_y = width / 2, height

                    # Draw ESP features if entity is on screen
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

                    # Draw aimbot FOV circle
                    if enable_aimbot_fov:
                        pme.draw_circle_lines(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, 
                                            aimbot_fov, pme.get_color("#ffffff"))

                    # Draw bomb timer
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
                        y_position = SCREEN_HEIGHT // 2 + y_offset
                        
                        # Draw bomb timer background and text
                        pme.draw_rectangle(10, y_position, background_width, background_height, 
                                         background_color)
                        pme.draw_text(bomb_text, 20, y_position + 10, fontSize=font_size, 
                                    color=text_color)

            pme.end_drawing()
        except Exception as e:
            print(f"Error in render loop: {e}")
            time.sleep(0.1)
            continue

def GUI():
    # Main window close handler
    def on_closing():
        os._exit(0)

    # Color picker handlers for team colors
    def pick_team_color(is_terrorist):
        color = AskColor().get()
        if color:
            global t_color, ct_color
            if is_terrorist:
                t_color = color
                update_color_display(t_color_display, color)
            else:
                ct_color = color 
                update_color_display(ct_color_display, color)

    # Updates color preview canvas
    def update_color_display(canvas, color):
        canvas.delete("all")
        canvas.create_rectangle(0, 0, canvas.winfo_width(), canvas.winfo_height(), fill=color, outline=color)
        canvas.update()

    # Keyboard event handler for triggerbot key binding
    def on_key_event(event):
        global triggerbot_key
        if event.event_type == keyboard.KEY_DOWN:
            triggerbot_key = event.name
            triggerbot_key_var.set(f"Trigger Key: {triggerbot_key}")
            keyboard.unhook_all()
            
    def start_recording_key():
        triggerbot_key_var.set("Press a key...")
        keyboard.hook(on_key_event)

    # Slider value handlers
    def update_slider_value(value, target_var, label_obj, label_text):
        globals()[target_var] = int(value)
        label_obj.configure(text=f"{label_text}: {int(value)}")

    def update_aim_position(value):
        global aim_position
        aim_position = bones.get(value)

    # Generic checkbox handler
    def checkbox_action(var_name, var):
        globals()[var_name] = var.get()

    def open_url(url):
        webbrowser.open(url)

    # Creates a slider with label in consistent style
    def create_slider_with_label(parent, value, command, label_text, slider_from, slider_to, step):
        frame = ctk.CTkFrame(master=parent, corner_radius=8, bg_color="#2e2e2e")
        frame.pack(padx=10, pady=5, fill="x")

        def slider_callback(new_value):
            slider.set(new_value)
            command(new_value)

        slider = ctk.CTkSlider(
            master=frame, from_=slider_from, to=slider_to, command=slider_callback,
            bg_color="#2e2e2e", border_color="#444444", progress_color="#8A2BE2", 
            button_color="#8A2BE2", button_hover_color="#6912BF"
        )
        slider.set(value)
        slider.pack(side="left", fill="x", padx=(0, 10))

        value_label = ctk.CTkLabel(master=frame, text=f"{label_text}: {value:.1f}", 
                                 font=("Segoe UI", 12), text_color="#FFFFFF", width=120)
        value_label.pack(side="left", padx=(10, 0), anchor="w")

        return slider, value_label

    # Initialize main window
    root = ctk.CTk()
    root.title("cs2py")
    root.iconbitmap("cs2py.ico")
    root.attributes("-topmost", True, "-alpha", 0.96)
    root.resizable(False, False)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.configure(bg="#2e2e2e")
    
    # Create main container frame
    gradient_frame = ctk.CTkFrame(root, corner_radius=0, bg_color="#2e2e2e")
    gradient_frame.pack(padx=10, pady=10, expand=True, fill="both")
    
    # Initialize tab view
    tabview = ctk.CTkTabview(gradient_frame, segmented_button_selected_color="#8A2BE2", 
                            segmented_button_selected_hover_color="#8A2BE2")
    tabview.pack(padx=10, pady=10, expand=True, fill="both")

    # Create tabs
    tabs = {
        "ESP": tabview.add("ESP"),
        "Triggerbot": tabview.add("Triggerbot"), 
        "Aimbot": tabview.add("Aimbot"),
        "Misc": tabview.add("Misc")
    }

    # Helper function for consistent checkbox styling
    def create_checkbox_with_outline(parent, text, variable, command):
        frame = ctk.CTkFrame(master=parent, corner_radius=8, bg_color="#2e2e2e", 
                           border_color="#444444", border_width=2)
        frame.pack(padx=10, pady=5, anchor="w", fill="x")

        checkbox = ctk.CTkCheckBox(master=frame, text=text, variable=variable, 
                                 command=command, **neon_checkbox_style())
        checkbox.pack(padx=10, pady=5, anchor="w")

        return checkbox

    # Consistent checkbox styling
    def neon_checkbox_style():
        return {
            "font": ("Segoe UI", 12),
            "text_color": "#FFFFFF", 
            "fg_color": "#333333",
            "border_color": "#8A2BE2",
            "checkmark_color": "#8A2BE2",
            "hover_color": "#8A2BE2",
            "border_width": 2
        }

    # ESP Tab Checkboxes
    esp_checkboxes = {
        'skeleton_rendering': skeleton_rendering,
        'box_rendering': box_rendering,
        'tracer_rendering': tracer_rendering,
        'name_rendering': name_rendering,
        'health_bar_rendering': health_bar_rendering,
        'health_text_rendering': health_text_rendering,
        'team_check': team_check
    }

    for var_name, initial_value in esp_checkboxes.items():
        var = ctk.BooleanVar(value=initial_value)
        create_checkbox_with_outline(tabs["ESP"], var_name.replace('_', ' ').title(), 
                                   var, lambda v=var_name, var=var: checkbox_action(v, var))

    # Team color selection UI
    color_frame_width = 200

    def create_color_display_frame(parent, color):
        canvas = ctk.CTkCanvas(master=parent, width=30, height=30, highlightthickness=0, bg=color)
        update_color_display(canvas, color)
        return canvas

    # Create T and CT color selection frames
    for team_type, color, label in [("t", t_color, "Terrorist"), ("ct", ct_color, "Counter Terrorist")]:
        color_frame = ctk.CTkFrame(master=tabs["ESP"], corner_radius=8, bg_color="#2e2e2e", 
                                 border_color="#444444", border_width=2)
        color_frame.pack(padx=30, pady=10, anchor="w", fill="x")

        color_display = create_color_display_frame(color_frame, color)
        color_display.pack(side="left", padx=5, pady=5)

        if team_type == "t":
            t_color_display = color_display
        else:
            ct_color_display = color_display

        color_button = ctk.CTkButton(
            master=color_frame, 
            text=f"{label} Color",
            width=color_frame_width,
            fg_color="#6A0D91",
            hover_color="#8A2BE2",
            corner_radius=8,
            bg_color="#2e2e2e",
            font=("Segoe UI", 12),
            text_color="#FFFFFF",
            border_color="#8A2BE2",
            border_width=2,
            command=lambda t=team_type=="t": pick_team_color(t)
        )
        color_button.pack(side="left", padx=5, pady=5)

    # Triggerbot Tab
    triggerbot_checkboxes = {
        'enable_triggerbot': enable_triggerbot,
        'triggerbot_team_check': triggerbot_team_check,
        'enable_triggerbot_keycheck': enable_triggerbot_keycheck
    }

    for var_name, initial_value in triggerbot_checkboxes.items():
        var = ctk.BooleanVar(value=initial_value)
        create_checkbox_with_outline(tabs["Triggerbot"], var_name.replace('_', ' ').title(), 
                                   var, lambda v=var_name, var=var: checkbox_action(v, var))

    global triggerbot_key_var
    triggerbot_key_var = StringVar(value=f"Trigger Key: {triggerbot_key}")
    triggerbot_key_button = ctk.CTkButton(
        master=tabs["Triggerbot"],
        textvariable=triggerbot_key_var,
        width=200,
        fg_color="#6A0D91",
        hover_color="#8A2BE2",
        corner_radius=8,
        bg_color="#2e2e2e",
        font=("Segoe UI", 12),
        text_color="#FFFFFF",
        border_color="#8A2BE2",
        border_width=2,
        command=start_recording_key
    )
    triggerbot_key_button.pack(padx=10, pady=10)

    # Aimbot Tab
    aimbot_checkboxes = {
        'enable_aimbot': enable_aimbot,
        'enable_aimbot_fov': enable_aimbot_fov,
        'aimbot_team_check': aimbot_team_check,
        'visibility_check': False
    }

    for var_name, initial_value in aimbot_checkboxes.items():
        var = ctk.BooleanVar(value=initial_value)
        create_checkbox_with_outline(tabs["Aimbot"], var_name.replace('_', ' ').title(), 
                                   var, lambda v=var_name, var=var: checkbox_action(v, var))

    # Aimbot bone selection
    optionmenu_var = ctk.StringVar(value="head")
    optionmenu = ctk.CTkOptionMenu(
        tabs["Aimbot"],
        fg_color="#6A0D91",
        button_color="#8A2BE2",
        button_hover_color="#6912BF",
        dropdown_fg_color="#2e2e2e",
        dropdown_hover_color="#6912BF",
        dropdown_font=("Segoe UI", 12),
        dropdown_text_color="#ffffff",
        values=list(bones.keys()),
        variable=optionmenu_var,
        command=update_aim_position
    )
    optionmenu.pack(padx=10, pady=5, anchor="w", fill="x")

    # Aimbot sliders
    aimbot_fov_slider, aimbot_fov_value_label = create_slider_with_label(
        tabs["Aimbot"], aimbot_fov,
        lambda v: update_slider_value(v, 'aimbot_fov', aimbot_fov_value_label, "Aimbot FOV"),
        "Aimbot FOV", 0, 800, 1
    )
    
    smoothness_slider, smoothness_value_label = create_slider_with_label(
        tabs["Aimbot"], aimbot_smoothness,
        lambda v: update_slider_value(v, 'aimbot_smoothness', smoothness_value_label, "Smoothness"),
        "Smoothness", 0, 7, 1
    )

    # Misc Tab
    misc_checkboxes = {
        'anti_flashbang': anti_flashbang,
        'enable_bhop': enable_bhop,
        'enable_bomb_timer': enable_bomb_timer,
        'discord_presence_enabled': discord_presence_enabled,
        'fov_changer_option': fov_changer_option
    }

    for var_name, initial_value in misc_checkboxes.items():
        var = ctk.BooleanVar(value=initial_value)
        create_checkbox_with_outline(tabs["Misc"], var_name.replace('_', ' ').title(), 
                                   var, lambda v=var_name, var=var: checkbox_action(v, var))

    # FOV slider
    fov_slider, fov_value_label = create_slider_with_label(
        tabs["Misc"], player_fov,
        lambda v: update_slider_value(v, 'player_fov', fov_value_label, "FOV"),
        "FOV", 30, 170, 1
    )

    # Misc buttons
    button_style = {
        "width": 100,
        "fg_color": "#6A0D91",
        "hover_color": "#8A2BE2",
        "corner_radius": 8,
        "bg_color": "#2e2e2e",
        "font": ("Segoe UI", 11),
        "text_color": "#FFFFFF",
        "border_color": "#8A2BE2",
        "border_width": 2
    }

    github_button = ctk.CTkButton(
        master=tabs["Misc"],
        text="GitHub",
        command=lambda: open_url("https://github.com/GsDeluxe/cs2py"),
        **button_style
    )
    github_button.pack(side="left", padx=8, pady=10)

    # Placeholder buttons for future features
    for label in ["Soon", "Soon"]:
        button = ctk.CTkButton(master=tabs["Misc"], text=label, **button_style)
        button.pack(side="left", padx=8, pady=10)

    root.mainloop()

if __name__ == "__main__":
    print("          ____              \n  ___ ___|___ \\ _ __  _   _ \n / __/ __| __) | '_ \\| | | |\n| (__\\__ \\/ __/| |_) | |_| |\n \\___|___/_____| .__/ \\__, |\n               |_|    |___/ \n\n             - By GsDeluxe")
    main()
