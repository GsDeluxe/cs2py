from dataclasses import dataclass
import os
import json
import requests

@dataclass
class Offset:
	dwViewMatrix: int
	dwLocalPlayerPawn: int
	dwEntityList: int
	dwLocalPlayerController: int
	dwViewAngles: int
	dwGameRules: int
	dwSensitivity_sensitivity: int
	dwSensitivity: int 


	ButtonJump: int
	
	m_hPlayerPawn: int
	m_iHealth: int
	m_lifeState: int
	m_iTeamNum: int
	m_vOldOrigin: int
	m_pGameSceneNode: int
	m_modelState: int
	m_boneArray: int
	m_nodeToWorld: int
	m_sSanitizedPlayerName: int
	m_iIDEntIndex: int
	m_flFlashMaxAlpha: int
	m_fFlags: int
	m_iFOV: int
	m_pCameraServices: int
	m_bIsScoped: int

	m_vecViewOffset: int
	m_entitySpottedState: int 
	m_bSpotted: int 
	m_bBombPlanted: int
	
	m_iShotsFired: int
	m_aimPunchAngle: int
	
	m_bSpottedByMask: int
	m_vecVelocity: int
	


class Client:
	def __init__(self, manual_dump=False):
		if not manual_dump:
			self._load_from_url()
		else:
			self._load_from_file()

	def _load_from_url(self):
		try:
			self.offsets = self._get_json_from_url('https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json')
			self.clientdll = self._get_json_from_url('https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client_dll.json')
			self.buttons = self._get_json_from_url('https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/buttons.json')
		except Exception as e:
			print(f'Unable to get offsets: {e}')
			exit()

	def _get_json_from_url(self, url):
		return requests.get(url).json()

	def _load_from_file(self):
		try:
			base_path = os.path.join(os.getcwd(), 'output')
			self.offsets = self._load_json_from_file(base_path, 'offsets.json')
			self.clientdll = self._load_json_from_file(base_path, 'client_dll.json')
			self.buttons = self._load_json_from_file(base_path, 'buttons.json')
		except Exception as e:
			print(f'Unable to load data from file: {e}')
			exit()

	def _load_json_from_file(self, base_path, filename):
		with open(os.path.join(base_path, filename), 'r') as f:
			return json.load(f)

	def offset(self, a):
		return self._get_value_from_dict(self.offsets, ['client.dll', a], f'Offset {a} not found.')

	def get(self, a, b):
		try:
			return self.clientdll["client.dll"]['classes'][a]['fields'][b]
		except KeyError as e:
			print(f"Error with getting offset for {a} -> {b}: {e}")
			exit()

	def button(self, a):
		return self._get_value_from_dict(self.buttons, ['client.dll', a], f'Button {a} not found.')

	def _get_value_from_dict(self, data, keys, error_message):
		try:
			for key in keys:
				data = data[key]
			return data
		except KeyError:
			print(error_message)
			exit()


def get_offsets() -> Offset:
	oc = Client()
	offsets_obj = Offset(
		dwViewMatrix=oc.offset("dwViewMatrix"),
		dwLocalPlayerPawn=oc.offset("dwLocalPlayerPawn"),
		dwEntityList=oc.offset("dwEntityList"),
		dwLocalPlayerController=oc.offset("dwLocalPlayerController"),
		dwViewAngles = oc.offset("dwViewAngles"),
		dwGameRules = oc.offset("dwGameRules"),
		dwSensitivity_sensitivity = oc.offset("dwSensitivity_sensitivity"),
		dwSensitivity = oc.offset("dwSensitivity"),
		

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
		m_iIDEntIndex=oc.get("C_CSPlayerPawn", "m_iIDEntIndex"),
		m_flFlashMaxAlpha=oc.get("C_CSPlayerPawnBase", "m_flFlashMaxAlpha"),
		m_fFlags=oc.get("C_BaseEntity", "m_fFlags"),
		m_iFOV=oc.get("CCSPlayerBase_CameraServices", "m_iFOV"),
		m_pCameraServices=oc.get("C_BasePlayerPawn", "m_pCameraServices"),
		m_bIsScoped=oc.get("C_CSPlayerPawn", "m_bIsScoped"),
		m_vecViewOffset = oc.get("C_BaseModelEntity", "m_vecViewOffset"),
		m_entitySpottedState = oc.get("C_CSPlayerPawn", "m_entitySpottedState"),
		m_bSpotted = oc.get("EntitySpottedState_t", "m_bSpotted"),
		m_bBombPlanted = oc.get("C_CSGameRules", "m_bBombPlanted"),
		m_iShotsFired = oc.get("C_CSPlayerPawn", "m_iShotsFired"),
		m_aimPunchAngle = oc.get("C_CSPlayerPawn", "m_aimPunchAngle"),
		
		m_bSpottedByMask = oc.get("EntitySpottedState_t", "m_bSpottedByMask"),
		m_vecVelocity = oc.get("C_BaseEntity", "m_vecVelocity"),
		
	)
	return offsets_obj

