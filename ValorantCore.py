import os
import sys
import json
import time
import datetime
import ctypes
import threading
import subprocess
from ctypes import wintypes
import psutil
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import shutil
import atexit
import math
import winreg

# Resolve correct base directory whether running as .py or frozen .exe
if getattr(sys, 'frozen', False):
    # PyInstaller extracts data to sys._MEIPASS; the exe itself lives in sys.executable
    _BASE_DIR = os.path.dirname(sys.executable)   # folder where VAL-CORE.exe sits
    _MEIPASS  = sys._MEIPASS                       # temp extraction dir for bundled files
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    _MEIPASS  = _BASE_DIR

class AppManager:
    # Config lives next to the exe/script so settings persist between runs
    CONFIG_FILE = os.path.join(_BASE_DIR, "launcher_config.json")
    LOG_FILE    = os.path.join(_BASE_DIR, "log", "val_core_system.log")

    @classmethod
    def load_config(cls) -> dict:
        default_data = {
            "valorant_path": "",
            "default_stretched": {"x": 1280, "y": 960},
            "exit_res": {"x": 1920, "y": 1080},
            "aggressive_mode": True,
            "monitor_toggle_enabled": False,
            "auto_high_priority": True,
            "true_stretched": True,
            "ui_font_scale": 14,
            "ui_anim_speed": 1.0,
            "btn_anim_style": "Sink",
            "accent_color": "#FF4655",
            "transition_style": "Smooth Slide",
            "vibrance_auto": False,
            "womic_auto": False,
            "ui_theme_preset": "Elite Cyber",
            "layout_style": "Elite Hybrid"
        }
        if os.path.exists(cls.CONFIG_FILE):
            try:
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, val in data.items():
                        if isinstance(val, dict) and key in default_data:
                            default_data[key].update(val)
                        else:
                            default_data[key] = val
                
                # Sanitize configuration parameters to guarantee safe runtime types
                default_data["default_stretched"]["x"] = int(default_data["default_stretched"].get("x", 1280))
                default_data["default_stretched"]["y"] = int(default_data["default_stretched"].get("y", 960))
                default_data["exit_res"]["x"] = int(default_data["exit_res"].get("x", 1920))
                default_data["exit_res"]["y"] = int(default_data["exit_res"].get("y", 1080))
                default_data["ui_font_scale"] = int(default_data.get("ui_font_scale", 14))
                default_data["ui_anim_speed"] = float(default_data.get("ui_anim_speed", 1.0))
            except Exception: pass
        return default_data

    @classmethod
    def save_config(cls, data: dict):
        with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    @classmethod
    def write_file_log(cls, msg: str, tag: str):
        if tag.lower() != "err":
            return
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            # Ensure the target log directory exists before writing
            os.makedirs(os.path.dirname(cls.LOG_FILE), exist_ok=True)
            with open(cls.LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(f"[{ts}] [ERROR] {msg}\n")
        except Exception: pass
    
    @classmethod
    def apply_qres(cls, width: int, height: int) -> bool:
        possible_paths = [
            os.path.join(_MEIPASS, "bin", "QRes.exe"),
            os.path.join(_MEIPASS, "bin", "qres.exe"),
            os.path.join(_BASE_DIR, "bin", "QRes.exe"),
            os.path.join(_BASE_DIR, "bin", "qres.exe"),
            shutil.which("QRes.exe"),
            shutil.which("qres.exe")
        ]
        qres_path = next((p for p in possible_paths if p and os.path.exists(p)), None)
        if not qres_path: return False
        try:
            args = [qres_path, f"/x:{width}", f"/y:{height}"]
            result = subprocess.run(args, capture_output=True, creationflags=WinAPI.CREATE_NO_WINDOW)
            return result.returncode == 0
        except Exception: pass
        return False

class WinAPI:
    CREATE_NO_WINDOW = 0x08000000

    @staticmethod
    def is_admin() -> bool:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

    @staticmethod
    def is_laptop() -> bool:
        try:
            battery = psutil.sensors_battery()
            return battery is not None
        except: return False

    @staticmethod
    def is_resolution_supported(width: int, height: int) -> bool:
        try:
            import win32api
            i = 0
            while True:
                try:
                    devmode = win32api.EnumDisplaySettings(None, i)
                    if devmode.PelsWidth == width and devmode.PelsHeight == height:
                        return True
                    i += 1
                except Exception: break
            return False
        except Exception: return True

    @staticmethod
    def force_resolution(width: int, height: int, permanent: bool = False) -> bool:
        try:
            import win32api, win32con
            devmode = win32api.EnumDisplaySettings(None, win32con.ENUM_CURRENT_SETTINGS)
            devmode.PelsWidth, devmode.PelsHeight = width, height
            devmode.Fields = win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT
            flags = win32con.CDS_UPDATEREGISTRY if permanent else 0
            res = win32api.ChangeDisplaySettings(devmode, flags)
            return res == win32con.DISP_CHANGE_SUCCESSFUL
        except Exception: return False

    @staticmethod
    def is_taskbar_auto_hide_enabled() -> bool:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\StuckRects3") as key:
                value, _ = winreg.QueryValueEx(key, "Settings")
                return value[8] == 3
        except Exception:
            return False

    @staticmethod
    def toggle_taskbar(hide: bool):
        if hide:
            is_currently_hidden = WinAPI.is_taskbar_auto_hide_enabled()
            AppState.was_taskbar_hidden_by_default = is_currently_hidden
            if not is_currently_hidden:
                abd = type("APPBARDATA", (ctypes.Structure,), {
                    "_fields_": [
                        ("cbSize", wintypes.DWORD), 
                        ("hWnd", wintypes.HWND), 
                        ("uCallbackMessage", wintypes.UINT), 
                        ("uEdge", wintypes.UINT), 
                        ("rc", wintypes.RECT), 
                        ("lParam", wintypes.LPARAM)
                    ]
                })()
                abd.cbSize = ctypes.sizeof(abd)
                abd.hWnd = ctypes.windll.user32.FindWindowW(u"Shell_TrayWnd", None)
                if abd.hWnd:
                    abd.lParam = 1 
                    ctypes.windll.shell32.SHAppBarMessage(10, ctypes.byref(abd))
        else:
            if AppState.was_taskbar_hidden_by_default is False:
                is_currently_hidden = WinAPI.is_taskbar_auto_hide_enabled()
                if is_currently_hidden:
                    abd = type("APPBARDATA", (ctypes.Structure,), {
                        "_fields_": [
                            ("cbSize", wintypes.DWORD), 
                            ("hWnd", wintypes.HWND), 
                            ("uCallbackMessage", wintypes.UINT), 
                            ("uEdge", wintypes.UINT), 
                            ("rc", wintypes.RECT), 
                            ("lParam", wintypes.LPARAM)
                        ]
                    })()
                    abd.cbSize = ctypes.sizeof(abd)
                    abd.hWnd = ctypes.windll.user32.FindWindowW(u"Shell_TrayWnd", None)
                    if abd.hWnd:
                        abd.lParam = 2
                        ctypes.windll.shell32.SHAppBarMessage(10, ctypes.byref(abd))

    @staticmethod
    def pulse_pnp_monitor():
        cmd = "Get-PnpDevice -Class Monitor -Status OK | Select-Object -First 1 | Disable-PnpDevice -Confirm:$false; Start-Sleep -s 1; Get-PnpDevice -Class Monitor -Status OK | Select-Object -First 1 | Enable-PnpDevice -Confirm:$false"
        subprocess.run(["powershell", "-Command", cmd], creationflags=WinAPI.CREATE_NO_WINDOW)

    @staticmethod
    def patch_game_config(x: int, y: int):
        path = os.path.join(os.getenv('LOCALAPPDATA', ''), "VALORANT", "Saved", "Config")
        if not os.path.exists(path): return
        for root, _, files in os.walk(path):
            if "GameUserSettings.ini" in files:
                fpath = os.path.join(root, "GameUserSettings.ini")
                try:
                    os.chmod(fpath, 0o666)
                    with open(fpath, 'r', encoding='utf-8') as f: 
                        lines = f.readlines()
                    
                    changes_needed = False
                    has_x = False
                    has_y = False
                    has_mode = False
                    
                    for line in lines:
                        if line.startswith("ResolutionSizeX=") and f"ResolutionSizeX={x}" not in line: changes_needed = True
                        if line.startswith("ResolutionSizeY=") and f"ResolutionSizeY={y}" not in line: changes_needed = True
                        if line.startswith("FullscreenMode=") and "FullscreenMode=2" not in line: changes_needed = True
                        
                    if changes_needed or not lines:
                        new_lines = []
                        for line in lines:
                            if line.startswith("ResolutionSizeX="):
                                new_lines.append(f"ResolutionSizeX={x}\n")
                                has_x = True
                            elif line.startswith("ResolutionSizeY="):
                                new_lines.append(f"ResolutionSizeY={y}\n")
                                has_y = True
                            elif line.startswith("FullscreenMode="):
                                new_lines.append("FullscreenMode=2\n")
                                has_mode = True
                            else:
                                new_lines.append(line)
                                
                        if not has_x: new_lines.append(f"ResolutionSizeX={x}\n")
                        if not has_y: new_lines.append(f"ResolutionSizeY={y}\n")
                        if not has_mode: new_lines.append("FullscreenMode=2\n")
                        
                        with open(fpath, 'w', encoding='utf-8') as f:
                            f.writelines(new_lines)
                            
                    os.chmod(fpath, 0o444)
                except Exception: pass

    @staticmethod
    def kill_game():
        # Avoid shell=True to prevent command injection vulnerabilities; use argument lists instead
        subprocess.run(["taskkill", "/f", "/im", "VALORANT-Win64-Shipping.exe"], capture_output=True, creationflags=WinAPI.CREATE_NO_WINDOW)
        subprocess.run(["taskkill", "/f", "/im", "RiotClientServices.exe"], capture_output=True, creationflags=WinAPI.CREATE_NO_WINDOW)

    @staticmethod
    def is_process_running(process_name):
        for proc in psutil.process_iter(['name']):
            try:
                if process_name.lower() in proc.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess): pass
        return False

    @staticmethod
    def launch_vibrance():
        if WinAPI.is_process_running("vibranceGUI.exe"):
            return "running"
        v_path = os.path.join(_MEIPASS, "bin", "vibranceGUI.exe")
        if not os.path.exists(v_path):
            v_path = os.path.join(_BASE_DIR, "bin", "vibranceGUI.exe")
        if os.path.exists(v_path):
            # Avoid shell=True to prevent argument injection
            subprocess.Popen([v_path])
            return "launched"
        return "missing"

    @staticmethod
    def _find_womic_exe():
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\WO Mic")
            install_loc, _ = winreg.QueryValueEx(key, "InstallLocation")
            exe_path = os.path.join(install_loc, "WOMicClient.exe")
            if os.path.exists(exe_path): return exe_path
        except Exception: pass

        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\WO Mic")
            install_loc, _ = winreg.QueryValueEx(key, "InstallLocation")
            exe_path = os.path.join(install_loc, "WOMicClient.exe")
            if os.path.exists(exe_path): return exe_path
        except Exception: pass

        drives = [p.device for p in psutil.disk_partitions() if 'cdrom' not in p.opts and p.fstype != '']
        for drive in drives:
            paths = [
                os.path.join(drive, r"Program Files (x86)\WOMic\WOMicClient.exe"),
                os.path.join(drive, r"Program Files\WOMic\WOMicClient.exe"),
                os.path.join(drive, r"WOMic\WOMicClient.exe")
            ]
            for p in paths:
                if os.path.exists(p): return p
        return None

    @staticmethod
    def handle_womic():
        if WinAPI.is_process_running("WOMicClient.exe"):
            return "running"
            
        womic_exe = WinAPI._find_womic_exe()
        if not womic_exe:
            installer_path = os.path.join(_MEIPASS, "bin", "womic_installer.exe")
            if not os.path.exists(installer_path):
                installer_path = os.path.join(_BASE_DIR, "bin", "womic_installer.exe")
            if os.path.exists(installer_path):
                # Avoid shell=True to prevent command execution hijack
                subprocess.run([installer_path, "/S"], creationflags=WinAPI.CREATE_NO_WINDOW)
                time.sleep(5)
                womic_exe = WinAPI._find_womic_exe()
        
        if womic_exe:
            # Avoid shell=True to run the WOMic client executable safely
            subprocess.Popen([womic_exe])
            return "launched"
        return "missing"

    @staticmethod
    def get_riot_client_path_dynamic():
        possible_keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Riot Games\Riot Client"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Riot Games\Riot Client")
        ]
        for hive, key in possible_keys:
            try:
                with winreg.OpenKey(hive, key) as reg_key:
                    install_folder, _ = winreg.QueryValueEx(reg_key, "InstallFolder")
                candidate = os.path.join(install_folder, "RiotClientServices.exe")
                if os.path.exists(candidate): return candidate
            except Exception: pass

        drives = [p.device for p in psutil.disk_partitions() if 'cdrom' not in p.opts and p.fstype != '']
        cyber_paths = [
            r"Riot Games\Riot Client\RiotClientServices.exe",
            r"Online Games\Valorant\Riot Games\Riot Client\RiotClientServices.exe",
            r"Games\Valorant\Riot Games\Riot Client\RiotClientServices.exe",
            r"Game\Valorant\Riot Games\Riot Client\RiotClientServices.exe",
            r"Valorant\Riot Games\Riot Client\RiotClientServices.exe",
            r"Program Files\Riot Games\Riot Client\RiotClientServices.exe",
            r"Program Files (x86)\Riot Games\Riot Client\RiotClientServices.exe"
        ]
        for drive in drives:
            for c_path in cyber_paths:
                full_check_path = os.path.join(drive, c_path)
                if os.path.exists(full_check_path): return full_check_path
        return None

class EaseAnim:
    @staticmethod
    def ease_out_quint(t): return 1 - pow(1 - t, 5)
    @staticmethod
    def ease_out_back(t): 
        c1 = 1.70158; c3 = c1 + 1
        return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)
    @staticmethod
    def ease_out_elastic(t):
        c4 = (2 * math.pi) / 3
        if t == 0: return 0
        if t == 1: return 1
        return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1
    @staticmethod
    def lerp(start, end, t):
        return start + (end - start) * t

def interpolate_color(color1, color2, t):
    try:
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return color2

class PulsingDot(ctk.CTkCanvas):
    def __init__(self, master, color="#10B981", size=16, **kwargs):
        super().__init__(master, width=size, height=size, bg="#121214", highlightthickness=0, **kwargs)
        self.color = color
        self.size = size
        self.pulse_val = 0.0
        self.pulse_dir = 1
        self.anim_active = True
        self._animate()

    def set_color(self, color):
        self.color = color

    def _animate(self):
        if not self.anim_active: return
        self.delete("all")
        
        center = self.size / 2
        glow_r = center * (0.4 + 0.6 * self.pulse_val)
        
        bg_col = self.master.cget("fg_color") if hasattr(self.master, "cget") else "#121214"
        if not bg_col or bg_col == "transparent":
            bg_col = "#121214"
        glow_color = interpolate_color(bg_col, self.color, self.pulse_val * 0.45)
        
        self.create_oval(center - glow_r, center - glow_r, center + glow_r, center + glow_r, fill=glow_color, outline="")
        self.create_oval(center - 4, center - 4, center + 4, center + 4, fill=self.color, outline="")
        
        self.pulse_val += 0.04 * self.pulse_dir
        if self.pulse_val >= 1.0:
            self.pulse_val = 1.0
            self.pulse_dir = -1
        elif self.pulse_val <= 0.0:
            self.pulse_val = 0.0
            self.pulse_dir = 1
            
        self.after(40, self._animate)

class SmoothFocusEntry(ctk.CTkEntry):
    def __init__(self, master, accent_color="#FF4655", **kwargs):
        self.default_border = "#1E1E24"
        self.accent_border = accent_color
        super().__init__(master, border_color=self.default_border, border_width=1, **kwargs)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self._anim_task = None
        self.progress = 0.0

    def update_accent_color(self, new_color):
        self.accent_border = new_color
        if self.focus_get() == self:
            self.configure(border_color=new_color)

    def _on_focus_in(self, event):
        self._animate_border(True)

    def _on_focus_out(self, event):
        self._animate_border(False)

    def _animate_border(self, focus_in):
        if self._anim_task:
            self.after_cancel(self._anim_task)
            self._anim_task = None
            
        target = 1.0 if focus_in else 0.0
        step = 0.15
        
        if abs(self.progress - target) < 0.01:
            self.progress = target
            current_color = self.accent_border if focus_in else self.default_border
            self.configure(border_color=current_color)
            return
            
        if self.progress < target:
            self.progress = min(1.0, self.progress + step)
        else:
            self.progress = max(0.0, self.progress - step)
            
        current_color = interpolate_color(self.default_border, self.accent_border, self.progress)
        self.configure(border_color=current_color)
        
        self._anim_task = self.after(16, self._animate_border, focus_in)

class AnimatedButton(ctk.CTkFrame):
    def __init__(self, master, text, font, config_ref, command=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.command = command
        self.cfg = config_ref
        self.accent = self.cfg["accent_color"]
        self.btn = ctk.CTkButton(
            self, text=text, fg_color=self.accent, hover_color=self._get_hover_color(),
            text_color="#FFFFFF", font=font, corner_radius=6, border_width=0
        )
        self.btn.pack(fill="both", expand=True, pady=(0, 6))
        self.btn.bind("<Button-1>", self._on_press)
        self.btn.bind("<ButtonRelease-1>", self._on_release)
        self.btn.bind("<Leave>", self._on_leave)
        self.is_pressed = False

    def _get_hover_color(self):
        try: return "#%02x%02x%02x" % tuple(max(0, int(self.accent[i:i+2], 16) - 30) for i in (1, 3, 5))
        except: return "#D82A3A"

    def _on_press(self, event):
        self.is_pressed = True
        style = self.cfg["btn_anim_style"]
        if style == "Sink": self.btn.pack_configure(pady=(6, 0)) 
        elif style == "Color Pulse": self.btn.configure(fg_color="#FFFFFF", text_color=self.accent)

    def _on_release(self, event):
        if self.is_pressed:
            self.is_pressed = False
            self.btn.pack_configure(pady=(0, 6))
            self.btn.configure(fg_color=self.accent, text_color="#FFFFFF")
            if self.command: self.after(10, self.command)

    def _on_leave(self, event):
        if self.is_pressed:
            self.is_pressed = False
            self.btn.pack_configure(pady=(0, 6))
            self.btn.configure(fg_color=self.accent, text_color="#FFFFFF")

    def update_state(self, text, fg_color=None):
        if fg_color: self.accent = fg_color
        self.btn.configure(text=text, fg_color=self.accent, hover_color=self._get_hover_color())

class AppState:
    tool_active = True
    game_running = False
    was_taskbar_hidden_by_default = None

class UltimateUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        if not WinAPI.is_admin():
            messagebox.showerror("System Error", "Admin Privileges Required!")
            sys.exit()

        self.cfg = AppManager.load_config()
        self.game_running = False
        self.abort_requested = False
        self._save_timer = None       
        self._font_debounce = None
        self._anim_task = None
        self._typing_timer = None
        self._about_anim_task = None
        self.log_queue = []
        self.is_logging = False
        self.util_switches = []
        self.switches = {}
        self.switch_cells = {}
        self.cards = []
        self.current_tab = "home"

        self.title("VALORANT CORE")
        self.geometry("950x600")
        self.resizable(False, False)
        self.configure(fg_color="#09090C")
        
        # Load window icon bitmap from the assets folder
        icon_path = os.path.join(_MEIPASS, "assets", "valorant_logo.ico")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(_BASE_DIR, "assets", "valorant_logo.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception: pass
        
        self.protocol("WM_DELETE_WINDOW", self.on_force_exit)
        atexit.register(self.on_force_exit)

        self._init_fonts()
        self._build_ui()
        
        # Apply dynamic visual theme preset on startup
        initial_theme = self.cfg.get("ui_theme_preset", "Elite Cyber")
        self._apply_theme_style(initial_theme)
        
        # Apply structural UI layout on startup
        initial_layout = self.cfg.get("layout_style", "Elite Hybrid")
        self._repack_layouts(initial_layout)
        self._highlight_style_box(initial_layout)
        self._log("System Online. Elite Hybrid Architecture Operational.", "sys")
        self._update_diagnostics()

    def _init_fonts(self):
        bs = self.cfg["ui_font_scale"]
        self.f_h1 = ctk.CTkFont("Segoe UI", 28, "bold")
        self.f_h2 = ctk.CTkFont("Segoe UI", bs + 2, "bold")
        self.f_p = ctk.CTkFont("Segoe UI", bs)
        self.f_bold_p = ctk.CTkFont("Segoe UI", bs, "bold")
        self.f_btn = ctk.CTkFont("Segoe UI", bs + 3, "bold")
        self.f_mono = ctk.CTkFont("Consolas", bs - 2)

    def _build_ui(self):
        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(1, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color="#121214", border_width=1, border_color="#1E1E24")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)
        
        self.lbl_logo = ctk.CTkLabel(self.sidebar, text="VAL-CORE", font=self.f_h1, text_color=self.cfg["accent_color"])
        self.lbl_logo.pack(pady=(45, 2))
        self.lbl_sub_logo = ctk.CTkLabel(self.sidebar, text="H Y B R I D   E D I T I O N", font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"), text_color="#71717A")
        self.lbl_sub_logo.pack(pady=(0, 30))
 
        self.tab_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.tab_container.pack(fill="x", padx=10, pady=10)
        
        self.tab_indicator = ctk.CTkFrame(self.tab_container, width=4, corner_radius=2, fg_color=self.cfg["accent_color"])
        
        self.tabs = {}
        tab_list = [("home", "⯁  Dashboard"), ("engine", "⯁  Core Engine"), ("settings", "⯁  Settings"), ("about", "⯁  About")]
        for name, text in tab_list:
            btn = ctk.CTkButton(self.tab_container, text=text, fg_color="transparent", hover_color="#1E1E24", 
                                anchor="w", font=self.f_h2, text_color="#8A8A93", corner_radius=8,
                                command=lambda n=name: self._switch_tab(n))
            btn.pack(fill="x", padx=(15, 10), pady=6, ipady=6)
            self.tabs[name] = btn
 
        # Permanent, fixed bottom Action Bar at the very bottom of the main window
        self.bottom_action_bar = ctk.CTkFrame(self, fg_color="transparent")
 
        self.btn_play = AnimatedButton(self.bottom_action_bar, "▶ INJECT GAME", self.f_btn, self.cfg, self.handle_action_button, height=55)
        self.btn_play.pack(side="left", fill="x", expand=True, padx=(0, 20))
 
        self.status_container = ctk.CTkFrame(self.bottom_action_bar, fg_color="transparent")
        self.status_container.pack(side="right")
        
        self.status_dot = PulsingDot(self.status_container, color="#10B981", size=16)
        self.status_dot.pack(side="left", padx=(0, 6))
        
        self.lbl_status = ctk.CTkLabel(self.status_container, text="SYSTEM READY", text_color="#10B981", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"))
        self.lbl_status.pack(side="left")
 
        self.container = ctk.CTkFrame(self, fg_color="#09090C", corner_radius=0)
        self.container.grid(row=0, column=1, sticky="nsew")
        self.panels = {}
        
        # Create all_in_one panel container and scrollable grid structure
        self.panels["all_in_one"] = ctk.CTkFrame(self.container, fg_color="transparent", corner_radius=0)
        p_all = self.panels["all_in_one"]
        
        self.aio_scroll_frame = ctk.CTkScrollableFrame(p_all, fg_color="#09090C")
        self.aio_scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.aio_scroll_frame.grid_columnconfigure(0, weight=1, uniform="aio_col")
        self.aio_scroll_frame.grid_columnconfigure(1, weight=1, uniform="aio_col")
        
        # Force synchronous repaint on every scroll tick to prevent GDI ghosting
        if hasattr(self.aio_scroll_frame, "_parent_frame"):
            self.aio_scroll_frame._parent_frame.bind("<Configure>", lambda e: self.update_idletasks(), add="+")

        # Install 120 FPS LERP smooth scroll engine
        self._setup_smooth_scroll()

        self._build_home_panel()
        self._build_engine_panel()
        self._build_settings_panel()
        self._build_about_panel()

    def update_status(self, text, color):
        self.lbl_status.configure(text=text, text_color=color)
        self.status_dot.set_color(color)

    def _build_home_panel(self):
        p_home = ctk.CTkFrame(self.container, fg_color="transparent", corner_radius=0)
        
        self.home_top_grid = ctk.CTkFrame(p_home, fg_color="transparent")
        self.home_top_grid.pack(fill="x", padx=20, pady=15)
        self.home_top_grid.grid_columnconfigure(0, weight=1, uniform="col")
        self.home_top_grid.grid_columnconfigure(1, weight=1, uniform="col")
        
        self.res_card = ctk.CTkFrame(self.container, fg_color="#111115", corner_radius=12, border_width=1, border_color="#1E1E24")
        self.cards.append(self.res_card)
        
        ctk.CTkLabel(self.res_card, text="STRETCHED RESOLUTION", font=self.f_h2, text_color="#FAFAFA").pack(pady=(15, 10))
        
        inputs_frame = ctk.CTkFrame(self.res_card, fg_color="transparent")
        inputs_frame.pack(pady=5)
        
        self.ent_x = SmoothFocusEntry(inputs_frame, accent_color=self.cfg["accent_color"], width=100, height=45, font=ctk.CTkFont("Segoe UI", 22, "bold"), justify="center", fg_color="#08080C")
        self.ent_x.pack(side="left")
        self.ent_x.insert(0, str(self.cfg["default_stretched"]["x"]))
        self.ent_x.bind("<KeyRelease>", self._schedule_save)
 
        x_lbl = ctk.CTkLabel(inputs_frame, text="×", font=ctk.CTkFont("Segoe UI", 20, "bold"), text_color="#4F4F56")
        x_lbl.pack(side="left", padx=15)
 
        self.ent_y = SmoothFocusEntry(inputs_frame, accent_color=self.cfg["accent_color"], width=100, height=45, font=ctk.CTkFont("Segoe UI", 22, "bold"), justify="center", fg_color="#08080C")
        self.ent_y.pack(side="left")
        self.ent_y.insert(0, str(self.cfg["default_stretched"]["y"]))
        self.ent_y.bind("<KeyRelease>", self._schedule_save)
        
        preset_frame = ctk.CTkFrame(self.res_card, fg_color="transparent")
        preset_frame.pack(pady=(10, 15))
        presets = [("1280×960", 1280, 960), ("1024×768", 1024, 768), ("1440×1080", 1440, 1080), ("1600×1024", 1600, 1024)]
        for label, rx, ry in presets:
            btn = ctk.CTkButton(preset_frame, text=label, width=70, height=28, font=ctk.CTkFont("Segoe UI", 10, "bold"), fg_color="#1E1E24", hover_color="#2E2E38", text_color="#D1D1D6", corner_radius=6, command=lambda x=rx, y=ry: self._apply_preset(x, y))
            btn.pack(side="left", padx=3)
            
        self.diag_card = ctk.CTkFrame(self.container, fg_color="#111115", corner_radius=12, border_width=1, border_color="#1E1E24")
        self.cards.append(self.diag_card)
        
        ctk.CTkLabel(self.diag_card, text="SYSTEM DIAGNOSTICS", font=self.f_h2, text_color="#FAFAFA").pack(pady=(15, 10))
        
        diag_inner = ctk.CTkFrame(self.diag_card, fg_color="transparent")
        diag_inner.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        diag_inner.grid_columnconfigure(0, weight=1)
        diag_inner.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(diag_inner, text="Privilege Level:", font=ctk.CTkFont("Segoe UI", 11), text_color="#71717A").grid(row=0, column=0, sticky="w", pady=4)
        self.lbl_diag_priv = ctk.CTkLabel(diag_inner, text="ADMINISTRATOR", font=ctk.CTkFont("Segoe UI", 11, "bold"), text_color="#10B981")
        self.lbl_diag_priv.grid(row=0, column=1, sticky="e", pady=4)
        
        ctk.CTkLabel(diag_inner, text="GPU Active Res:", font=ctk.CTkFont("Segoe UI", 11), text_color="#71717A").grid(row=1, column=0, sticky="w", pady=4)
        self.lbl_diag_res = ctk.CTkLabel(diag_inner, text="1920 × 1080", font=ctk.CTkFont("Segoe UI", 11, "bold"), text_color="#D1D1D6")
        self.lbl_diag_res.grid(row=1, column=1, sticky="e", pady=4)
        
        ctk.CTkLabel(diag_inner, text="Riot Connection:", font=ctk.CTkFont("Segoe UI", 11), text_color="#71717A").grid(row=2, column=0, sticky="w", pady=4)
        self.lbl_diag_path = ctk.CTkLabel(diag_inner, text="CHECKING...", font=ctk.CTkFont("Segoe UI", 11, "bold"), text_color="#F59E0B")
        self.lbl_diag_path.grid(row=2, column=1, sticky="e", pady=4)
        
        ctk.CTkLabel(diag_inner, text="Utilities Launch:", font=ctk.CTkFont("Segoe UI", 11), text_color="#71717A").grid(row=3, column=0, sticky="w", pady=4)
        self.lbl_diag_utils = ctk.CTkLabel(diag_inner, text="Vib: OFF | Mic: OFF", font=ctk.CTkFont("Segoe UI", 11, "bold"), text_color="#A1A1AA")
        self.lbl_diag_utils.grid(row=3, column=1, sticky="e", pady=4)
 
        self.log_card = ctk.CTkFrame(self.container, fg_color="#08080A", corner_radius=12, border_width=1, border_color="#1E1E24")
        self.cards.append(self.log_card)
        
        self.log_area = tk.Text(self.log_card, bg="#08080A", fg="#D1D1D6", font=self.f_mono, bd=0, state="disabled", highlightthickness=0, padx=12, pady=12)
        self.log_area.pack(side="left", fill="both", expand=True, padx=(15, 0), pady=15)
        
        scrollbar = ctk.CTkScrollbar(self.log_card, command=self.log_area.yview)
        scrollbar.pack(side="right", fill="y", padx=(5, 15), pady=15)
        self.log_area.configure(yscrollcommand=scrollbar.set)
        
        for t, c in [("sys", "#38BDF8"), ("ok", "#10B981"), ("err", "#EF4444"), ("hype", "#FF4655")]:
            self.log_area.tag_configure(t, foreground=c)
            
        self.panels["home"] = p_home

    def _get_current_display_res(self):
        try:
            import win32api, win32con
            devmode = win32api.EnumDisplaySettings(None, win32con.ENUM_CURRENT_SETTINGS)
            return f"{devmode.PelsWidth} × {devmode.PelsHeight}"
        except Exception:
            return "Unknown"

    def _update_diagnostics(self):
        current_res = self._get_current_display_res()
        self.lbl_diag_res.configure(text=current_res)
        
        path_valid = os.path.exists(self.cfg.get("valorant_path", ""))
        if path_valid:
            self.lbl_diag_path.configure(text="CONNECTED", text_color="#10B981")
        else:
            self.lbl_diag_path.configure(text="AUTO-SEARCH", text_color="#F59E0B")
            
        v_status = "ON" if self.var_vib.get() else "OFF"
        w_status = "ON" if self.var_mic.get() else "OFF"
        self.lbl_diag_utils.configure(text=f"Vib: {v_status} | Mic: {w_status}")
        
        self.after(4000, self._update_diagnostics)

    def _apply_preset(self, x, y):
        self.ent_x.delete(0, tk.END)
        self.ent_x.insert(0, str(x))
        self.ent_y.delete(0, tk.END)
        self.ent_y.insert(0, str(y))
        self._log(f"Preset override configured: {x}x{y}", "sys")
        self._instant_save()

    def _build_engine_panel(self):
        p_engine = ctk.CTkFrame(self.container, fg_color="transparent", corner_radius=0)
        
        self.path_card = ctk.CTkFrame(self.container, fg_color="#111115", corner_radius=12, border_width=1, border_color="#1E1E24")
        self.cards.append(self.path_card)
        
        ctk.CTkLabel(self.path_card, text="VALORANT RUNTIME PATH", font=self.f_h2, text_color="#FAFAFA").pack(anchor="w", padx=20, pady=(15, 8))
        
        row_path = ctk.CTkFrame(self.path_card, fg_color="transparent")
        row_path.pack(fill="x", padx=20, pady=(0, 15))
        
        self.ent_path = SmoothFocusEntry(row_path, accent_color=self.cfg["accent_color"], fg_color="#08080C", height=40, font=self.f_p)
        self.ent_path.insert(0, self.cfg["valorant_path"] or "Hybrid Universal Deployment Mode (Auto-Search)")
        self.ent_path.configure(state="readonly")
        self.ent_path.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.btn_browse = ctk.CTkButton(row_path, text="Browse", width=90, height=40, font=ctk.CTkFont("Segoe UI", 12, "bold"), fg_color="#1E1E24", hover_color="#2E2E38", text_color="#FAFAFA", command=self._browse_path)
        self.btn_browse.pack(side="left")
 
        self.overrides_card = ctk.CTkFrame(self.container, fg_color="#111115", corner_radius=12, border_width=1, border_color="#1E1E24")
        self.cards.append(self.overrides_card)
        
        ctk.CTkLabel(self.overrides_card, text="RUNTIME OVERRIDES", font=self.f_h2, text_color="#FAFAFA").pack(anchor="w", padx=20, pady=(15, 10))
        
        grid_frame = ctk.CTkFrame(self.overrides_card, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        grid_frame.grid_columnconfigure(0, weight=1, uniform="grid_col")
        grid_frame.grid_columnconfigure(1, weight=1, uniform="grid_col")
        grid_frame.grid_rowconfigure(0, weight=1)
        grid_frame.grid_rowconfigure(1, weight=1)
        
        switch_specs = [
            ("true_stretched", "True Stretched Mode", "Forces hardware display configuration to match custom resolution.", self.cfg["true_stretched"], 0, 0),
            ("aggro_mode", "Aggressive Mode", "Forces Windows Taskbar auto-hide to prevent window overlapping.", self.cfg["aggressive_mode"], 0, 1),
            ("pnp_toggle", "Monitor Pulse", "Cycles display state dynamically to bypass Windows 11 black bars.", self.cfg["monitor_toggle_enabled"], 1, 0),
            ("fps_boost", "CPU Priority Booster", "Elevates Valorant priority class for improved frame stability.", self.cfg["auto_high_priority"], 1, 1)
        ]
        
        self.switches = {}
        self.switch_cells = {}
        for key, title, desc, val, r, c in switch_specs:
            cell = ctk.CTkFrame(grid_frame, fg_color="transparent")
            cell.grid(row=r, column=c, padx=10, pady=8, sticky="nsew")
            
            var = tk.BooleanVar(value=val)
            sw = ctk.CTkSwitch(cell, text=title, variable=var, command=self._schedule_save, progress_color=self.cfg["accent_color"], font=self.f_h2)
            sw.pack(anchor="w")
            
            lbl_desc = ctk.CTkLabel(cell, text=desc, font=ctk.CTkFont("Segoe UI", 11), text_color="#71717A", justify="left", anchor="w", wraplength=235)
            lbl_desc.pack(anchor="w", padx=(30, 10), pady=(2, 0))
            
            self.switches[key] = sw
            self.switch_cells[key] = cell
            
        self.panels["engine"] = p_engine

    def _build_settings_panel(self):
        p_set = ctk.CTkFrame(self.container, fg_color="transparent", corner_radius=0)
        
        # Select UI Layout Architecture selector card
        self.layout_card = ctk.CTkFrame(self.container, fg_color="#111115", corner_radius=12, border_width=1, border_color="#1E1E24")
        self.cards.append(self.layout_card)
        
        ctk.CTkLabel(self.layout_card, text="SELECT UI LAYOUT ARCHITECTURE", font=self.f_h2, text_color="#FAFAFA").pack(anchor="w", padx=20, pady=(10, 5))
        
        style_box_container = ctk.CTkFrame(self.layout_card, fg_color="transparent")
        style_box_container.pack(fill="x", padx=20, pady=(0, 10))
        
        style_box_container.grid_columnconfigure(0, weight=1, uniform="layout_col")
        style_box_container.grid_columnconfigure(1, weight=1, uniform="layout_col")
        style_box_container.grid_columnconfigure(2, weight=1, uniform="layout_col")
        style_box_container.grid_columnconfigure(3, weight=1, uniform="layout_col")
        
        style_specs = [
            ("Elite Hybrid", "Elite Hybrid", "Sidebar left, tabs right."),
            ("Top Nav Minimal", "Top Nav Minimal", "Sidebar at top, center view."),
            ("All-in-One Dashboard", "All-in-One", "Unified screen scrollable grid."),
            ("Glassmorphism Floating", "Glassmorphic Glow", "Floating windows layout.")
        ]
        
        self.style_boxes = {}
        for idx, (code_name, title, tooltip) in enumerate(style_specs):
            box = ctk.CTkFrame(style_box_container, fg_color="#1E1E24", border_width=1, border_color="#2E2E38", corner_radius=8, cursor="hand2")
            box.grid(row=0, column=idx, padx=5, sticky="nsew", ipady=8)
            
            canvas = ctk.CTkCanvas(box, width=60, height=35, bg="#1E1E24", highlightthickness=0)
            canvas.pack(pady=(8, 4))
            
            self._draw_layout_preview(canvas, code_name)
            
            lbl_title = ctk.CTkLabel(box, text=title, font=ctk.CTkFont("Segoe UI", 10, "bold"), text_color="#FAFAFA")
            lbl_title.pack(pady=(0, 2))
            
            lbl_tip = ctk.CTkLabel(box, text=tooltip, font=ctk.CTkFont("Segoe UI", 8), text_color="#71717A", wraplength=120, justify="center")
            lbl_tip.pack()
            
            for w in [box, canvas, lbl_title, lbl_tip]:
                w.bind("<Button-1>", lambda e, name=code_name: self._change_ui_layout(name))
                
            self.style_boxes[code_name] = box

        self.utils_card = ctk.CTkFrame(self.container, fg_color="#111115", corner_radius=12, border_width=1, border_color="#1E1E24")
        self.cards.append(self.utils_card)
        
        ctk.CTkLabel(self.utils_card, text="INTEGRATED UTILITIES", font=self.f_h2, text_color="#FAFAFA").pack(anchor="w", padx=20, pady=(10, 5))
        
        u_row = ctk.CTkFrame(self.utils_card, fg_color="transparent")
        u_row.pack(fill="x", padx=20, pady=(0, 10))
        
        self.var_vib = tk.BooleanVar(value=self.cfg.get("vibrance_auto", False))
        self.sw_vib = ctk.CTkSwitch(u_row, text="Auto-Launch VibranceGUI", variable=self.var_vib, command=self._schedule_save, progress_color=self.cfg["accent_color"], font=self.f_h2)
        if WinAPI.is_laptop():
            self.sw_vib.configure(state="disabled", text="VibranceGUI (Laptop detected - Disabled)")
            self.var_vib.set(False)
        self.sw_vib.pack(side="left", padx=(0, 30))
 
        self.var_mic = tk.BooleanVar(value=self.cfg.get("womic_auto", False))
        self.sw_mic = ctk.CTkSwitch(u_row, text="Auto-Launch WO Mic Client", variable=self.var_mic, command=self._schedule_save, progress_color=self.cfg["accent_color"], font=self.f_h2)
        self.sw_mic.pack(side="left")
        
        self.util_switches.clear()
        self.util_switches.extend([self.sw_vib, self.sw_mic])
 
        self.style_card = ctk.CTkFrame(self.container, fg_color="#111115", corner_radius=12, border_width=1, border_color="#1E1E24")
        self.cards.append(self.style_card)
        
        ctk.CTkLabel(self.style_card, text="LAUNCHER AESTHETICS", font=self.f_h2, text_color="#FAFAFA").pack(anchor="w", padx=20, pady=(10, 5))
        
        style_inner = ctk.CTkFrame(self.style_card, fg_color="transparent")
        style_inner.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        style_inner.grid_columnconfigure(0, weight=1, uniform="style_col")
        style_inner.grid_columnconfigure(1, weight=1, uniform="style_col")
        
        self.style_left_side = ctk.CTkFrame(style_inner, fg_color="transparent")
        self.style_left_side.grid(row=0, column=0, padx=(0, 15), sticky="nsew")
        
        th_row = ctk.CTkFrame(self.style_left_side, fg_color="transparent")
        th_row.pack(fill="x", pady=2)
        ctk.CTkLabel(th_row, text="UI Style Theme:", font=self.f_bold_p, width=140, anchor="w").pack(side="left")
        self.opt_theme = ctk.CTkOptionMenu(th_row, values=["Elite Cyber", "Neon Void", "Toxicity", "Retro Gold"], 
                                         command=self._apply_theme_style, fg_color="#1E1E24", button_color="#2E2E38", font=self.f_p, dropdown_font=self.f_p)
        self.opt_theme.set(self.cfg.get("ui_theme_preset", "Elite Cyber"))
        self.opt_theme.pack(side="left", fill="x", expand=True)

        c_row = ctk.CTkFrame(self.style_left_side, fg_color="transparent")
        c_row.pack(fill="x", pady=2)
        ctk.CTkLabel(c_row, text="Theme Accent Color:", font=self.f_bold_p, width=140, anchor="w").pack(side="left")
        self.opt_color = ctk.CTkOptionMenu(c_row, values=["Valorant Red", "Neon Blue", "Emerald", "Gold", "Monochrome"], 
                                         command=self._update_accent, fg_color="#1E1E24", button_color="#2E2E38", font=self.f_p, dropdown_font=self.f_p)
        color_map = {"#FF4655": "Valorant Red", "#00F0FF": "Neon Blue", "#00FF94": "Emerald", "#FFD700": "Gold", "#FAFAFA": "Monochrome"}
        self.opt_color.set(color_map.get(self.cfg["accent_color"], "Valorant Red"))
        self.opt_color.pack(side="left", fill="x", expand=True)
 
        t_row = ctk.CTkFrame(self.style_left_side, fg_color="transparent")
        t_row.pack(fill="x", pady=2)
        ctk.CTkLabel(t_row, text="Page Transition:", font=self.f_bold_p, width=140, anchor="w").pack(side="left")
        self.opt_trans = ctk.CTkOptionMenu(t_row, values=["Smooth Slide", "Bounce Back", "Elastic", "Slide Up"], 
                                         command=self._update_transition, fg_color="#1E1E24", button_color="#2E2E38", font=self.f_p, dropdown_font=self.f_p)
        self.opt_trans.set(self.cfg["transition_style"])
        self.opt_trans.pack(side="left", fill="x", expand=True)
 
        b_row = ctk.CTkFrame(self.style_left_side, fg_color="transparent")
        b_row.pack(fill="x", pady=2)
        ctk.CTkLabel(b_row, text="Inject Button Anim:", font=self.f_bold_p, width=140, anchor="w").pack(side="left")
        self.opt_btn = ctk.CTkOptionMenu(b_row, values=["Sink", "Color Pulse", "Minimal"], 
                                       command=self._update_btn_anim, fg_color="#1E1E24", button_color="#2E2E38", font=self.f_p, dropdown_font=self.f_p)
        self.opt_btn.set(self.cfg["btn_anim_style"])
        self.opt_btn.pack(side="left", fill="x", expand=True)
  
        self.style_right_side = ctk.CTkFrame(style_inner, fg_color="transparent")
        self.style_right_side.grid(row=0, column=1, padx=(15, 0), sticky="nsew")
        
        a_row = ctk.CTkFrame(self.style_right_side, fg_color="transparent")
        a_row.pack(fill="x", pady=5)
        a_lbl_frame = ctk.CTkFrame(a_row, fg_color="transparent")
        a_lbl_frame.pack(fill="x")
        ctk.CTkLabel(a_lbl_frame, text="Animation Speed:", font=self.f_bold_p).pack(side="left")
        self.lbl_anim_speed_val = ctk.CTkLabel(a_lbl_frame, text=f"{self.cfg['ui_anim_speed']:.2f}x", font=self.f_h2, text_color=self.cfg["accent_color"])
        self.lbl_anim_speed_val.pack(side="right")
        self.sld_anim = ctk.CTkSlider(a_row, from_=0.2, to=2.0, number_of_steps=18, command=self._update_anim_speed_ui, progress_color=self.cfg["accent_color"])
        self.sld_anim.set(self.cfg["ui_anim_speed"])
        self.sld_anim.pack(fill="x", pady=(5, 0))
 
        f_row = ctk.CTkFrame(self.style_right_side, fg_color="transparent")
        f_row.pack(fill="x", pady=5)
        f_lbl_frame = ctk.CTkFrame(f_row, fg_color="transparent")
        f_lbl_frame.pack(fill="x")
        ctk.CTkLabel(f_lbl_frame, text="Global Font Scale:", font=self.f_bold_p).pack(side="left")
        self.lbl_font_scale_val = ctk.CTkLabel(f_lbl_frame, text=f"{int(self.cfg['ui_font_scale'])}px", font=self.f_h2, text_color=self.cfg["accent_color"])
        self.lbl_font_scale_val.pack(side="right")
        self.sld_font = ctk.CTkSlider(f_row, from_=10, to=18, number_of_steps=8, command=self._update_font_scale_ui, progress_color=self.cfg["accent_color"])
        self.sld_font.set(self.cfg["ui_font_scale"])
        self.sld_font.pack(fill="x", pady=(5, 0))
 
        self.panels["settings"] = p_set

    def _build_about_panel(self):
        p_about = ctk.CTkFrame(self.container, fg_color="transparent", corner_radius=0)
        card = ctk.CTkFrame(p_about, fg_color="#121214", corner_radius=15, border_width=1, border_color="#1E1E24")
        card.pack(expand=True, fill="both", padx=30, pady=30)
        self.cards.append(card)
        
        self.about_canvas = ctk.CTkCanvas(card, width=100, height=100, bg="#121214", highlightthickness=0)
        self.about_canvas.pack(pady=(25, 5))
        
        ctk.CTkLabel(card, text="V A L - C O R E", font=ctk.CTkFont(family="Impact", size=38), text_color="#FAFAFA").pack(pady=(8, 0))
        ctk.CTkLabel(card, text="E L I T E   H Y B R I D   E D I T I O N", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=self.cfg["accent_color"]).pack(pady=(2, 10))
        
        separator = ctk.CTkFrame(card, fg_color=self.cfg["accent_color"], height=2, width=80)
        separator.pack(pady=5)
        
        self.lbl_typewriter = ctk.CTkLabel(card, text="", font=self.f_p, text_color="#A1A1AA", justify="center", wraplength=500)
        self.lbl_typewriter.pack(pady=10)
        
        ctk.CTkLabel(card, text="Designed for 0 Latency. Universal Environment.", font=ctk.CTkFont(family="Consolas", size=10), text_color="#52525B").pack(side="bottom", pady=15)
        self.panels["about"] = p_about

    def _update_anim_speed_ui(self, val):
        self.lbl_anim_speed_val.configure(text=f"{float(val):.2f}x")
        self._update_anim_speed(val)
        
    def _update_font_scale_ui(self, val):
        self.lbl_font_scale_val.configure(text=f"{int(val)}px")
        self._debounce_font(val)

    def _create_entry(self, parent, val):
        e = ctk.CTkEntry(parent, width=120, height=55, font=ctk.CTkFont("Segoe UI", 26, "bold"), justify="center", fg_color="#09090B", border_color="#3F3F46")
        e.insert(0, val); e.bind("<KeyRelease>", self._schedule_save); e.pack(side="left")
        return e

    def _create_switch(self, parent, text, val):
        var = tk.BooleanVar(value=val)
        sw = ctk.CTkSwitch(parent, text=text, variable=var, command=self._schedule_save, progress_color=self.cfg["accent_color"], font=self.f_p)
        sw.pack(anchor="w", padx=45, pady=12)
        return sw

    def _apply_theme_style(self, theme_name):
        THEME_PRESETS = {
            "Elite Cyber": {
                "accent": "#FF4655",
                "bg": "#09090C",
                "card_bg": "#111115",
                "sidebar_bg": "#121214",
                "border": "#1E1E24",
                "text": "#FAFAFA",
                "corner_radius": 12,
                "entry_bg": "#08080C",
                "accent_name": "Valorant Red"
            },
            "Neon Void": {
                "accent": "#00F0FF",
                "bg": "#070B12",
                "card_bg": "#0F1622",
                "sidebar_bg": "#111926",
                "border": "#1D2B3F",
                "text": "#F0F5FA",
                "corner_radius": 16,
                "entry_bg": "#070A10",
                "accent_name": "Neon Blue"
            },
            "Toxicity": {
                "accent": "#00FF94",
                "bg": "#050A08",
                "card_bg": "#0D1713",
                "sidebar_bg": "#0F1A16",
                "border": "#1A2E26",
                "text": "#E8F8F2",
                "corner_radius": 6,
                "entry_bg": "#040807",
                "accent_name": "Emerald"
            },
            "Retro Gold": {
                "accent": "#FFD700",
                "bg": "#110E0A",
                "card_bg": "#1B1712",
                "sidebar_bg": "#1F1A14",
                "border": "#2E261E",
                "text": "#FAF8F5",
                "corner_radius": 20,
                "entry_bg": "#0D0B08",
                "accent_name": "Gold"
            }
        }
        
        if theme_name not in THEME_PRESETS:
            theme_name = "Elite Cyber"
            
        theme = THEME_PRESETS[theme_name]
        self.cfg["ui_theme_preset"] = theme_name
        self.cfg["accent_color"] = theme["accent"]
        
        # Apply window background
        self.configure(fg_color=theme["bg"])
        self.container.configure(fg_color=theme["bg"])
        if hasattr(self, "aio_scroll_frame"):
            try:
                self.aio_scroll_frame.configure(fg_color=theme["bg"])
            except Exception:
                pass
        
        # Apply sidebar styling
        self.sidebar.configure(
            fg_color=theme["sidebar_bg"],
            border_color=theme["border"]
        )
        
        # Apply cards styling
        for card in self.cards:
            try:
                card.configure(
                    fg_color=theme["card_bg"],
                    border_color=theme["border"],
                    corner_radius=theme["corner_radius"]
                )
            except Exception: pass
            
        if hasattr(self, "log_area"):
            try:
                self.log_area.configure(bg=theme["entry_bg"], fg=theme["text"])
            except Exception: pass
            
        if hasattr(self, "about_canvas"):
            try:
                self.about_canvas.configure(bg=theme["card_bg"])
            except Exception: pass
            
        self.lbl_logo.configure(text_color=theme["accent"])
        
        # Update option menus colors
        for opt in [self.opt_color, self.opt_trans, self.opt_btn, self.opt_theme]:
            if hasattr(opt, "configure"):
                try:
                    opt.configure(
                        fg_color=theme["card_bg"],
                        button_color=theme["sidebar_bg"]
                    )
                except Exception: pass
                
        if hasattr(self, "opt_color"):
            self.opt_color.set(theme["accent_name"])
        if hasattr(self, "opt_theme"):
            self.opt_theme.set(theme_name)
            
        # Update entries styling
        for entry in [self.ent_x, self.ent_y, self.ent_path]:
            if hasattr(entry, "configure"):
                try:
                    entry.configure(
                        fg_color=theme["entry_bg"],
                        border_color=theme["border"]
                    )
                except Exception: pass
                if hasattr(entry, "update_accent_color"):
                    try:
                        entry.update_accent_color(theme["accent"])
                    except Exception: pass
                    
        # Update control elements
        if hasattr(self, "btn_play"):
            self.btn_play.update_state("▶ INJECT GAME", theme["accent"])
            
        if hasattr(self, "sld_font"):
            self.sld_font.configure(progress_color=theme["accent"])
        if hasattr(self, "sld_anim"):
            self.sld_anim.configure(progress_color=theme["accent"])
            
        if hasattr(self, "tab_indicator"):
            self.tab_indicator.configure(fg_color=theme["accent"])
            
        if hasattr(self, "lbl_anim_speed_val"):
            self.lbl_anim_speed_val.configure(text_color=theme["accent"])
        if hasattr(self, "lbl_font_scale_val"):
            self.lbl_font_scale_val.configure(text_color=theme["accent"])
            
        for sw in self.switches.values(): 
            sw.configure(progress_color=theme["accent"])
        for sw in self.util_switches: 
            sw.configure(progress_color=theme["accent"])
            
        for k, btn in self.tabs.items():
            if btn.cget("fg_color") != "transparent": 
                btn.configure(fg_color=theme["card_bg"], text_color="#FFFFFF")
            else:
                btn.configure(hover_color=theme["card_bg"])

        self._schedule_save()

    def _update_accent(self, color_name):
        colors = {"Valorant Red": "#FF4655", "Neon Blue": "#00F0FF", "Emerald": "#00FF94", "Gold": "#FFD700", "Monochrome": "#FAFAFA"}
        new_color = colors[color_name]
        self.cfg["accent_color"] = new_color
        
        self.lbl_logo.configure(text_color=new_color)
        self.btn_play.update_state("▶ INJECT GAME", new_color)
        self.sld_font.configure(progress_color=new_color)
        self.sld_anim.configure(progress_color=new_color)
        
        if hasattr(self, "tab_indicator"):
            self.tab_indicator.configure(fg_color=new_color)
            
        if hasattr(self, "ent_x"):
            self.ent_x.update_accent_color(new_color)
        if hasattr(self, "ent_y"):
            self.ent_y.update_accent_color(new_color)
            
        if hasattr(self, "lbl_anim_speed_val"):
            self.lbl_anim_speed_val.configure(text_color=new_color)
        if hasattr(self, "lbl_font_scale_val"):
            self.lbl_font_scale_val.configure(text_color=new_color)
            
        for sw in self.switches.values(): 
            sw.configure(progress_color=new_color)
        for sw in self.util_switches: 
            sw.configure(progress_color=new_color)
            
        for k, btn in self.tabs.items():
            if btn.cget("fg_color") != "transparent": 
                theme_preset = self.cfg.get("ui_theme_preset", "Elite Cyber")
                theme_card_bg = theme_preset == "Neon Void" and "#0F1622" or (theme_preset == "Toxicity" and "#0D1713" or (theme_preset == "Retro Gold" and "#1B1712" or "#1E1E24"))
                btn.configure(fg_color=theme_card_bg, text_color="#FFFFFF")

        self._schedule_save()

    def _draw_layout_preview(self, canvas, code_name):
        canvas.delete("all")
        accent = self.cfg.get("accent_color", "#FF4655")
        
        # Draw base screen background outline
        canvas.create_rectangle(2, 2, 58, 33, fill="#09090C", outline="#3F3F46", width=1)
        
        if code_name == "Elite Hybrid":
            # Left sidebar, right content
            canvas.create_rectangle(2, 2, 18, 33, fill="#121214", outline="")
            canvas.create_line(18, 2, 18, 33, fill="#3F3F46")
            canvas.create_oval(6, 6, 10, 10, fill=accent, outline="")
            canvas.create_rectangle(22, 5, 36, 15, fill="#111115", outline="#1E1E24")
            canvas.create_rectangle(40, 5, 54, 15, fill="#111115", outline="#1E1E24")
            canvas.create_rectangle(22, 19, 54, 29, fill="#111115", outline="#1E1E24")
            
        elif code_name == "Top Nav Minimal":
            # Top header navigation, content below
            canvas.create_rectangle(2, 2, 58, 10, fill="#121214", outline="")
            canvas.create_line(2, 10, 58, 10, fill="#3F3F46")
            canvas.create_oval(6, 4, 10, 8, fill=accent, outline="")
            canvas.create_rectangle(6, 14, 28, 29, fill="#111115", outline="#1E1E24")
            canvas.create_rectangle(32, 14, 54, 29, fill="#111115", outline="#1E1E24")
            
        elif code_name == "All-in-One Dashboard":
            # Compact 3 columns layout
            canvas.create_rectangle(5, 5, 20, 15, fill="#111115", outline="#1E1E24")
            canvas.create_rectangle(5, 19, 20, 29, fill="#111115", outline="#1E1E24")
            canvas.create_rectangle(24, 5, 39, 29, fill="#111115", outline="#1E1E24")
            canvas.create_rectangle(43, 5, 55, 15, fill="#111115", outline="#1E1E24")
            canvas.create_rectangle(43, 19, 55, 29, fill="#111115", outline="#1E1E24")
            
        elif code_name == "Glassmorphism Floating":
            # Floating cards layout
            canvas.create_rectangle(5, 5, 18, 30, fill="#121214", outline=accent, width=1)
            canvas.create_rectangle(23, 5, 55, 30, fill="#111115", outline=accent, width=1)

    def _change_ui_layout(self, style_name):
        self.cfg["layout_style"] = style_name
        self._repack_layouts(style_name)
        self._highlight_style_box(style_name)
        self._schedule_save()

    def _highlight_style_box(self, style_name):
        accent = self.cfg.get("accent_color", "#FF4655")
        theme_preset = self.cfg.get("ui_theme_preset", "Elite Cyber")
        THEME_PRESETS = {
            "Elite Cyber": {"card_bg": "#111115", "border": "#1E1E24"},
            "Neon Void": {"card_bg": "#0F1622", "border": "#1D2B3F"},
            "Toxicity": {"card_bg": "#0D1713", "border": "#1A2E26"},
            "Retro Gold": {"card_bg": "#1B1712", "border": "#2E261E"}
        }
        theme = THEME_PRESETS.get(theme_preset, THEME_PRESETS["Elite Cyber"])
        
        for name, box in self.style_boxes.items():
            if name == style_name:
                box.configure(border_color=accent, fg_color=theme["card_bg"])
                for child in box.winfo_children():
                    if isinstance(child, ctk.CTkCanvas):
                        self._draw_layout_preview(child, name)
            else:
                box.configure(border_color=theme["border"], fg_color="#1E1E24")
                for child in box.winfo_children():
                    if isinstance(child, ctk.CTkCanvas):
                        self._draw_layout_preview(child, name)

    def _repack_overrides(self, style_name):
        pass

    def _repack_aesthetics(self, style_name):
        pass

    def _repack_utilities(self, style_name):
        pass

    # ──────────────────────────────────────────────────────────────────
    # 120 FPS LERP Smooth Scroll Engine
    # Intercepts at the canvas.yview() level so the existing bind_all
    # handler still fires, but scroll jumps become smooth LERP targets.
    # ──────────────────────────────────────────────────────────────────
    def _setup_smooth_scroll(self):
        """Monkey-patch _parent_canvas.yview so every scroll call from
        CTkScrollableFrame's bind_all handler is redirected into our
        LERP accumulator instead of jumping the viewport directly."""
        self._ss_target_y  = 0.0   # target fraction (0.0 – 1.0)
        self._ss_current_y = 0.0   # animated current fraction
        self._ss_anim_id   = None  # after() id for the tick loop
        self._ss_dragging  = False # True while user holds scrollbar thumb

        sf  = self.aio_scroll_frame
        canvas = sf._parent_canvas

        # Keep a reference to the real yview command
        self._ss_real_yview = canvas.yview

        def _intercepted_yview(*args):
            """Intercept yview('scroll', n, 'units') and feed LERP instead."""
            if args and args[0] == "scroll" and not self._ss_dragging:
                n = int(args[1])          # number of units (+ve = down)
                # CTk sends delta/6 as units; each unit ≈ 6px
                scroll_region = canvas.bbox("all")
                if scroll_region:
                    total_h = max(scroll_region[3] - scroll_region[1], 1)
                    # How far one notch moves as a fraction of total content height
                    step_frac = (n * 6.0) / total_h
                    lo, hi = self._ss_real_yview()
                    view_size = hi - lo
                    self._ss_target_y = max(0.0, min(1.0 - view_size,
                                                     self._ss_target_y + step_frac))
                    if self._ss_anim_id is None:
                        self._ss_current_y = lo
                        self._tick_smooth_scroll(canvas)
                return  # suppress the original jump
            # All other calls (moveto, query) pass through untouched
            return self._ss_real_yview(*args)

        canvas.yview = _intercepted_yview  # type: ignore[method-assign]

        # Detect scrollbar thumb drag so we skip LERP during manual drag
        if hasattr(sf, "_scrollbar"):
            sf._scrollbar.bind("<ButtonPress-1>",
                               lambda e: setattr(self, "_ss_dragging", True),  add="+")
            sf._scrollbar.bind("<ButtonRelease-1>",
                               lambda e: setattr(self, "_ss_dragging", False), add="+")

    def _tick_smooth_scroll(self, canvas):
        """Tick the LERP animation at 8 ms intervals (~125 Hz)."""
        LERP_FACTOR = 0.25            # larger = faster catch-up, smaller = silkier
        STOP_THRESHOLD = 0.00008     # stop when close enough

        diff = self._ss_target_y - self._ss_current_y
        if abs(diff) < STOP_THRESHOLD or self._ss_dragging:
            # Snap to final position and stop
            if not self._ss_dragging:
                self._ss_real_yview("moveto", self._ss_target_y)
            self._ss_anim_id = None
            return

        self._ss_current_y += diff * LERP_FACTOR
        self._ss_real_yview("moveto", self._ss_current_y)
        self._ss_anim_id = self.after(8, self._tick_smooth_scroll, canvas)

    def _stop_smooth_scroll(self):
        """Cancel any in-progress smooth scroll animation."""
        if hasattr(self, "_ss_anim_id") and self._ss_anim_id is not None:
            self.after_cancel(self._ss_anim_id)
            self._ss_anim_id = None

    # ──────────────────────────────────────────────────────────────────

    def _repack_layouts(self, style_name):
        if not hasattr(self, "sidebar") or not hasattr(self, "container"):
            return
            
        # Cancel any active animation tasks to prevent Tkinter race conditions / panel overlapping
        if hasattr(self, "_anim_task") and self._anim_task:
            self.after_cancel(self._anim_task)
            self._anim_task = None
        if hasattr(self, "_indicator_anim_task") and self._indicator_anim_task:
            self.after_cancel(self._indicator_anim_task)
            self._indicator_anim_task = None
        if hasattr(self, "_typing_timer") and self._typing_timer:
            self.after_cancel(self._typing_timer)
            self._typing_timer = None
        if hasattr(self, "_about_anim_task") and self._about_anim_task:
            self.after_cancel(self._about_anim_task)
            self._about_anim_task = None
            
        # Reset row and column configurations to avoid grid clashing when switching styles
        for i in range(5):
            self.grid_rowconfigure(i, weight=0, minsize=0)
            self.grid_columnconfigure(i, weight=0, minsize=0)
            
        self.sidebar.grid_forget()
        self.sidebar.pack_forget()
        self.container.grid_forget()
        self.container.pack_forget()
        self.bottom_action_bar.grid_forget()
        self.bottom_action_bar.pack_forget()
        
        for p in self.panels.values():
            p.place_forget()
            p.grid_forget()
            p.pack_forget()
            
        self.res_card.grid_forget()
        self.res_card.pack_forget()
        self.diag_card.grid_forget()
        self.diag_card.pack_forget()
        self.log_card.grid_forget()
        self.log_card.pack_forget()
        self.path_card.grid_forget()
        self.path_card.pack_forget()
        self.overrides_card.grid_forget()
        self.overrides_card.pack_forget()
        self.layout_card.grid_forget()
        self.layout_card.pack_forget()
        self.utils_card.grid_forget()
        self.utils_card.pack_forget()
        self.style_card.grid_forget()
        self.style_card.pack_forget()
        
        if hasattr(self, "home_top_grid"):
            self.home_top_grid.pack_forget()
            self.home_top_grid.grid_forget()
            
        self.lbl_logo.pack_forget()
        self.lbl_sub_logo.pack_forget()
        self.tab_container.pack_forget()
        for btn in self.tabs.values():
            btn.pack_forget()
        self.tab_indicator.place_forget()
        # Restore style rows and layout preview boxes to full size
        for _opt_attr in ("opt_theme", "opt_btn", "opt_trans", "opt_color"):
            _opt = getattr(self, _opt_attr, None)
            if _opt is not None:
                _opt.master.pack(fill="x", pady=2)
                _opt.master.pack_configure(pady=2)
        for _box in getattr(self, "style_boxes", {}).values():
            _box.grid_configure(ipady=8)
            for _ch in _box.winfo_children():
                if isinstance(_ch, ctk.CTkCanvas):
                    _ch.configure(height=35)

        
        if style_name == "Elite Hybrid":
            # Grid config of main window
            self.grid_rowconfigure(0, weight=1)
            self.grid_rowconfigure(1, weight=0, minsize=80)
            self.grid_columnconfigure(0, weight=0, minsize=260)
            self.grid_columnconfigure(1, weight=1)
            
            self.sidebar.grid(row=0, column=0, sticky="nsew")
            self.sidebar.configure(border_width=1, corner_radius=0)
            self.container.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
            self.bottom_action_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(5, 15))
            
            self.lbl_logo.pack(pady=(45, 2))
            self.lbl_sub_logo.pack(pady=(0, 30))
            self.tab_container.pack(fill="x", padx=10, pady=10)
            for btn in self.tabs.values():
                btn.pack(fill="x", padx=(15, 10), pady=6, ipady=6)
                btn.configure(anchor="w")
                
            self.home_top_grid.pack(in_=self.panels["home"], fill="x", padx=20, pady=15)
            self.res_card.grid(in_=self.home_top_grid, row=0, column=0, padx=(0, 10), sticky="nsew")
            self.diag_card.grid(in_=self.home_top_grid, row=0, column=1, padx=(10, 0), sticky="nsew")
            self.log_card.pack(in_=self.panels["home"], fill="both", expand=True, padx=20, pady=(0, 15))
            
            self.path_card.pack(in_=self.panels["engine"], fill="x", padx=20, pady=15)
            self.overrides_card.pack(in_=self.panels["engine"], fill="both", expand=True, padx=20, pady=(0, 15))
            
            self.layout_card.pack(in_=self.panels["settings"], fill="x", padx=20, pady=15)
            self.utils_card.pack(in_=self.panels["settings"], fill="x", padx=20, pady=(0, 15))
            self.style_card.pack(in_=self.panels["settings"], fill="both", expand=True, padx=20, pady=(0, 15))
            
            target_tab = self.current_tab if (hasattr(self, "current_tab") and self.current_tab != "all_in_one") else "home"
            self._switch_tab(target_tab)
            
        elif style_name == "Top Nav Minimal":
            # Grid config of main window
            self.grid_rowconfigure(0, weight=0, minsize=70)
            self.grid_rowconfigure(1, weight=1)
            self.grid_rowconfigure(2, weight=0, minsize=90)
            self.grid_columnconfigure(0, weight=1)
            
            self.sidebar.grid(row=0, column=0, sticky="ew")
            self.sidebar.configure(border_width=1, corner_radius=0)
            self.container.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
            self.bottom_action_bar.grid(row=2, column=0, sticky="ew", padx=20, pady=(5, 15))
            
            self.lbl_logo.pack(side="left", padx=25, pady=15)
            self.lbl_sub_logo.pack_forget()
            self.tab_container.pack(side="left", fill="y", padx=20, pady=10)
            for btn in self.tabs.values():
                btn.pack(side="left", padx=5, pady=0)
                btn.configure(anchor="center")
                
            self.home_top_grid.pack(in_=self.panels["home"], fill="x", padx=20, pady=15)
            self.res_card.grid(in_=self.home_top_grid, row=0, column=0, padx=(0, 10), sticky="nsew")
            self.diag_card.grid(in_=self.home_top_grid, row=0, column=1, padx=(10, 0), sticky="nsew")
            self.log_card.pack(in_=self.panels["home"], fill="both", expand=True, padx=20, pady=(0, 15))
            
            self.path_card.pack(in_=self.panels["engine"], fill="x", padx=20, pady=15)
            self.overrides_card.pack(in_=self.panels["engine"], fill="both", expand=True, padx=20, pady=(0, 15))
            
            self.layout_card.pack(in_=self.panels["settings"], fill="x", padx=20, pady=(15, 5))
            self.utils_card.pack(in_=self.panels["settings"], fill="x", padx=20, pady=(0, 5))
            self.style_card.pack(in_=self.panels["settings"], fill="x", padx=20, pady=(0, 15))
            # Compact mode: shrink the layout preview boxes and reduce row padding
            # so all 4 Launcher Aesthetics rows fit without hiding any
            for _box in getattr(self, "style_boxes", {}).values():
                _box.grid_configure(ipady=2)
                for _ch in _box.winfo_children():
                    if isinstance(_ch, ctk.CTkCanvas):
                        _ch.configure(height=22)
                    elif isinstance(_ch, ctk.CTkLabel):
                        _ch.configure(pady=0)
            # Reduce row gaps inside the aesthetics card
            for _attr in ("opt_theme", "opt_color", "opt_trans", "opt_btn"):
                _w = getattr(self, _attr, None)
                if _w is not None:
                    _w.master.pack_configure(pady=1)
            
            target_tab = self.current_tab if (hasattr(self, "current_tab") and self.current_tab != "all_in_one") else "home"
            self._switch_tab(target_tab)
            
        elif style_name == "All-in-One Dashboard":
            self.grid_rowconfigure(0, weight=1)
            self.grid_rowconfigure(1, weight=0, minsize=80)
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure(1, weight=0)
            
            self.sidebar.grid_forget()
            self.container.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
            self.bottom_action_bar.grid(row=1, column=0, sticky="ew", padx=20, pady=(5, 15))
            
            self.current_tab = "all_in_one"
            self.panels["all_in_one"].place(relx=0, rely=0, relwidth=1, relheight=1)
            
            self.layout_card.grid(in_=self.aio_scroll_frame, row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
            self.res_card.grid(in_=self.aio_scroll_frame, row=1, column=0, padx=10, pady=10, sticky="nsew")
            self.path_card.grid(in_=self.aio_scroll_frame, row=1, column=1, padx=10, pady=10, sticky="nsew")
            self.diag_card.grid(in_=self.aio_scroll_frame, row=2, column=0, padx=10, pady=10, sticky="nsew")
            self.overrides_card.grid(in_=self.aio_scroll_frame, row=2, column=1, padx=10, pady=10, sticky="nsew")
            self.utils_card.grid(in_=self.aio_scroll_frame, row=3, column=0, padx=10, pady=10, sticky="nsew")
            self.style_card.grid(in_=self.aio_scroll_frame, row=3, column=1, padx=10, pady=10, sticky="nsew")
            self.log_card.grid(in_=self.aio_scroll_frame, row=4, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
            
        elif style_name == "Glassmorphism Floating":
            self.grid_rowconfigure(0, weight=1)
            self.grid_rowconfigure(1, weight=0, minsize=80)
            self.grid_columnconfigure(0, weight=0, minsize=280)
            self.grid_columnconfigure(1, weight=1)
            
            self.sidebar.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
            self.sidebar.configure(border_width=1, corner_radius=15)
            self.container.grid(row=0, column=1, sticky="nsew", padx=(0, 15), pady=15)
            self.bottom_action_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(5, 15))
            
            self.lbl_logo.pack(pady=(35, 2))
            self.lbl_sub_logo.pack(pady=(0, 20))
            self.tab_container.pack(fill="x", padx=10, pady=10)
            for btn in self.tabs.values():
                btn.pack(fill="x", padx=(15, 10), pady=6, ipady=6)
                btn.configure(anchor="w")
                
            self.home_top_grid.pack(in_=self.panels["home"], fill="x", padx=20, pady=15)
            self.res_card.grid(in_=self.home_top_grid, row=0, column=0, padx=(0, 10), sticky="nsew")
            self.diag_card.grid(in_=self.home_top_grid, row=0, column=1, padx=(10, 0), sticky="nsew")
            self.log_card.pack(in_=self.panels["home"], fill="both", expand=True, padx=20, pady=(0, 15))
            
            self.path_card.pack(in_=self.panels["engine"], fill="x", padx=20, pady=15)
            self.overrides_card.pack(in_=self.panels["engine"], fill="both", expand=True, padx=20, pady=(0, 15))
            
            self.layout_card.pack(in_=self.panels["settings"], fill="x", padx=20, pady=15)
            self.utils_card.pack(in_=self.panels["settings"], fill="x", padx=20, pady=(0, 15))
            self.style_card.pack(in_=self.panels["settings"], fill="both", expand=True, padx=20, pady=(0, 15))
            
            target_tab = self.current_tab if (hasattr(self, "current_tab") and self.current_tab != "all_in_one") else "home"
            self._switch_tab(target_tab)

    def _update_transition(self, val):
        self.cfg["transition_style"] = val
        self._schedule_save()

    def _update_btn_anim(self, val):
        self.cfg["btn_anim_style"] = val
        self._schedule_save()
        
    def _update_anim_speed(self, val):
        self.cfg["ui_anim_speed"] = float(val)
        self._schedule_save()

    def _debounce_font(self, val):
        if self._font_debounce: self.after_cancel(self._font_debounce)
        self._font_debounce = self.after(200, lambda: self._apply_font_scale(val))

    def _apply_font_scale(self, val):
        self.cfg["ui_font_scale"] = int(val)
        self._init_fonts()
        self.lbl_logo.configure(font=self.f_h1)
        for btn in self.tabs.values(): btn.configure(font=self.f_h2)
        self.btn_play.btn.configure(font=self.f_btn)
        self._schedule_save()

    def _animate_indicator(self, start_y, start_h, end_y, end_h, start_time):
        if self.cfg.get("layout_style", "Elite Hybrid") == "All-in-One Dashboard":
            self._indicator_anim_task = None
            return
            
        elapsed = time.time() - start_time
        duration = 0.22 / self.cfg.get("ui_anim_speed", 1.0)
        
        if elapsed >= duration:
            self.tab_indicator.configure(height=int(end_h))
            self.tab_indicator.place(x=5, y=end_y)
            self.current_indicator_y = end_y
            self.current_indicator_h = end_h
            self._indicator_anim_task = None
            return
            
        t = elapsed / duration
        ease = EaseAnim.ease_out_quint(t)
        curr_y = EaseAnim.lerp(start_y, end_y, ease)
        curr_h = EaseAnim.lerp(start_h, end_h, ease)
        
        self.tab_indicator.configure(height=int(curr_h))
        self.tab_indicator.place(x=5, y=curr_y)
        self.current_indicator_y = curr_y
        self.current_indicator_h = curr_h
        
        self._indicator_anim_task = self.after(10, self._animate_indicator, start_y, start_h, end_y, end_h, start_time)

    def _switch_tab(self, name):
        self.current_tab = name
            
        if self._anim_task: self.after_cancel(self._anim_task)
        if self._typing_timer: self.after_cancel(self._typing_timer)
        if self._about_anim_task: self.after_cancel(self._about_anim_task)
        
        for k, btn in self.tabs.items(): 
            if k == name:
                btn.configure(fg_color="#1E1E24", text_color="#FFFFFF")
            else:
                btn.configure(fg_color="transparent", text_color="#8A8A93")
            
        btn = self.tabs[name]
        self.update_idletasks()
        target_y = btn.winfo_y()
        target_h = btn.winfo_height()
        
        if not hasattr(self, "current_indicator_y"):
            self.current_indicator_y = target_y
            self.current_indicator_h = target_h
            self.tab_indicator.configure(height=int(target_h))
            self.tab_indicator.place(x=5, y=target_y)
        else:
            if hasattr(self, "_indicator_anim_task") and self._indicator_anim_task:
                self.after_cancel(self._indicator_anim_task)
            self._indicator_anim_task = None
            self._animate_indicator(self.current_indicator_y, self.current_indicator_h, target_y, target_h, time.time())

        if self.cfg.get("layout_style", "Elite Hybrid") == "All-in-One Dashboard":
            return

        for p in self.panels.values(): 
            p.place_forget()
            p.grid_forget()
            p.pack_forget()
        
        if name == "about":
            self.lbl_typewriter.configure(text="")
            self._typewriter_effect("Engineered for pure hybrid performance.\nSeamlessly switches between Home configurations and Cyber Cafe network structures.\nForces resolution matrix modifications instantly.", 0)
            self._animate_about_logo(0)

        target_panel = self.panels[name]
        start_time = time.time()
        self._animate_panel(target_panel, start_time, self.cfg["transition_style"])

    def _animate_panel(self, panel, start_time, style):
        if self.cfg.get("layout_style", "Elite Hybrid") == "All-in-One Dashboard":
            self._anim_task = None
            return
            
        # Verify if this panel is actually the one currently selected
        panel_name = next((k for k, v in self.panels.items() if v == panel), None)
        if panel_name != self.current_tab:
            self._anim_task = None
            return
            
        elapsed = time.time() - start_time
        duration = 0.32 / self.cfg.get("ui_anim_speed", 1.0)
        
        if elapsed >= duration:
            panel.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._anim_task = None
            return
            
        t = elapsed / duration
        if style == "Elastic":
            ease = EaseAnim.ease_out_elastic(t)
            offset_x = 0.1 * (1 - ease)
            panel.place(relx=offset_x, rely=0, relwidth=1, relheight=1)
        elif style == "Bounce Back":
            ease = EaseAnim.ease_out_back(t)
            offset_x = 0.1 * (1 - ease)
            panel.place(relx=offset_x, rely=0, relwidth=1, relheight=1)
        elif style == "Slide Up":
            ease = EaseAnim.ease_out_quint(t)
            offset_y = 0.05 * (1 - ease)
            panel.place(relx=0, rely=offset_y, relwidth=1, relheight=1)
        else:
            ease = EaseAnim.ease_out_quint(t)
            offset_x = 0.08 * (1 - ease)
            panel.place(relx=offset_x, rely=0, relwidth=1, relheight=1)
            
        self._anim_task = self.after(16, self._animate_panel, panel, start_time, style)

    def _typewriter_effect(self, text, index):
        if self.cfg.get("layout_style", "Elite Hybrid") == "All-in-One Dashboard":
            self._typing_timer = None
            return
        if self.current_tab != "about":
            self._typing_timer = None
            return
            
        if index <= len(text):
            cursor = " █" if (index // 2) % 2 == 0 else "  "
            self.lbl_typewriter.configure(text=text[:index] + cursor)
            self._typing_timer = self.after(15, self._typewriter_effect, text, index + 1)
        else:
            self._blink_cursor_counter = 0
            self._blink_typewriter_cursor(text)

    def _blink_typewriter_cursor(self, text):
        if self.cfg.get("layout_style", "Elite Hybrid") == "All-in-One Dashboard":
            self._typing_timer = None
            return
        if self.current_tab != "about":
            self._typing_timer = None
            return
        if self.tabs["about"].cget("fg_color") == "transparent":
            return
        cursor = " █" if self._blink_cursor_counter % 2 == 0 else "  "
        self.lbl_typewriter.configure(text=text + cursor)
        self._blink_cursor_counter += 1
        self._typing_timer = self.after(500, self._blink_typewriter_cursor, text)

    def _animate_about_logo(self, step=0):
        if self.cfg.get("layout_style", "Elite Hybrid") == "All-in-One Dashboard":
            self._about_anim_task = None
            return
        if self.current_tab != "about":
            self._about_anim_task = None
            return
            
        if self._about_anim_task:
            self.after_cancel(self._about_anim_task)
            self._about_anim_task = None
            
        if self.tabs["about"].cget("fg_color") == "transparent":
            return
            
        self.about_canvas.delete("all")
        
        cx, cy = 60, 60
        accent_color = self.cfg["accent_color"]
        
        length = min(1.0, step / 20) * 15
        
        self.about_canvas.create_line(cx - 35, cy - 35, cx - 35 + length, cy - 35, fill=accent_color, width=2)
        self.about_canvas.create_line(cx - 35, cy - 35, cx - 35, cy - 35 + length, fill=accent_color, width=2)
        
        self.about_canvas.create_line(cx + 35, cy - 35, cx + 35 - length, cy - 35, fill=accent_color, width=2)
        self.about_canvas.create_line(cx + 35, cy - 35, cx + 35, cy - 35 + length, fill=accent_color, width=2)
        
        self.about_canvas.create_line(cx - 35, cy + 35, cx - 35 + length, cy + 35, fill=accent_color, width=2)
        self.about_canvas.create_line(cx - 35, cy + 35, cx - 35, cy + 35 - length, fill=accent_color, width=2)
        
        self.about_canvas.create_line(cx + 35, cy + 35, cx + 35 - length, cy + 35, fill=accent_color, width=2)
        self.about_canvas.create_line(cx + 35, cy + 35, cx + 35, cy + 35 - length, fill=accent_color, width=2)
        
        v_progress = max(0.0, min(1.0, (step - 10) / 20))
        if v_progress > 0:
            x0, y0 = cx - 15, cy - 15
            x1, y1 = cx, cy + 15
            curr_x1 = EaseAnim.lerp(x0, x1, v_progress)
            curr_y1 = EaseAnim.lerp(y0, y1, v_progress)
            self.about_canvas.create_line(x0, y0, curr_x1, curr_y1, fill="#FAFAFA", width=4)
            
            if v_progress > 0.5:
                v_prog_r = (v_progress - 0.5) * 2
                rx0, ry0 = cx, cy + 15
                rx1, ry1 = cx + 15, cy - 15
                curr_rx1 = EaseAnim.lerp(rx0, rx1, v_prog_r)
                curr_ry1 = EaseAnim.lerp(ry0, ry1, v_prog_r)
                self.about_canvas.create_line(rx0, ry0, curr_rx1, curr_ry1, fill="#FAFAFA", width=4)
                
        if step > 25:
            wave_prog = ((step - 25) % 30) / 30
            wave_r = 15 + wave_prog * 25
            wave_color = interpolate_color(accent_color, "#121214", wave_prog)
            self.about_canvas.create_oval(cx - wave_r, cy - wave_r, cx + wave_r, cy + wave_r, outline=wave_color, width=1)
            
        self._about_anim_task = self.after(20, self._animate_about_logo, step + 1)

    def _log(self, msg, tag):
        self.log_area.config(state="normal")
        self.log_area.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] [{tag.upper()}] {msg}\n", tag)
        self.log_area.see(tk.END)
        self.log_area.config(state="disabled")
        AppManager.write_file_log(msg, tag)

    def _schedule_save(self, event=None):
        if self._save_timer: self.after_cancel(self._save_timer)
        self._save_timer = self.after(500, self._instant_save) 

    def _instant_save(self):
        try:
            self.cfg["default_stretched"]["x"] = int(self.ent_x.get())
            self.cfg["default_stretched"]["y"] = int(self.ent_y.get())
        except ValueError: pass
        
        if hasattr(self, "switches"):
            if "true_stretched" in self.switches:
                self.cfg["true_stretched"] = bool(self.switches["true_stretched"].get())
            if "aggro_mode" in self.switches:
                self.cfg["aggressive_mode"] = bool(self.switches["aggro_mode"].get())
            if "pnp_toggle" in self.switches:
                self.cfg["monitor_toggle_enabled"] = bool(self.switches["pnp_toggle"].get())
            if "fps_boost" in self.switches:
                self.cfg["auto_high_priority"] = bool(self.switches["fps_boost"].get())
        self.cfg["vibrance_auto"] = bool(self.var_vib.get())
        self.cfg["womic_auto"] = bool(self.var_mic.get())
        if hasattr(self, "opt_theme"):
            self.cfg["ui_theme_preset"] = self.opt_theme.get()
        
        AppManager.save_config(self.cfg)

    def _check_paths(self):
        if not self.cfg["valorant_path"]:
            p = WinAPI.get_riot_client_path_dynamic()
            if p: self._update_path(p)

    def _browse_path(self):
        p = filedialog.askopenfilename(title="Select RiotClientServices.exe", filetypes=[("Executable", "*.exe")])
        if p: self._update_path(p)

    def _update_path(self, p):
        self.cfg["valorant_path"] = p
        AppManager.save_config(self.cfg)
        self.ent_path.configure(state="normal")
        self.ent_path.delete(0, tk.END); self.ent_path.insert(0, p)
        self.ent_path.configure(state="readonly")

    def handle_action_button(self):
        if self.game_running or self.btn_play.btn.cget("text") == "ABORT ENGINE":
            self.abort_requested = True
            self._log("Emergency termination triggered!", "err")
            WinAPI.kill_game()
            self._cleanup_to_idle()
        else:
            self.boot_sequence()

    def boot_sequence(self):
        self.abort_requested = False
        self.btn_play.update_state("ABORT ENGINE", "#EF4444")
        self.update_status("INITIALIZING...", "#38BDF8")
        threading.Thread(target=self._core_thread, daemon=True).start()

    def _core_thread(self):
        try:
            res_x, res_y = self.cfg["default_stretched"]["x"], self.cfg["default_stretched"]["y"]
            
            if not WinAPI.is_resolution_supported(res_x, res_y):
                self._log(f"Error: Resolution {res_x}x{res_y} is not supported by your GPU!", "err")
                self.after(0, self._cleanup_to_idle); return

            self._log("Patching game layout configuration data structure...", "sys")
            WinAPI.patch_game_config(res_x, res_y)
            
            if self.cfg.get("true_stretched", True):
                if not AppManager.apply_qres(res_x, res_y):
                    if WinAPI.force_resolution(res_x, res_y, permanent=False):
                        self._log(f"Resolution forced via native API ({res_x}x{res_y}).", "ok")
                    else:
                        self._log(f"Failed to force resolution native API ({res_x}x{res_y}).", "err")
                else: self._log(f"Resolution applied via qres ({res_x}x{res_y}).", "ok")
            else:
                if WinAPI.force_resolution(res_x, res_y, permanent=False):
                    self._log(f"Resolution forced via native API ({res_x}x{res_y}).", "ok")
                else:
                    self._log(f"Failed to force resolution native API ({res_x}x{res_y}).", "err")

            if self.cfg["aggressive_mode"]: WinAPI.toggle_taskbar(hide=True)
            if self.cfg["monitor_toggle_enabled"]: WinAPI.pulse_pnp_monitor()

            if self.cfg.get("vibrance_auto") and not WinAPI.is_laptop():
                WinAPI.launch_vibrance()

            if self.cfg.get("womic_auto"):
                WinAPI.handle_womic()

            val_path = self.cfg.get("valorant_path", "")
            if val_path and os.path.exists(val_path):
                self._log(f"Launching Client via configured environment path...", "sys")
                subprocess.Popen([val_path, "--launch-product=valorant", "--launch-patchline=live"], creationflags=WinAPI.CREATE_NO_WINDOW)
            else:
                self._log("Configured path invalid. Initializing multi-tier disk scanning sequence...", "sys")
                scanned_path = WinAPI.get_riot_client_path_dynamic()
                if scanned_path:
                    self._log(f"Target found on system storage: {scanned_path}. Initializing...", "sys")
                    subprocess.Popen([scanned_path, "--launch-product=valorant", "--launch-patchline=live"], creationflags=WinAPI.CREATE_NO_WINDOW)
                else:
                    self._log("Automated launch blocked by system virtualization. Awaiting manual execution...", "sys")

            timeout = 180
            target_pid = None
            # Poll at 250 ms intervals — detects the process up to 4× faster than 1 s
            poll_interval = 0.25
            elapsed = 0.0
            while elapsed < timeout:
                if self.abort_requested:
                    self._log("Process hook sequence cancelled.", "sys")
                    return
                try:
                    for p in psutil.process_iter(['name', 'pid']):
                        try:
                            if p.info['name'] == "VALORANT-Win64-Shipping.exe":
                                target_pid = p.info['pid']
                                break
                        except (psutil.NoSuchProcess, psutil.AccessDenied): continue
                except Exception: pass
                if target_pid: break
                time.sleep(poll_interval)
                elapsed += poll_interval

            if not target_pid:
                self._log("Process hook sequence timed out.", "err")
                self.after(0, self._cleanup_to_idle); return

            if self.abort_requested:
                self._log("Process hook sequence cancelled.", "sys")
                return

            self.game_running = True
            self.after(0, lambda: self.update_status("CONNECTING...", "#F59E0B"))
            self._log("Process hooked successfully. Initializing sandbox synchronization...", "sys")

            # Smart wait: monitor CPU usage instead of sleeping a flat 15 s.
            # Valorant spikes CPU while loading then drops when the menu is ready.
            # We wait for that drop (or cap at 8 s — half the old 15 s).
            try:
                proc_obj = psutil.Process(target_pid)
                proc_obj.cpu_percent(interval=None)   # prime the counter
                smart_wait_limit = 8.0
                smart_elapsed = 0.0
                spike_seen = False
                while smart_elapsed < smart_wait_limit:
                    if self.abort_requested:
                        self._log("Process activation cancelled.", "sys")
                        return
                    time.sleep(0.5)
                    smart_elapsed += 0.5
                    try:
                        cpu = proc_obj.cpu_percent(interval=None)
                        if cpu > 30:
                            spike_seen = True      # loading spike detected
                        elif spike_seen and cpu < 8:
                            break                  # spike ended → game menu ready
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        break
            except Exception:
                time.sleep(8)   # fallback if psutil probe fails

            if self.abort_requested:
                self._log("Process activation cancelled.", "sys")
                return
            self._log("UNLEASH YOUR POWER! ⚔️", "hype")
            self.after(0, lambda: self.update_status("READY FOR ACTION", self.cfg["accent_color"]))

            if self.cfg.get("auto_high_priority", True):
                try: psutil.Process(target_pid).nice(psutil.HIGH_PRIORITY_CLASS)
                except Exception: pass

            proc = psutil.Process(target_pid)
            while True:
                if self.abort_requested:
                    self._log("Gameplay loop tracking cancelled.", "sys")
                    return
                try:
                    if not proc.is_running() or proc.status() == psutil.STATUS_ZOMBIE: break
                except psutil.NoSuchProcess: break
                time.sleep(2)


        except Exception as e: self._log(f"Core execution failure: {str(e)}", "err")
        finally:
            if self.game_running: self._log("Instance terminated. Executing system rollback parameters.", "sys")
            self.after(0, self._cleanup_to_idle)

    def _cleanup_to_idle(self):
        self.game_running = False
        WinAPI.force_resolution(self.cfg["exit_res"].get("x", 1920), self.cfg["exit_res"].get("y", 1080), permanent=True)
        WinAPI.toggle_taskbar(hide=False)
        self.update_status("SYSTEM READY", "#10B981")
        self.btn_play.update_state("▶ INJECT GAME", fg_color=self.cfg["accent_color"])

    def _emergency_cleanup(self):
        WinAPI.force_resolution(self.cfg["exit_res"].get("x", 1920), self.cfg["exit_res"].get("y", 1080), permanent=True)
        WinAPI.toggle_taskbar(hide=False)

    def on_force_exit(self):
        self._emergency_cleanup()
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    app = UltimateUI()
    app.mainloop()