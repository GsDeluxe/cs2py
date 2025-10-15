import logging
import pymem
from ext.datatypes import *
from functions import memfuncs, calculations, gameinput
import globals
import win32api, time

import serial

def is_valid_address(address):
	return address is not None and 0x10000 < address < 0x7FFFFFFFFFFF

def GetPlayers(processHandle, clientBaseAddress, LocalPlayer, AimBoneID, Options, Offsets):
	entities = []
	try:
		EntityList = memfuncs.ProcMemHandler.ReadPointer(processHandle, clientBaseAddress + Offsets.offset.dwEntityList)
	except Exception as e:
		return entities

	for i in range(64):
		try:
			tempEntity = Entity()

			ListEntry = memfuncs.ProcMemHandler.ReadPointer(processHandle, EntityList + (8 * (i & 0x7FFF) >> 9) + 16)
			if not is_valid_address(ListEntry):
				continue

			currentController = memfuncs.ProcMemHandler.ReadPointer(processHandle, ListEntry + 112 * (i & 0x1FF))
			if not is_valid_address(currentController):
				continue

			pawnHandle = memfuncs.ProcMemHandler.ReadInt(processHandle, currentController + Offsets.offset.m_hPlayerPawn)
			if pawnHandle == 0:
				continue

			ListEntry2 = memfuncs.ProcMemHandler.ReadPointer(processHandle, EntityList + 0x8 * ((pawnHandle & 0x7FFF) >> 9) + 0x10)
			if not is_valid_address(ListEntry2):
				continue

			currentPawn = memfuncs.ProcMemHandler.ReadPointer(processHandle, ListEntry2 + 0x70 * (pawnHandle & 0x1FF))
			if not is_valid_address(currentPawn) or currentPawn == LocalPlayer.pawnAddress:
				continue

			sceneNode = memfuncs.ProcMemHandler.ReadPointer(processHandle, currentPawn + Offsets.offset.m_pGameSceneNode)
			boneMatrix = memfuncs.ProcMemHandler.ReadPointer(processHandle, sceneNode + Offsets.offset.m_modelState + 0x80)
			tempEntity.HeadPos = memfuncs.ProcMemHandler.ReadVec(processHandle, boneMatrix + (AimBoneID * 32))
			tempEntity.origin = memfuncs.ProcMemHandler.ReadVec(processHandle, currentPawn + Offsets.offset.m_vOldOrigin)

			ViewMatrix = memfuncs.ProcMemHandler.ReadMatrix(processHandle, clientBaseAddress + Offsets.offset.dwViewMatrix)
			tempEntity.head2d = calculations.world_to_screen(ViewMatrix, tempEntity.HeadPos)

			ScreenVec = Vector2(globals.SCREEN_WIDTH / 2, globals.SCREEN_HEIGHT / 2)
			tempEntity.pixelDistance = calculations.distance_vec2(tempEntity.head2d, ScreenVec)

			if tempEntity.pixelDistance >= Options["AimbotFOV"]:
				continue

			tempEntity.Distance = calculations.distance_vec3(tempEntity.origin, LocalPlayer.origin)

			lifestate = memfuncs.ProcMemHandler.ReadInt(processHandle, currentPawn + Offsets.offset.m_lifeState)
			spotted = memfuncs.ProcMemHandler.ReadInt(processHandle, currentPawn + Offsets.offset.m_entitySpottedState + Offsets.offset.m_bSpotted)
			team = memfuncs.ProcMemHandler.ReadInt(processHandle, currentPawn + Offsets.offset.m_iTeamNum)

			if Options["EnableAimbotVisibilityCheck"] and not spotted:
				continue
			if lifestate != 256:  
				continue
			if Options["EnableAimbotTeamCheck"] and LocalPlayer.Team == team:
				continue

			entities.append(tempEntity)

		except pymem.exception.MemoryReadError as e:
			logging.debug(f"[Player {i}] Memory read failed: {e}")
			continue
		except Exception as e:
			logging.error(f"[Player {i}] Unexpected error: {e}")
			continue

	return entities

def ResolveBoneToID(selectedIndex):
	match selectedIndex:
		case 0: 
			return PLAYER_BONES["head"]
		case 1: 
			return PLAYER_BONES["seck_0"]
		case 2: 
			return PLAYER_BONES["spine_2"]
		case 3: 
			return PLAYER_BONES["leg_lower_L"]
		case _:
			return PLAYER_BONES["head"]


_last_update_time = time.perf_counter()
def Aimbot_Update(processHandle, clientBaseAddress, Offsets, Options, ARDUINO_HANDLE):
	m_flIntervalPerTick = 0.015625
	global _last_update_time
	try:

		current_time = time.perf_counter()
		frame_time = current_time - _last_update_time
		_last_update_time = current_time

		localPawn = memfuncs.ProcMemHandler.ReadPointer(processHandle, clientBaseAddress + Offsets.offset.dwLocalPlayerPawn)
		localController = memfuncs.ProcMemHandler.ReadPointer(processHandle, clientBaseAddress + Offsets.offset.dwLocalPlayerController)
		localTeam = memfuncs.ProcMemHandler.ReadInt(processHandle, localPawn + Offsets.offset.m_iTeamNum)
		localOrigin = memfuncs.ProcMemHandler.ReadVec(processHandle, localPawn + Offsets.offset.m_vOldOrigin)
		localView = memfuncs.ProcMemHandler.ReadVec(processHandle, localPawn + Offsets.offset.m_vecViewOffset)
		viewMatrix = memfuncs.ProcMemHandler.ReadMatrix(processHandle, clientBaseAddress + Offsets.offset.dwViewMatrix)
		entityList = memfuncs.ProcMemHandler.ReadPointer(processHandle, clientBaseAddress + Offsets.offset.dwEntityList)

		AimBoneID = ResolveBoneToID(Options["AimPosition"])
		bestEntity2D = None
		bestEntity3D = None
		bestMetric = float("inf")
		localIndex = -1

		for i in range(64):
			try:
				listEntry = memfuncs.ProcMemHandler.ReadPointer(processHandle, entityList + (8 * (i & 0x7FFF) >> 9) + 16)
				if not is_valid_address(listEntry):
					continue

				controller = memfuncs.ProcMemHandler.ReadPointer(processHandle, listEntry + 112 * (i & 0x1FF))
				if not is_valid_address(controller):
					continue

				pawnHandle = memfuncs.ProcMemHandler.ReadInt(processHandle, controller + Offsets.offset.m_hPlayerPawn)
				if pawnHandle == 0:
					continue

				listEntry2 = memfuncs.ProcMemHandler.ReadPointer(processHandle, entityList + 0x8 * ((pawnHandle & 0x7FFF) >> 9) + 0x10)
				if not is_valid_address(listEntry2):
					continue

				pawn = memfuncs.ProcMemHandler.ReadPointer(processHandle, listEntry2 + 0x70 * (pawnHandle & 0x1FF))
				if not is_valid_address(pawn):
					continue

				if pawn == localPawn:
					localIndex = i
					continue

				lifestate = memfuncs.ProcMemHandler.ReadInt(processHandle, pawn + Offsets.offset.m_lifeState)
				if lifestate != 256:
					continue

				team = memfuncs.ProcMemHandler.ReadInt(processHandle, pawn + Offsets.offset.m_iTeamNum)
				if Options["EnableAimbotTeamCheck"] and team == localTeam:
					continue

				if Options["EnableAimbotVisibilityCheck"] and localIndex > 0:
					spotted_mask = memfuncs.ProcMemHandler.ReadInt(processHandle, pawn + Offsets.offset.m_entitySpottedState + Offsets.offset.m_bSpottedByMask)
					if not (spotted_mask & (1 << (localIndex - 1))):
						continue

				sceneNode = memfuncs.ProcMemHandler.ReadPointer(processHandle, pawn + Offsets.offset.m_pGameSceneNode)
				boneMatrix = memfuncs.ProcMemHandler.ReadPointer(processHandle, sceneNode + Offsets.offset.m_modelState + 0x80)
				headPos = memfuncs.ProcMemHandler.ReadVec(processHandle, boneMatrix + (AimBoneID * 32))
				origin = memfuncs.ProcMemHandler.ReadVec(processHandle, pawn + Offsets.offset.m_vOldOrigin)

				if Options["EnableAimbotPrediction"]:
					ticks_passed = frame_time / m_flIntervalPerTick
					base_ticks_to_predict = 3.55
					ticks_to_predict = base_ticks_to_predict + max(0.0, ticks_passed)
					
					prediction_time = m_flIntervalPerTick * ticks_to_predict
					target_vel = memfuncs.ProcMemHandler.ReadVec(processHandle, pawn + Offsets.offset.m_vecVelocity)
					local_vel = memfuncs.ProcMemHandler.ReadVec(processHandle, localPawn + Offsets.offset.m_vecVelocity)
					relative_vel = Vector3(
						target_vel.x - local_vel.x,
						target_vel.y - local_vel.y,
						target_vel.z - local_vel.z
					)
					headPos = Vector3(
						headPos.x + relative_vel.x * prediction_time,
						headPos.y + relative_vel.y * prediction_time,
						headPos.z + relative_vel.z * prediction_time
					)

				head2d = calculations.world_to_screen(viewMatrix, headPos)
				if head2d.x <= -1 or head2d.y <= -1:
					continue

				screenCenter = Vector2(globals.SCREEN_WIDTH / 2, globals.SCREEN_HEIGHT / 2)
				pixelDist = calculations.distance_vec2(head2d, screenCenter)
				if pixelDist >= Options["AimbotFOV"]:
					continue

				entityDist = calculations.distance_vec3(origin, localOrigin)
				totalMetric = pixelDist + entityDist

				if totalMetric < bestMetric:
					bestMetric = totalMetric
					bestEntity2D = head2d
					bestEntity3D = headPos

			except Exception as e:
				logging.debug(f"[Entity {i}] Read failed: {e}")
				continue

		if bestEntity2D is not None and bestEntity3D is not None:
			cameraOrigin = localOrigin + localView
			newAngles = calculations.calculate_angles(cameraOrigin, bestEntity3D)

			shotsFired = memfuncs.ProcMemHandler.ReadInt(processHandle, localPawn + Offsets.offset.m_iShotsFired)
			if shotsFired > 1 and Options["EnableRecoilControl"]:
				globals.RCS_CTRL_BY_AIMBOT = True
				punch = memfuncs.ProcMemHandler.ReadVec(processHandle, localPawn + Offsets.offset.m_aimPunchAngle)
				punchX = punch.x * 12.0
				punchY = punch.y * 12.0
				recoilSmooth = max(1.0, min(float(Options["RecoilControlSmoothing"]), 3.0))
				punchX /= recoilSmooth
				punchY /= recoilSmooth

				bestEntity2D.y -= punchX
				bestEntity2D.x += punchY

			currentMouse = gameinput.getCurrentMousePosition()
			crosshairX = globals.SCREEN_WIDTH / 2.0
			crosshairY = globals.SCREEN_HEIGHT / 2.0

			sensitivityBase = memfuncs.ProcMemHandler.ReadPointer(processHandle, clientBaseAddress + Offsets.offset.dwSensitivity)
			sensitivity = memfuncs.ProcMemHandler.ReadFloat(processHandle, sensitivityBase + Offsets.offset.dwSensitivity_sensitivity)

			deltaX = (bestEntity2D.x - crosshairX) / sensitivity
			deltaY = (bestEntity2D.y - crosshairY) / sensitivity

			stepFactor = 1.0 / Options["AimbotSmoothing"]
			moveX = deltaX * stepFactor
			moveY = deltaY * stepFactor

			nextPos = Vector2(currentMouse.x + moveX, currentMouse.y + moveY)

			if ARDUINO_HANDLE is not None:
				gameinput.moveMouseToLocationArdunio(nextPos, handle=ARDUINO_HANDLE)
			else:
				gameinput.moveMouseToLocation(nextPos)
		globals.RCS_CTRL_BY_AIMBOT = False

	except pymem.exception.MemoryReadError as e:
		logging.debug(f"Aimbot Loop MemoryReadError: {e}")
	except Exception as e:
		logging.error(f"Aimbot Loop Exception: {e}")