from dataclasses import dataclass
import struct

from functions.memfuncs import ProcMemHandler, GetModuleBase

SCHEMA_SYSTEM_PATTERN = "4C 8D 35 ? ? ? ? 0F 28 45"
BUTTON_LIST_PATTERN = "48 8B 15 ? ? ? ? 48 85 D2 74 ? 48 8B 02 48 85 C0"

CLIENT_PATTERNS = {
	"dwPrediction": ("48 8D 05 ? ? ? ? C3 CC CC CC CC CC CC CC CC 40 53 56 41 54", "Rip", 3, 0, None),
	"dwViewMatrix": ("48 8D 0D ? ? ? ? 48 C1 E0 06", "Rip", 3, 0, None),
	"dwLocalPlayerPawn": ("4C 39 B6 ? ? ? ? 74 ? 44 88 BE", "Imm32", 3, 0, "dwPrediction"),
	"dwLocalPlayerController": ("48 8B 05 ? ? ? ? 41 89 BE", "Rip", 3, 0, None),
	"dwEntityList": ("48 89 0D ? ? ? ? E9 ? ? ? ? CC", "Rip", 3, 0, None),
	"dwGameRules": ("F6 C1 01 0F 85 ? ? ? ? 4C 8B 05 ? ? ? ? 4D 85", "Rip", 12, 0, None),
	"dwSensitivity": ("48 8D 0D ? ? ? ? 0F 57 C9 0F 28 F0", "Rip", 3, 8, None),
	"dwGlobalVars": ("48 89 15 ? ? ? ? 48 89 42", "Rip", 3, 0, None),
	"dwPlantedC4": ("48 8B 1D ? ? ? ? 45 32 F6", "Rip", 3, 0, None),
}

def ScanPattern(buffer, pattern):
	signature = [None if token in ("?", "??") else int(token, 16) for token in pattern.split()]

	chunks = []
	chunkStart = None
	for index, byte in enumerate(signature + [None]):
		if byte is not None and chunkStart is None:
			chunkStart = index
		elif byte is None and chunkStart is not None:
			chunks.append((chunkStart, bytes(signature[chunkStart:index])))
			chunkStart = None

	anchorOffset, anchor = max(chunks, key=lambda chunk: len(chunk[1]))
	searchFrom = anchorOffset

	while True:
		found = buffer.find(anchor, searchFrom)
		if found < 0:
			return -1

		start = found - anchorOffset
		if start + len(signature) > len(buffer):
			return -1

		if start >= 0 and all(buffer[start + offset:start + offset + len(chunk)] == chunk for offset, chunk in chunks):
			return start
		searchFrom = found + 1

def Extract(buffer, index, kind, position, extra=0):
	if kind == "Rip":
		return index + position + 4 + struct.unpack_from("<i", buffer, index + position)[0] + extra
	return (struct.unpack_from("<I", buffer, index + position)[0] + extra) & 0xFFFFFFFF

def DumpOffsets(ClientBuffer):
	result = {"dwSensitivity_sensitivity": 0x58}

	for name, (pattern, kind, position, extra, parent) in CLIENT_PATTERNS.items():
		index = ScanPattern(ClientBuffer, pattern)
		if index < 0 or (parent and parent not in result):
			print(f"Pattern not found: {name}")
			continue

		result[name] = result.get(parent, 0) + Extract(ClientBuffer, index, kind, position, extra)

	return result

def DumpButtons(ProcessObject, ClientDLL, ClientBuffer):
	result = {}

	index = ScanPattern(ClientBuffer, BUTTON_LIST_PATTERN)
	if index < 0:
		print("Pattern not found: ButtonList")
		return result

	buttonPointer = ProcMemHandler.ReadPointer(ProcessObject, ClientDLL + Extract(ClientBuffer, index, "Rip", 3))
	visited = set()

	while buttonPointer and buttonPointer not in visited:
		visited.add(buttonPointer)
		try:
			buttonData = ProcMemHandler.ReadBytes(ProcessObject, buttonPointer, 0x90)
			name = ProcMemHandler.ReadString(ProcessObject, struct.unpack_from("<Q", buttonData, 0x08)[0], 32)
			if buttonPointer + 0x30 >= ClientDLL:
				result[name] = buttonPointer + 0x30 - ClientDLL
			buttonPointer = struct.unpack_from("<Q", buttonData, 0x88)[0]
		except Exception as e:
			print(f"Failed to read button at 0x{buttonPointer:X}: {e}")
			break

	return result

def ReadHashElements(ProcessObject, hashAddress):
	elements = []
	header = ProcMemHandler.ReadBytes(ProcessObject, hashAddress, 0x1870)
	blocksAllocated, peakAllocated = struct.unpack_from("<ii", header, 0x0C)

	for bucket in range(256):
		nodePointer = struct.unpack_from("<Q", header, 0x60 + bucket * 0x18 + 0x10)[0]
		while nodePointer and len(elements) < blocksAllocated:
			nextPointer, dataPointer = struct.unpack_from("<QQ", ProcMemHandler.ReadBytes(ProcessObject, nodePointer, 0x18), 0x08)
			if dataPointer:
				elements.append(dataPointer)
			nodePointer = nextPointer

	blobPointer = struct.unpack_from("<Q", header, 0x20)[0]
	for _ in range(max(peakAllocated, 0)):
		if not blobPointer:
			break
		blobData = ProcMemHandler.ReadBytes(ProcessObject, blobPointer, 0x18)
		if struct.unpack_from("<Q", blobData, 0x10)[0]:
			elements.append(struct.unpack_from("<Q", blobData, 0x10)[0])
		blobPointer = struct.unpack_from("<Q", blobData, 0)[0]

	return list(dict.fromkeys(elements))

def DumpSchemas(ProcessObject, SchemaSystemDLL, SchemaSystemDLLSize, moduleName="client.dll"):
	result = {}

	buffer = ProcMemHandler.ReadBytes(ProcessObject, SchemaSystemDLL, SchemaSystemDLLSize)
	index = ScanPattern(buffer, SCHEMA_SYSTEM_PATTERN)
	if index < 0:
		print("Pattern not found: SchemaSystem")
		return result

	schemaSystem = ProcMemHandler.ReadBytes(ProcessObject, SchemaSystemDLL + Extract(buffer, index, "Rip", 3), 0x1A0)
	scopeCount = min(max(struct.unpack_from("<i", schemaSystem, 0x190)[0], 0), 256)
	scopesPointer = struct.unpack_from("<Q", schemaSystem, 0x198)[0]
	scopes = struct.unpack(f"<{scopeCount}Q", ProcMemHandler.ReadBytes(ProcessObject, scopesPointer, scopeCount * 8))

	for scopePointer in scopes:
		if not scopePointer or ProcMemHandler.ReadString(ProcessObject, scopePointer + 0x08, 256) != moduleName:
			continue

		for classPointer in ReadHashElements(ProcessObject, scopePointer + 0x560):
			try:
				classData = ProcMemHandler.ReadBytes(ProcessObject, classPointer, 0x38)
				className = ProcMemHandler.ReadString(ProcessObject, struct.unpack_from("<Q", classData, 0x08)[0], 128)
				fieldCount = struct.unpack_from("<h", classData, 0x24)[0]
				fieldsPointer = struct.unpack_from("<Q", classData, 0x30)[0]

				fields = {}
				if fieldCount > 0 and fieldsPointer:
					fieldData = ProcMemHandler.ReadBytes(ProcessObject, fieldsPointer, fieldCount * 0x20)
					for field in range(fieldCount):
						fieldName = ProcMemHandler.ReadString(ProcessObject, struct.unpack_from("<Q", fieldData, field * 0x20)[0], 128)
						fields[fieldName] = struct.unpack_from("<i", fieldData, field * 0x20 + 0x10)[0]

				if className:
					result[className] = fields
			except Exception as e:
				print(f"Failed to read class at 0x{classPointer:X}: {e}")

	return result

@dataclass
class Offset:
	dwViewMatrix: int
	dwLocalPlayerPawn: int
	dwEntityList: int
	dwLocalPlayerController: int
	dwGameRules: int
	dwSensitivity_sensitivity: int
	dwSensitivity: int
	dwGlobalVars: int
	dwPlantedC4: int

	ButtonJump: int

	m_hPlayerPawn: int
	m_iHealth: int
	m_lifeState: int
	m_iTeamNum: int
	m_vOldOrigin: int
	m_pGameSceneNode: int
	m_modelState: int
	m_boneArray: int
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
	m_pAimPunchServices: int
	m_unpredictableBaseTick: int

	m_bSpottedByMask: int
	m_vecVelocity: int

	m_ArmorValue: int
	m_bIsDefusing: int
	m_pInGameMoneyServices: int
	m_iAccount: int
	m_pWeaponServices: int
	m_hActiveWeapon: int
	m_pItemServices: int
	m_bHasHelmet: int
	m_bHasDefuser: int
	m_AttributeManager: int
	m_Item: int
	m_iItemDefinitionIndex: int
	m_iFOVStart: int

	m_designerName: int
	m_nSmokeEffectTickBegin: int
	m_bDidSmokeEffect: int
	m_vSmokeDetonationPos: int
	m_flC4Blow: int
	m_bBombDefused: int

def GetOffsets(ProcessObject):
	ClientDLL, ClientDLLSize = GetModuleBase(modulename="client.dll", process_object=ProcessObject)
	SchemaSystemDLL, SchemaSystemDLLSize = GetModuleBase(modulename="schemasystem.dll", process_object=ProcessObject)
	ClientBuffer = ProcMemHandler.ReadBytes(ProcessObject, ClientDLL, ClientDLLSize)

	Offsets = DumpOffsets(ClientBuffer)
	Buttons = DumpButtons(ProcessObject, ClientDLL, ClientBuffer)
	Schemas = DumpSchemas(ProcessObject, SchemaSystemDLL, SchemaSystemDLLSize)

	def Lookup(data, *keys):
		try:
			for key in keys:
				data = data[key]
			return data
		except KeyError:
			print(f"Offset not found: {' -> '.join(keys)}")
			exit()

	print(f"Dumped {len(Offsets)} offsets, {len(Buttons)} buttons and {len(Schemas)} classes")

	return Offset(
		dwViewMatrix = Lookup(Offsets, "dwViewMatrix"),
		dwLocalPlayerPawn = Lookup(Offsets, "dwLocalPlayerPawn"),
		dwEntityList = Lookup(Offsets, "dwEntityList"),
		dwLocalPlayerController = Lookup(Offsets, "dwLocalPlayerController"),
		dwGameRules = Lookup(Offsets, "dwGameRules"),
		dwSensitivity_sensitivity = Lookup(Offsets, "dwSensitivity_sensitivity"),
		dwSensitivity = Lookup(Offsets, "dwSensitivity"),
		dwGlobalVars = Lookup(Offsets, "dwGlobalVars"),
		dwPlantedC4 = Lookup(Offsets, "dwPlantedC4"),

		ButtonJump = Lookup(Buttons, "jump"),

		m_hPlayerPawn = Lookup(Schemas, "CCSPlayerController", "m_hPlayerPawn"),
		m_iHealth = Lookup(Schemas, "C_BaseEntity", "m_iHealth"),
		m_lifeState = Lookup(Schemas, "C_BaseEntity", "m_lifeState"),
		m_iTeamNum = Lookup(Schemas, "C_BaseEntity", "m_iTeamNum"),
		m_vOldOrigin = Lookup(Schemas, "C_BasePlayerPawn", "m_vOldOrigin"),
		m_pGameSceneNode = Lookup(Schemas, "C_BaseEntity", "m_pGameSceneNode"),
		m_modelState = Lookup(Schemas, "CSkeletonInstance", "m_modelState"),
		m_boneArray = 128,
		m_sSanitizedPlayerName = Lookup(Schemas, "CCSPlayerController", "m_sSanitizedPlayerName"),
		m_iIDEntIndex = Lookup(Schemas, "C_CSPlayerPawn", "m_iIDEntIndex"),
		m_flFlashMaxAlpha = Lookup(Schemas, "C_CSPlayerPawnBase", "m_flFlashMaxAlpha"),
		m_fFlags = Lookup(Schemas, "C_BaseEntity", "m_fFlags"),
		m_iFOV = Lookup(Schemas, "CCSPlayerBase_CameraServices", "m_iFOV"),
		m_pCameraServices = Lookup(Schemas, "C_BasePlayerPawn", "m_pCameraServices"),
		m_bIsScoped = Lookup(Schemas, "C_CSPlayerPawn", "m_bIsScoped"),

		m_vecViewOffset = Lookup(Schemas, "C_BaseModelEntity", "m_vecViewOffset"),
		m_entitySpottedState = Lookup(Schemas, "C_CSPlayerPawn", "m_entitySpottedState"),
		m_bSpotted = Lookup(Schemas, "EntitySpottedState_t", "m_bSpotted"),
		m_bBombPlanted = Lookup(Schemas, "C_CSGameRules", "m_bBombPlanted"),

		m_iShotsFired = Lookup(Schemas, "C_CSPlayerPawn", "m_iShotsFired"),
		m_pAimPunchServices = Lookup(Schemas, "C_CSPlayerPawn", "m_pAimPunchServices"),
		m_unpredictableBaseTick = Lookup(Schemas, "CCSPlayer_AimPunchServices", "m_unpredictableBaseTick"),

		m_bSpottedByMask = Lookup(Schemas, "EntitySpottedState_t", "m_bSpottedByMask"),
		m_vecVelocity = Lookup(Schemas, "C_BaseEntity", "m_vecVelocity"),

		m_ArmorValue = Lookup(Schemas, "C_CSPlayerPawn", "m_ArmorValue"),
		m_bIsDefusing = Lookup(Schemas, "C_CSPlayerPawn", "m_bIsDefusing"),
		m_pInGameMoneyServices = Lookup(Schemas, "CCSPlayerController", "m_pInGameMoneyServices"),
		m_iAccount = Lookup(Schemas, "CCSPlayerController_InGameMoneyServices", "m_iAccount"),
		m_pWeaponServices = Lookup(Schemas, "C_BasePlayerPawn", "m_pWeaponServices"),
		m_hActiveWeapon = Lookup(Schemas, "CPlayer_WeaponServices", "m_hActiveWeapon"),
		m_pItemServices = Lookup(Schemas, "C_BasePlayerPawn", "m_pItemServices"),
		m_bHasHelmet = Lookup(Schemas, "CCSPlayer_ItemServices", "m_bHasHelmet"),
		m_bHasDefuser = Lookup(Schemas, "CCSPlayer_ItemServices", "m_bHasDefuser"),
		m_AttributeManager = Lookup(Schemas, "C_EconEntity", "m_AttributeManager"),
		m_Item = Lookup(Schemas, "C_AttributeContainer", "m_Item"),
		m_iItemDefinitionIndex = Lookup(Schemas, "C_EconItemView", "m_iItemDefinitionIndex"),
		m_iFOVStart = Lookup(Schemas, "CCSPlayerBase_CameraServices", "m_iFOVStart"),

		m_designerName = Lookup(Schemas, "CEntityIdentity", "m_designerName"),
		m_nSmokeEffectTickBegin = Lookup(Schemas, "C_SmokeGrenadeProjectile", "m_nSmokeEffectTickBegin"),
		m_bDidSmokeEffect = Lookup(Schemas, "C_SmokeGrenadeProjectile", "m_bDidSmokeEffect"),
		m_vSmokeDetonationPos = Lookup(Schemas, "C_SmokeGrenadeProjectile", "m_vSmokeDetonationPos"),
		m_flC4Blow = Lookup(Schemas, "C_PlantedC4", "m_flC4Blow"),
		m_bBombDefused = Lookup(Schemas, "C_PlantedC4", "m_bBombDefused"),
	)
