import dearpygui.dearpygui as dpg
import threading, time, os
import win32api, win32gui, win32con

KeyNames = [
	"OFF",
	"VK_LBUTTON",
	"VK_RBUTTON",
	"VK_CANCEL",
	"VK_MBUTTON",
	"VK_XBUTTON1",
	"VK_XBUTTON2",
	"Unknown",
	"VK_BACK",
	"VK_TAB",
	"Unknown",
	"Unknown",
	"VK_CLEAR",
	"VK_RETURN",
	"Unknown",
	"Unknown",
	"VK_SHIFT",
	"VK_CONTROL",
	"VK_MENU",
	"VK_PAUSE",
	"VK_CAPITAL",
	"VK_KANA",
	"Unknown",
	"VK_JUNJA",
	"VK_FINAL",
	"VK_KANJI",
	"Unknown",
	"VK_ESCAPE",
	"VK_CONVERT",
	"VK_NONCONVERT",
	"VK_ACCEPT",
	"VK_MODECHANGE",
	"VK_SPACE",
	"VK_PRIOR",
	"VK_NEXT",
	"VK_END",
	"VK_HOME",
	"VK_LEFT",
	"VK_UP",
	"VK_RIGHT",
	"VK_DOWN",
	"VK_SELECT",
	"VK_PRINT",
	"VK_EXECUTE",
	"VK_SNAPSHOT",
	"VK_INSERT",
	"VK_DELETE",
	"VK_HELP",
	"0",
	"1",
	"2",
	"3",
	"4",
	"5",
	"6",
	"7",
	"8",
	"9",
	"Unknown",
	"Unknown",
	"Unknown",
	"Unknown",
	"Unknown",
	"Unknown",
	"Unknown",
	"A",
	"B",
	"C",
	"D",
	"E",
	"F",
	"G",
	"H",
	"I",
	"J",
	"K",
	"L",
	"M",
	"N",
	"O",
	"P",
	"Q",
	"R",
	"S",
	"T",
	"U",
	"V",
	"W",
	"X",
	"Y",
	"Z",
	"VK_LWIN",
	"VK_RWIN",
	"VK_APPS",
	"Unknown",
	"VK_SLEEP",
	"VK_NUMPAD0",
	"VK_NUMPAD1",
	"VK_NUMPAD2",
	"VK_NUMPAD3",
	"VK_NUMPAD4",
	"VK_NUMPAD5",
	"VK_NUMPAD6",
	"VK_NUMPAD7",
	"VK_NUMPAD8",
	"VK_NUMPAD9",
	"VK_MULTIPLY",
	"VK_ADD",
	"VK_SEPARATOR",
	"VK_SUBTRACT",
	"VK_DECIMAL",
	"VK_DIVIDE",
	"VK_F1",
	"VK_F2",
	"VK_F3",
	"VK_F4",
	"VK_F5",
	"VK_F6",
	"VK_F7",
	"VK_F8",
	"VK_F9",
	"VK_F10",
	"VK_F11",
	"VK_F12",
	"VK_F13",
	"VK_F14",
	"VK_F15",
	"VK_F16",
	"VK_F17",
	"VK_F18",
	"VK_F19",
	"VK_F20",
	"VK_F21",
	"VK_F22",
	"VK_F23",
	"VK_F24",
	"Unknown",
	"Unknown",
	"Unknown",
	"Unknown",
	"Unknown",
	"Unknown",
	"Unknown",
	"Unknown",
	"VK_NUMLOCK",
	"VK_SCROLL",
	"VK_OEM_NEC_EQUAL",
	"VK_OEM_FJ_MASSHOU",
	"VK_OEM_FJ_TOUROKU",
	"VK_OEM_FJ_LOYA",
	"VK_OEM_FJ_ROYA",
	"Unknown",
	"Unknown",
	"Unknown",
	"Unknown",
	"Unknown",
	"Unknown",
	"Unknown",
	"Unknown",
	"Unknown",
	"VK_LSHIFT",
	"VK_RSHIFT",
	"VK_LCONTROL",
	"VK_RCONTROL",
	"VK_LMENU",
	"VK_RMENU"
]
KeyCodes = [
	0x0,  # Undefined
	0x01,
	0x02,
	0x03,
	0x04,
	0x05,
	0x06,
	0x07, # Undefined
	0x08,
	0x09,
	0x0A, # Reserved
	0x0B, # Reserved
	0x0C,
	0x0D,
	0x0E, # Undefined
	0x0F, # Undefined
	0x10,
	0x11,
	0x12,
	0x13,
	0x14,
	0x15,
	0x16, # IME On
	0x17,
	0x18,
	0x19,
	0x1A, # IME Off
	0x1B,
	0x1C,
	0x1D,
	0x1E,
	0x1F,
	0x20,
	0x21,
	0x22,
	0x23,
	0x24,
	0x25,
	0x26,
	0x27,
	0x28,
	0x29,
	0x2A,
	0x2B,
	0x2C,
	0x2D,
	0x2E,
	0x2F,
	0x30,
	0x31,
	0x32,
	0x33,
	0x34,
	0x35,
	0x36,
	0x37,
	0x38,
	0x39,
	0x3A, # Undefined
	0x3B, # Undefined
	0x3C, # Undefined
	0x3D, # Undefined
	0x3E, # Undefined
	0x3F, # Undefined
	0x40, # Undefined
	0x41,
	0x42,
	0x43,
	0x44,
	0x45,
	0x46,
	0x47,
	0x48,
	0x49,
	0x4A,
	0x4B,
	0x4C,
	0x4B,
	0x4E,
	0x4F,
	0x50,
	0x51,
	0x52,
	0x53,
	0x54,
	0x55,
	0x56,
	0x57,
	0x58,
	0x59,
	0x5A,
	0x5B,
	0x5C,
	0x5D,
	0x5E, # Rservered
	0x5F,
	0x60, # Numpad1
	0x61, # Numpad2
	0x62, # Numpad3
	0x63, # Numpad4
	0x64, # Numpad5
	0x65, # Numpad6
	0x66, # Numpad7
	0x67, # Numpad8
	0x68, # Numpad8
	0x69, # Numpad9
	0x6A,
	0x6B,
	0x6C,
	0x6D,
	0x6E,
	0x6F,
	0x70, # F1
	0x71, # F2
	0x72, # F3
	0x73, # F4
	0x74, # F5
	0x75, # F6
	0x76, # F7
	0x77, # F8
	0x78, # F9
	0x79, # F10
	0x7A, # F11
	0x7B, # F12
	0x7C, # F13
	0x7D, # F14
	0x7E, # F15
	0x7F, # F16
	0x80, # F17
	0x81, # F18
	0x82, # F19
	0x83, # F20
	0x84, # F21
	0x85, # F22
	0x86, # F23
	0x87, # F24
	0x88, # Unkown
	0x89, # Unkown
	0x8A, # Unkown
	0x8B, # Unkown
	0x8C, # Unkown
	0x8D, # Unkown
	0x8E, # Unkown
	0x8F, # Unkown
	0x90,
	0x91,
	0x92, # OEM Specific
	0x93, # OEM Specific
	0x94, # OEM Specific
	0x95, # OEM Specific
	0x96, # OEM Specific
	0x97, # Unkown
	0x98, # Unkown
	0x99, # Unkown
	0x9A, # Unkown
	0x9B, # Unkown
	0x9C, # Unkown
	0x9D, # Unkown
	0x9E, # Unkown 
	0x9F, # Unkown
	0xA0,
	0xA1,
	0xA2,
	0xA3,
	0xA4,
	0xA5
]

class CS2PY_GUI:
	def __init__(self, config):
		self.n = 0
		self.ui_dragging = False
		self.viewport_width = 900
		self.viewport_height = 420
		self.interpolate_window = False

		self.init_context()
		self.create_theme()
		self.config = config
		self.build_ui()
		self.add_event_handlers()

	def hex_to_rgb(self, hex_code):
		hex_code = hex_code.lstrip('#')
		return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

	def rgb_to_hex(self, rgb):
		rgb = [round(x * 255) for x in rgb[:3]]
		return '#{:02X}{:02X}{:02X}'.format(*rgb[:3])

	def init_context(self):
		dpg.create_context()
		self.viewport = dpg.create_viewport(
			title="cs2py",
			width=self.viewport_width,
			height=self.viewport_height,
			vsync=True,
			decorated=False,
			resizable=False,
			max_width=self.viewport_width,
			max_height=self.viewport_height
		)
		dpg.setup_dearpygui()

	def keybind_use(self, sender, app_data, user_data):
		waiting_for_key = {}
		current_keys = {}
		delay_counters = {}

		key_id = user_data

		waiting_for_key[key_id] = True
		delay_counters[key_id] = 0
		dpg.set_item_label(sender, "...")

		def capture_key():
			while waiting_for_key[key_id]:
				time.sleep(0.05)
				delay_counters[key_id] += 1

				if delay_counters[key_id] > 3:
					for i in range(256):
						if win32api.GetAsyncKeyState(i) & 0x8000:
							key_name = KeyNames[i] if i < len(KeyNames) else f"Unknown({i})"
							current_keys[key_id] = i
							dpg.set_item_label(sender, f"{key_name}")
							waiting_for_key[key_id] = False
							self.config.update({user_data: i})
							return

		threading.Thread(target=capture_key, daemon=True).start()


	def create_theme(self):
		with dpg.theme() as theme:
			with dpg.theme_component(dpg.mvAll):
				dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255))
				dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, (128, 128, 128, 255))

				dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (10, 10, 10, 255))
				dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (0, 0, 0, 0))
				dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (20, 20, 20, 255))
				dpg.add_theme_color(dpg.mvThemeCol_Border, (110, 110, 127, 127))
				dpg.add_theme_color(dpg.mvThemeCol_BorderShadow, (0, 0, 0, 0))

				dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (38, 38, 38, 138))
				dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (130, 80, 220, 100))
				dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (110, 50, 230, 200))

				dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (110, 60, 200, 255))
				dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (100, 50, 190, 255))
				dpg.add_theme_color(dpg.mvThemeCol_TitleBgCollapsed, (110, 60, 200, 220))

				dpg.add_theme_color(dpg.mvThemeCol_Button, (51, 51, 51, 102))
				dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (255, 255, 255, 10))
				dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (87, 16, 250, 255))

				dpg.add_theme_color(dpg.mvThemeCol_Header, (255, 255, 255, 10))
				dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (130, 80, 220, 150))
				dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (130, 80, 220, 180))

				dpg.add_theme_color(dpg.mvThemeCol_Separator, (110, 110, 127, 127))
				dpg.add_theme_color(dpg.mvThemeCol_SeparatorHovered, (130, 80, 220, 180))
				dpg.add_theme_color(dpg.mvThemeCol_SeparatorActive, (130, 80, 220, 200))

				dpg.add_theme_color(dpg.mvThemeCol_ResizeGrip, (255, 255, 255, 10))
				dpg.add_theme_color(dpg.mvThemeCol_ResizeGripHovered, (255, 255, 255, 33))
				dpg.add_theme_color(dpg.mvThemeCol_ResizeGripActive, (130, 80, 220, 180))

				dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (130, 80, 220, 150))
				dpg.add_theme_color(dpg.mvThemeCol_Tab, (110, 60, 200, 180))
				dpg.add_theme_color(dpg.mvThemeCol_TabActive, (130, 80, 220, 200)) 

				dpg.add_theme_color(dpg.mvThemeCol_PlotLines, (155, 155, 155, 255))
				dpg.add_theme_color(dpg.mvThemeCol_PlotLinesHovered, (255, 110, 89, 255))
				dpg.add_theme_color(dpg.mvThemeCol_PlotHistogram, (229, 178, 0, 255))
				dpg.add_theme_color(dpg.mvThemeCol_PlotHistogramHovered, (255, 153, 0, 255))

				dpg.add_theme_color(dpg.mvThemeCol_TextSelectedBg, (130, 80, 220, 100))
				dpg.add_theme_color(dpg.mvThemeCol_DragDropTarget, (255, 255, 0, 229))
				dpg.add_theme_color(dpg.mvThemeCol_NavWindowingHighlight, (255, 255, 255, 178))
				dpg.add_theme_color(dpg.mvThemeCol_NavWindowingDimBg, (204, 204, 204, 51))
				dpg.add_theme_color(dpg.mvThemeCol_ModalWindowDimBg, (204, 204, 204, 89))
				dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (130, 80, 220, 255))
				dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (120, 60, 220, 150))
				dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (130, 80, 220, 200))

				dpg.add_theme_style(dpg.mvStyleVar_Alpha, 1.0)
				dpg.add_theme_style(dpg.mvStyleVar_DisabledAlpha, 1.0)
				dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 12, 12)
				dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
				dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0.0)
				dpg.add_theme_style(dpg.mvStyleVar_WindowMinSize, 20, 20)
				dpg.add_theme_style(dpg.mvStyleVar_WindowTitleAlign, 0.5, 0.5)
				dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 3.0)
				dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 1.0)
				dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 2.0)
				dpg.add_theme_style(dpg.mvStyleVar_PopupBorderSize, 1.0)
				dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 20, 4)
				dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
				dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 0.0)
				dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 6, 6)
				dpg.add_theme_style(dpg.mvStyleVar_ItemInnerSpacing, 7, 2)
				dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 12, 9)
				dpg.add_theme_style(dpg.mvStyleVar_IndentSpacing, 0.0)
				dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize, 12.0)
				dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 16.0)
				dpg.add_theme_style(dpg.mvStyleVar_GrabMinSize, 6.0)
				dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 20.0)
				dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 4.0)
				dpg.add_theme_style(dpg.mvStyleVar_TabBorderSize, 0.0)
				dpg.add_theme_style(dpg.mvStyleVar_ButtonTextAlign, 0.5, 0.5)
				dpg.add_theme_style(dpg.mvStyleVar_SelectableTextAlign, 0.0, 0.0)

			dpg.bind_theme(theme)


	def lerp(self, a, b, t):
		return a + (b - a) * t

	def is_dragging(self, _, data):
		if dpg.is_mouse_button_down(0):
			y = data[1]
			if -2 <= y <= 19:
				self.ui_dragging = True
				if dpg.is_viewport_vsync_on(): dpg.set_viewport_vsync(False)
		else:
			self.ui_dragging = False
			if not dpg.is_viewport_vsync_on(): dpg.set_viewport_vsync(True)

	def drag_logic(self, _, data):
		self.n += 1
		if self.n % 30 != 0:
			return
		self.n = 0

		if self.ui_dragging:
			pos = dpg.get_viewport_pos()
			x = data[1]
			y = data[2]

			if not self.interpolate_window:
				dpg.configure_viewport(self.viewport, x_pos=pos[0] + x, y_pos=pos[1] + y)
			else:
				speed = float(0.1)
				interpolated_x = self.lerp(pos[0], pos[0] + x, speed)
				interpolated_y = self.lerp(pos[1], pos[1] + y, speed)

				dpg.configure_viewport(self.viewport, x_pos=interpolated_x, y_pos=interpolated_y)

	def add_event_handlers(self):
		with dpg.handler_registry():
			dpg.add_mouse_drag_handler(0, callback=self.drag_logic)
			dpg.add_mouse_move_handler(callback=self.is_dragging)
		dpg.set_viewport_always_top(True)

	def run(self):
		dpg.show_viewport()
		dpg.start_dearpygui()
		dpg.destroy_context()

	def build_ui(self):
		with dpg.window(label="cs2py v2.0", width=self.viewport_width, height=self.viewport_height, no_move=True, no_resize=True, no_close=True, no_collapse=True, tag="cs2py_dpg_window"):
			dpg.add_text("INS Show/Hide Menu")
			dpg.add_text("END To Quit Program")
			dpg.add_text("HOME For Streamproof")
			dpg.add_separator()

			with dpg.tab_bar():
				
				with dpg.tab(label="Aimbot"):
					dpg.add_checkbox(label="Enable Aimbot", default_value=self.config["EnableAimbot"], callback=lambda s, d: self.config.update({"EnableAimbot": d}))
					dpg.add_checkbox(label="Team Check##Aimbot", default_value=self.config["EnableAimbotTeamCheck"], callback=lambda s, d: self.config.update({"EnableAimbotTeamCheck": d}))
					dpg.add_checkbox(label="Visibility Check", default_value=self.config["EnableAimbotVisibilityCheck"], callback=lambda s, d: self.config.update({"EnableAimbotVisibilityCheck": d}))
					dpg.add_slider_int(label="Aimbot FOV", default_value=self.config["AimbotFOV"], min_value=50, max_value=200, callback=lambda s, d: self.config.update({"AimbotFOV": d}))
					dpg.add_slider_int(label="Aimbot Smoothing", default_value=self.config["AimbotSmoothing"], min_value=1, max_value=10, callback=lambda s, d: self.config.update({"AimbotSmoothing": d}))
					dpg.add_checkbox(label="Prediction (Velocity-based)", default_value=self.config["EnableAimbotPrediction"], callback=lambda s, d: self.config.update({"EnableAimbotPrediction": d}))
					dpg.add_combo(label="Aim Position", items=["Head", "Neck", "Torso", "Leg"], default_value="Head", callback=lambda s, d: self.config.update({"AimPosition": d}))
					dpg.add_text("Aimbot HotKey")
					dpg.add_button(label=KeyNames[self.config["AimbotKey"]] if self.config["AimbotKey"] < len(KeyNames) else f"Unknown({self.config['AimbotKey']})", user_data="AimbotKey", callback=self.keybind_use)

				with dpg.tab(label="ESP & Visuals"):
					dpg.add_checkbox(label="Enable ESP Team Check", default_value=self.config["EnableESPTeamCheck"], callback=lambda s, d: self.config.update({"EnableESPTeamCheck": d}))
					dpg.add_checkbox(label="Enable Skeleton Rendering", default_value=self.config["EnableESPSkeletonRendering"], callback=lambda s, d: self.config.update({"EnableESPSkeletonRendering": d}))
					dpg.add_checkbox(label="Enable Box Rendering", default_value=self.config["EnableESPBoxRendering"], callback=lambda s, d: self.config.update({"EnableESPBoxRendering": d}))
					dpg.add_checkbox(label="Enable Tracer Rendering", default_value=self.config["EnableESPTracerRendering"], callback=lambda s, d: self.config.update({"EnableESPTracerRendering": d}))
					dpg.add_checkbox(label="Enable Name Rendering", default_value=self.config["EnableESPHealthBarRendering"], callback=lambda s, d: self.config.update({"EnableESPHealthBarRendering": d}))
					dpg.add_checkbox(label="Enable Health Bar Rendering", default_value=self.config["EnableESPNameText"], callback=lambda s, d: self.config.update({"EnableESPNameText": d}))
					dpg.add_checkbox(label="Enable Health Text", default_value=self.config["EnableESPHealthText"], callback=lambda s, d: self.config.update({"EnableESPHealthText": d}))
					dpg.add_checkbox(label="Enable Distance Text", default_value=self.config["EnableESPDistanceText"], callback=lambda s, d: self.config.update({"EnableESPDistanceText": d}))
					dpg.add_separator()
					dpg.add_checkbox(label="Enable Bomb Timer", default_value=self.config["EnableESPBombTimer"], callback=lambda s, d: self.config.update({"EnableESPBombTimer": d}))

				with dpg.tab(label="Triggerbot"):
					dpg.add_checkbox(label="Enable Trigger Bot", default_value=self.config["EnableTriggerbot"], callback=lambda s, d: self.config.update({"EnableTriggerbot": d}))
					dpg.add_checkbox(label="Team Check##Triggerbot", default_value=self.config["EnableTriggerbotTeamCheck"], callback=lambda s, d: self.config.update({"EnableTriggerbotTeamCheck": d}))
					dpg.add_checkbox(label="Key Check", default_value=self.config["EnableTriggerbotKeyCheck"], callback=lambda s, d: self.config.update({"EnableTriggerbotKeyCheck": d}))
					dpg.add_text("Triggerbot HotKey")
					dpg.add_button(label=KeyNames[self.config["TriggerbotKey"]] if self.config["TriggerbotKey"] < len(KeyNames) else f"Unknown({self.config['TriggerbotKey']})", user_data="TriggerbotKey", callback=self.keybind_use)

				with dpg.tab(label="Recoil Control"):
					dpg.add_checkbox(label="Enable Recoil Control", default_value=self.config["EnableRecoilControl"], callback=lambda s, d: self.config.update({"EnableRecoilControl": d}))
					dpg.add_slider_float(label="Recoil Control Smoothing", default_value=float(self.config["RecoilControlSmoothing"]), min_value=1.0, max_value=3.0, format="%.2f", callback=lambda s, d: self.config.update({"RecoilControlSmoothing": float(d)}))

				with dpg.tab(label="Colors"):
					dpg.add_text("Player Colors")
					dpg.add_color_picker(label="Counter Terrorist", default_value=self.hex_to_rgb(self.config["CT_color"]), no_alpha=True, no_inputs=True, no_side_preview=True, no_small_preview=True, width=75, height=75, callback=lambda s, d: self.config.update({"CT_color": self.rgb_to_hex(d)}))
					dpg.add_color_picker(label="Terrorist", default_value=self.hex_to_rgb(self.config["T_color"]), no_alpha=True, no_inputs=True, no_side_preview=True, no_small_preview=True, width=75, height=75, callback=lambda s, d: self.config.update({"T_color": self.rgb_to_hex(d)}))
					dpg.add_separator()
					dpg.add_text("Misc Colors")
					dpg.add_color_picker(label="FOV Color", default_value=self.hex_to_rgb(self.config["FOV_color"]), no_alpha=True, no_inputs=True, no_side_preview=True, no_small_preview=True, width=75, height=75, callback=lambda s, d: self.config.update({"FOV_color": self.rgb_to_hex(d)}))

				with dpg.tab(label="Misc"):
					dpg.add_checkbox(label="Enable Anti Flashbang", default_value=self.config["EnableAntiFlashbang"], callback=lambda s, d: self.config.update({"EnableAntiFlashbang": d}))
					dpg.add_separator()
					dpg.add_checkbox(label="Enable Bhop", default_value=self.config["EnableBhop"], callback=lambda s, d: self.config.update({"EnableBhop": d}))
					dpg.add_separator()
					dpg.add_checkbox(label="Enable Discord RPC", default_value=self.config["EnableDiscordRPC"], callback=lambda s, d: self.config.update({"EnableDiscordRPC": d}))
					dpg.add_separator()
					dpg.add_checkbox(label="Enable FOV Changer", default_value=self.config["EnableFovChanger"], callback=lambda s, d: self.config.update({"EnableFovChanger": d}))
					dpg.add_slider_int(label="Set FOV", default_value=self.config["FovChangeSize"], min_value=50, max_value=170, callback=lambda s, d: self.config.update({"FovChangeSize": d}))


def run_gui(Options):
	gui = CS2PY_GUI(Options)
	gui.run()