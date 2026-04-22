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

class AppManager:
    CONFIG_FILE = "launcher_config.json"
    LOG_FILE = "val_core_system.log"

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
            "btn_anim_style": "Sink"
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
            except Exception: pass
        return default_data

    @classmethod
    def save_config(cls, data: dict):
        with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    @classmethod
    def write_file_log(cls, msg: str, tag: str):
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(cls.LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(f"[{ts}] [{tag.upper()}] {msg}\n")
        except Exception: pass
    
    @classmethod
    def apply_qres(cls, width: int, height: int) -> bool:
        possible_paths = [os.path.join(os.path.dirname(__file__), "qres.exe"), shutil.which("qres.exe")]
        qres_path = next((p for p in possible_paths if p), None)
        if not qres_path: 
            return False
        try:
            args = [qres_path, f"/x:{width}", f"/y:{height}"]
            result = subprocess.run(args, capture_output=True, creationflags=WinAPI.CREATE_NO_WINDOW)
            return result.returncode == 0
        except Exception: 
            return False

class WinAPI:
    CREATE_NO_WINDOW = 0x08000000

    @staticmethod
    def is_admin() -> bool:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

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
                except Exception:
                    break
            return False
        except ImportError:
            return True

    @staticmethod
    def force_resolution(width: int, height: int) -> bool:
        try:
            import win32api, win32con
            devmode = win32api.EnumDisplaySettings(None, win32con.ENUM_CURRENT_SETTINGS)
            devmode.PelsWidth, devmode.PelsHeight = width, height
            devmode.Fields = win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT
            return win32api.ChangeDisplaySettings(devmode, 0) == win32con.DISP_CHANGE_SUCCESSFUL
        except ImportError:
            return False

    @staticmethod
    def toggle_taskbar(hide: bool):
        abd = type("APPBARDATA", (ctypes.Structure,), {"_fields_": [("cbSize", wintypes.DWORD), ("hWnd", wintypes.HWND), ("uCallbackMessage", wintypes.UINT), ("uEdge", wintypes.UINT), ("rc", wintypes.RECT), ("lParam", wintypes.LPARAM)]})()
        abd.cbSize, abd.hWnd = ctypes.sizeof(abd), ctypes.windll.user32.FindWindowW(u"Shell_TrayWnd", None)
        is_hidden = (ctypes.windll.shell32.SHAppBarMessage(4, ctypes.byref(abd)) & 1) != 0
        if hide and not is_hidden:
            abd.lParam = 1; ctypes.windll.shell32.SHAppBarMessage(10, ctypes.byref(abd))
        elif not hide and is_hidden:
            abd.lParam = 2; ctypes.windll.shell32.SHAppBarMessage(10, ctypes.byref(abd))

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
                    with open(fpath, 'r') as f: lines = f.readlines()
                    with open(fpath, 'w') as f:
                        for line in lines:
                            if line.startswith("ResolutionSizeX="): f.write(f"ResolutionSizeX={x}\n")
                            elif line.startswith("ResolutionSizeY="): f.write(f"ResolutionSizeY={y}\n")
                            elif line.startswith("FullscreenMode="): f.write("FullscreenMode=1\n")
                            else: f.write(line)
                    os.chmod(fpath, 0o444)
                except Exception: pass

    @staticmethod
    def kill_game():
        subprocess.run("taskkill /f /im VALORANT-Win64-Shipping.exe", shell=True, capture_output=True, creationflags=WinAPI.CREATE_NO_WINDOW)
        subprocess.run("taskkill /f /im RiotClientServices.exe", shell=True, capture_output=True, creationflags=WinAPI.CREATE_NO_WINDOW)

class EaseAnim:
    @staticmethod
    def ease_out_quint(t):
        return 1 - pow(1 - t, 5)
    
    @staticmethod
    def ease_out_sine(t):
        import math
        return math.sin((t * math.pi) / 2)
    
    @staticmethod
    def ease_out_cubic(t):
        return 1 - pow(1 - t, 3)
    
    @staticmethod
    def ease_out_expo(t):
        import math
        return 1 if t == 1 else 1 - pow(2, -10 * t)

class AnimatedButton(ctk.CTkFrame):
    def __init__(self, master, text, font, config_ref, command=None, fg_color="#FF4655", hover_color="#D82A3A", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.command = command
        self.cfg = config_ref
        self.base_color = fg_color
        self.press_color = hover_color
        self.btn = ctk.CTkButton(
            self, text=text, fg_color=self.base_color, hover_color=self.press_color, 
            text_color="#FFFFFF", font=font, corner_radius=6
        )
        self.btn.pack(fill="both", expand=True, pady=(0, 6))
        self.btn.bind("<Button-1>", self._on_press)
        self.btn.bind("<ButtonRelease-1>", self._on_release)
        self.btn.bind("<Leave>", self._on_leave)
        self.is_pressed = False

    def _on_press(self, event):
        self.is_pressed = True
        style = self.cfg["btn_anim_style"]
        if style == "Sink":
            self.btn.pack_configure(pady=(6, 0))
            self.btn.configure(fg_color=self.press_color)
        elif style == "Color Pulse":
            self.btn.configure(fg_color="#FFFFFF", text_color="#FF4655")

    def _on_release(self, event):
        if self.is_pressed:
            self.is_pressed = False
            self._reset_style()
            if self.command: self.after(50, self.command)

    def _on_leave(self, event):
        if self.is_pressed:
            self.is_pressed = False
            self._reset_style()

    def _reset_style(self):
        self.btn.pack_configure(pady=(0, 6))
        self.btn.configure(fg_color=self.base_color, text_color="#FFFFFF")

    def update_state(self, text, fg_color, hover_color):
        self.base_color = fg_color
        self.press_color = hover_color
        self.btn.configure(text=text, fg_color=fg_color, hover_color=hover_color)

ctk.set_appearance_mode("Dark")

class UltimateUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        if not WinAPI.is_admin():
            messagebox.showerror("Access Denied", "Run As Administrator required!")
            sys.exit()

        self.cfg = AppManager.load_config()
        self.game_running = False
        self._save_timer = None 
        self._typing_timer = None
        self._anim_task = None
        self.log_queue = []
        self.is_logging = False

        self.title("VALORANT CORE | ELITE EDITION")
        self.geometry("950x600")
        self.resizable(False, False)
        self.configure(fg_color="#09090B")
        self.protocol("WM_DELETE_WINDOW", self.on_force_exit)

        base_size = self.cfg["ui_font_scale"]
        self.font_h1 = ctk.CTkFont(family="Segoe UI", size=28, weight="bold")
        self.font_h2 = ctk.CTkFont(family="Segoe UI", size=base_size + 2, weight="bold")
        self.font_p = ctk.CTkFont(family="Segoe UI", size=base_size)
        self.font_btn = ctk.CTkFont(family="Segoe UI", size=base_size + 3, weight="bold")
        self.font_mono = ctk.CTkFont(family="Consolas", size=base_size - 2)

        self._build_ui()
        self._check_paths()

    def _build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color="#121214", border_width=1, border_color="#27272A")
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(5, weight=1)
        
        ctk.CTkLabel(sidebar, text="VAL-CORE", font=self.font_h1, text_color="#FF4655").pack(pady=(45, 2))
        ctk.CTkLabel(sidebar, text="E L I T E   E D I T I O N", font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"), text_color="#71717A").pack(pady=(0, 45))

        self.tabs = {}
        tab_list = [("home", "⯁  Dashboard"), ("engine", "⯁  Core Engine"), ("settings", "⯁  Settings"), ("about", "⯁  About")]
        for name, text in tab_list:
            btn = ctk.CTkButton(
                sidebar, text=text, fg_color="transparent", hover_color="#27272A", 
                anchor="w", font=self.font_h2, text_color="#FAFAFA"
            )
            btn.configure(command=lambda n=name: self._switch_tab(n))
            btn.pack(fill="x", padx=25, pady=6, ipady=6)
            self.tabs[name] = btn

        bottom_area = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom_area.pack(side="bottom", fill="x", padx=25, pady=35)

        self.btn_play = AnimatedButton(
            bottom_area, text="▶ INJECT GAME", font=self.font_btn, config_ref=self.cfg,
            command=self.handle_action_button, height=55
        )
        self.btn_play.pack(fill="x", pady=(0, 15))

        self.lbl_status = ctk.CTkLabel(bottom_area, text="● SYSTEM READY", text_color="#10B981", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"))
        self.lbl_status.pack(anchor="center")

        self.main_container = ctk.CTkFrame(self, fg_color="#09090B", corner_radius=0)
        self.main_container.grid(row=0, column=1, sticky="nsew")

        self.panels = {}
        
        pnl_home = ctk.CTkFrame(self.main_container, fg_color="transparent", corner_radius=0)
        box_res = ctk.CTkFrame(pnl_home, fg_color="#18181B", corner_radius=12, border_width=1, border_color="#27272A")
        box_res.pack(fill="x", padx=45, pady=(45, 20), ipadx=10, ipady=20)
        ctk.CTkLabel(box_res, text="STRETCHED RESOLUTION", font=self.font_h2, text_color="#A1A1AA").pack(pady=(0, 15))
        
        row_res = ctk.CTkFrame(box_res, fg_color="transparent")
        row_res.pack()
        self.ent_x = self._create_entry(row_res, str(self.cfg["default_stretched"]["x"]))
        ctk.CTkLabel(row_res, text="✕", font=self.font_h1, text_color="#52525B").pack(side="left", padx=25)
        self.ent_y = self._create_entry(row_res, str(self.cfg["default_stretched"]["y"]))

        self.log_area = tk.Text(
            pnl_home, bg="#0F0F12", fg="#E4E4E7", font=self.font_mono, 
            bd=0, state="disabled", highlightthickness=1, highlightbackground="#27272A", padx=15, pady=15
        )
        self.log_area.pack(fill="both", expand=True, padx=45, pady=(0, 45))
        for tag, color in [("sys", "#38BDF8"), ("ok", "#10B981"), ("err", "#EF4444"), ("hype", "#F59E0B")]:
            self.log_area.tag_configure(tag, foreground=color)
        
        self.panels["home"] = pnl_home

        pnl_engine = ctk.CTkFrame(self.main_container, fg_color="transparent", corner_radius=0)
        ctk.CTkLabel(pnl_engine, text="RIOT CLIENT PATH", font=self.font_h2, text_color="#A1A1AA").pack(anchor="w", padx=45, pady=(45, 10))
        row_path = ctk.CTkFrame(pnl_engine, fg_color="transparent")
        row_path.pack(fill="x", padx=45)
        self.ent_path = ctk.CTkEntry(row_path, state="normal", fg_color="#18181B", border_color="#27272A", height=45, font=self.font_p)
        self.ent_path.insert(0, self.cfg["valorant_path"] or "Not configured...")
        self.ent_path.configure(state="readonly")
        self.ent_path.pack(side="left", fill="x", expand=True, padx=(0, 15))
        ctk.CTkButton(row_path, text="Browse", width=100, height=45, font=self.font_h2, fg_color="#27272A", hover_color="#3F3F46", text_color="#FAFAFA", command=self._browse_path).pack(side="left")

        ctk.CTkLabel(pnl_engine, text="BEHAVIORAL OVERRIDES (AUTO-SAVE)", font=self.font_h2, text_color="#A1A1AA").pack(anchor="w", padx=45, pady=(50, 15))
        self.switches = {
            "true_stretched": self._create_switch(pnl_engine, "True Stretched Mode (Hardware Level Override)", self.cfg["true_stretched"]),
            "aggro_mode": self._create_switch(pnl_engine, "Aggressive Mode (Force-hide Taskbar during gameplay)", self.cfg["aggressive_mode"]),
            "pnp_toggle": self._create_switch(pnl_engine, "Monitor Pulse (Fix Windows 11 black bars issue)", self.cfg["monitor_toggle_enabled"]),
            "fps_boost": self._create_switch(pnl_engine, "CPU Priority Booster (Lock Max Frame Rates)", self.cfg["auto_high_priority"])
        }
        self.panels["engine"] = pnl_engine

        pnl_settings = ctk.CTkFrame(self.main_container, fg_color="transparent", corner_radius=0)
        ctk.CTkLabel(pnl_settings, text="UI CUSTOMIZATION", font=self.font_h2, text_color="#FF4655").pack(anchor="w", padx=45, pady=(45, 20))
        
        f_font = ctk.CTkFrame(pnl_settings, fg_color="transparent")
        f_font.pack(fill="x", padx=45, pady=15)
        ctk.CTkLabel(f_font, text="Global Font Scale:", font=self.font_p, width=150, anchor="w").pack(side="left")
        self.slider_font = ctk.CTkSlider(f_font, from_=10, to=18, number_of_steps=8, command=self._live_update_font, fg_color="#27272A", progress_color="#FF4655")
        self.slider_font.set(self.cfg["ui_font_scale"])
        self.slider_font.pack(side="left", fill="x", expand=True)

        f_anim = ctk.CTkFrame(pnl_settings, fg_color="transparent")
        f_anim.pack(fill="x", padx=45, pady=15)
        ctk.CTkLabel(f_anim, text="Animation Speed:", font=self.font_p, width=150, anchor="w").pack(side="left")
        self.slider_anim = ctk.CTkSlider(f_anim, from_=0.2, to=2.0, number_of_steps=18, command=self._live_update_anim, fg_color="#27272A", progress_color="#10B981")
        self.slider_anim.set(self.cfg["ui_anim_speed"])
        self.slider_anim.pack(side="left", fill="x", expand=True)

        f_btn = ctk.CTkFrame(pnl_settings, fg_color="transparent")
        f_btn.pack(fill="x", padx=45, pady=15)
        ctk.CTkLabel(f_btn, text="Inject Button Anim:", font=self.font_p, width=150, anchor="w").pack(side="left")
        self.opt_btn = ctk.CTkOptionMenu(f_btn, values=["Sink", "Color Pulse", "Minimal"], font=self.font_p, fg_color="#18181B", button_color="#27272A", command=self._live_update_btn)
        self.opt_btn.set(self.cfg["btn_anim_style"])
        self.opt_btn.pack(side="left", fill="x", expand=True)
        self.panels["settings"] = pnl_settings

        pnl_about = ctk.CTkFrame(self.main_container, fg_color="transparent", corner_radius=0)
        card = ctk.CTkFrame(pnl_about, fg_color="#121214", corner_radius=15, border_width=1, border_color="#27272A")
        card.pack(expand=True, fill="both", padx=60, pady=60)
        ctk.CTkLabel(card, text="V A L - C O R E", font=ctk.CTkFont(family="Impact", size=42), text_color="#FAFAFA").pack(pady=(50, 0))
        ctk.CTkLabel(card, text="E L I T E   E S P O R T S   E D I T I O N", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color="#FF4655").pack(pady=(5, 25))
        separator = ctk.CTkFrame(card, fg_color="#FF4655", height=2, width=80)
        separator.pack(pady=10)
        self.lbl_typewriter = ctk.CTkLabel(card, text="", font=self.font_p, text_color="#A1A1AA", justify="center")
        self.lbl_typewriter.pack(pady=20)
        ctk.CTkLabel(card, text="Designed for 0 Latency. Maximum Yield.", font=ctk.CTkFont(family="Consolas", size=10), text_color="#52525B").pack(side="bottom", pady=30)
        self.panels["about"] = pnl_about

        self._switch_tab("home")
        self._log("Elite Engine initialized. Awaiting orders.", "sys")

    def _create_entry(self, parent, val: str) -> ctk.CTkEntry:
        ent = ctk.CTkEntry(
            parent, width=120, height=55, font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"), 
            justify="center", fg_color="#09090B", border_color="#3F3F46", text_color="#FAFAFA"
        )
        ent.insert(0, val)
        ent.bind("<KeyRelease>", self._debounce_save)
        ent.pack(side="left")
        return ent

    def _create_switch(self, parent, text: str, val: bool) -> ctk.CTkSwitch:
        var = tk.BooleanVar(value=val)
        sw = ctk.CTkSwitch(
            parent, text=text, variable=var, command=self._instant_save, 
            progress_color="#FF4655", button_color="#FAFAFA", button_hover_color="#E4E4E7",
            font=self.font_p, text_color="#E4E4E7"
        )
        sw.pack(anchor="w", padx=45, pady=18)
        return var

    def _live_update_font(self, val):
        size = int(val)
        self.cfg["ui_font_scale"] = size
        self.font_h2.configure(size=size + 2)
        self.font_p.configure(size=size)
        self.font_btn.configure(size=size + 3)
        self.font_mono.configure(size=size - 2)
        self._debounce_save()

    def _live_update_anim(self, val):
        self.cfg["ui_anim_speed"] = float(val)
        self._debounce_save()

    def _live_update_btn(self, val):
        self.cfg["btn_anim_style"] = val
        self._debounce_save()

    def _switch_tab(self, name: str):
        if self._anim_task:
            self.after_cancel(self._anim_task)
            
        for k, btn in self.tabs.items(): 
            btn.configure(fg_color="#27272A" if k == name else "transparent")
        for pnl in self.panels.values(): 
            pnl.place_forget()
        
        if name == "about":
            self.lbl_typewriter.configure(text="")
            if self._typing_timer:
                self.after_cancel(self._typing_timer)
            self._typewriter_effect("Engineered for pure performance.\nAutomates environment optimization, strictly forces custom resolutions,\nand dynamically shifts CPU priority to guarantee minimum latency.", 0)

        target_panel = self.panels[name]
        start_time = time.time()
        duration = 0.5 / self.cfg["ui_anim_speed"] 
        self._slide_animation_step(target_panel, start_time, duration)

    def _slide_animation_step(self, panel, start_time, duration):
        elapsed = time.time() - start_time
        if elapsed >= duration:
            panel.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._anim_task = None
            return
        t = min(elapsed / duration, 1.0)
        ease = EaseAnim.ease_out_quint(t)
        current_x = 0.15 * (1 - ease)
        panel.place(relx=current_x, rely=0, relwidth=1, relheight=1)
        self._anim_task = self.after(5, self._slide_animation_step, panel, start_time, duration)  # Reduced from 8ms to 5ms (200fps)

    def _typewriter_effect(self, text, index):
        if index < len(text):
            current = self.lbl_typewriter.cget("text")
            self.lbl_typewriter.configure(text=current + text[index])
            self._typing_timer = self.after(8, self._typewriter_effect, text, index + 1)  # Reduced from 15ms to 8ms for smoother typing

    def _log(self, msg: str, tag: str="sys"):
        self.log_queue.append((msg, tag))
        if not self.is_logging:
            self._process_log_queue()

    def _process_log_queue(self):
        if not self.log_queue:
            self.is_logging = False
            return
        self.is_logging = True
        msg, tag = self.log_queue.pop(0)
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        AppManager.write_file_log(msg, tag)
        full_msg = f"[{ts}] [{tag.upper()}] {msg}\n"
        self.log_area.config(state="normal")
        self._typewrite_log(full_msg, tag, 0)

    def _typewrite_log(self, text, tag, index):
        if index < len(text):
            chunk = 3
            self.log_area.insert(tk.END, text[index:index+chunk], tag)
            self.log_area.see(tk.END)
            self.after(5, self._typewrite_log, text, tag, index + chunk)
        else:
            self.log_area.config(state="disabled")
            self._process_log_queue()

    def _debounce_save(self, event=None):
        if self._save_timer: self.after_cancel(self._save_timer)
        self._save_timer = self.after(500, self._instant_save) 

    def _instant_save(self):
        try:
            self.cfg["default_stretched"]["x"] = int(self.ent_x.get())
            self.cfg["default_stretched"]["y"] = int(self.ent_y.get())
        except ValueError: pass
        self.cfg["true_stretched"] = self.switches["true_stretched"].get()
        self.cfg["aggressive_mode"] = self.switches["aggro_mode"].get()
        self.cfg["monitor_toggle_enabled"] = self.switches["pnp_toggle"].get()
        self.cfg["auto_high_priority"] = self.switches["fps_boost"].get()
        AppManager.save_config(self.cfg)

    def _check_paths(self):
        if not self.cfg["valorant_path"]:
            for drive in ["C", "D", "E"]:
                p = rf"{drive}:\Riot Games\Riot Client\RiotClientServices.exe"
                if os.path.exists(p):
                    self._update_path(p)
                    self._log(f"Auto-detected Riot Client: {p}", "ok")
                    return
            self._log("Game path missing. Please configure in Core Engine.", "err")

    def _browse_path(self):
        p = filedialog.askopenfilename(title="Select RiotClientServices.exe", filetypes=[("Executable", "*.exe")])
        if p: self._update_path(p)

    def _update_path(self, p: str):
        self.cfg["valorant_path"] = p
        AppManager.save_config(self.cfg)
        self.ent_path.configure(state="normal")
        self.ent_path.delete(0, tk.END)
        self.ent_path.insert(0, p)
        self.ent_path.configure(state="readonly")

    def handle_action_button(self):
        if self.game_running or self.btn_play.btn.cget("text") == "ABORT ENGINE":
            self._log("Emergency termination triggered!", "err")
            WinAPI.kill_game()
            self._cleanup_to_idle()
        else:
            self.boot_sequence()

    def boot_sequence(self):
        if not self.cfg["valorant_path"]:
            self._switch_tab("settings")
            return self._log("Invalid Executable Path!", "err")

        self.btn_play.update_state("ABORT ENGINE", fg_color="#EF4444", hover_color="#B91C1C")
        self.lbl_status.configure(text="● INITIALIZING...", text_color="#38BDF8")
        threading.Thread(target=self._core_thread, daemon=True).start()

    def _core_thread(self):
        try:
            res_x, res_y = self.cfg["default_stretched"]["x"], self.cfg["default_stretched"]["y"]
            
            if not WinAPI.is_resolution_supported(res_x, res_y):
                self._log(f"Error: Resolution {res_x}x{res_y} is not supported by your GPU!", "err")
                self.after(0, self._cleanup_to_idle)
                return

            self._log("Applying resolution overdrive...", "sys")
            WinAPI.patch_game_config(res_x, res_y)
            
            if self.cfg.get("true_stretched", True):
                if not AppManager.apply_qres(res_x, res_y):
                    if not WinAPI.force_resolution(res_x, res_y):
                        self._log("Warning: Resolution could not be forced via native API.", "err")
                    else:
                        self._log(f"Resolution forced via native API ({res_x}x{res_y}).", "ok")
                else:
                    self._log(f"Resolution applied via qres ({res_x}x{res_y}).", "ok")
            else:
                if not WinAPI.force_resolution(res_x, res_y):
                    self._log("Warning: Native API failed to force resolution.", "err")
                else:
                    self._log(f"Resolution forced via native API ({res_x}x{res_y}).", "ok")

            if self.cfg["aggressive_mode"]: WinAPI.toggle_taskbar(hide=True)
            if self.cfg["monitor_toggle_enabled"]: WinAPI.pulse_pnp_monitor()

            self._log(f"Injecting Riot Client (Forcing {res_x}x{res_y})...", "sys")
            cmd = f'"{self.cfg["valorant_path"]}" --launch-product=valorant --launch-patchline=live'
            subprocess.Popen(cmd, shell=True, creationflags=WinAPI.CREATE_NO_WINDOW)

            timeout = 90
            target_pid = None
            while timeout > 0:
                try:
                    for p in psutil.process_iter(['name', 'pid']):
                        try:
                            if p.info['name'] == "VALORANT-Win64-Shipping.exe":
                                target_pid = p.info['pid']
                                break
                        except (psutil.NoSuchProcess, psutil.AccessDenied): continue
                except Exception: pass
                if target_pid: break
                time.sleep(1)
                timeout -= 1

            if not target_pid:
                self._log("Boot failed or cancelled.", "err")
                self.after(0, self._cleanup_to_idle)
                return

            self.game_running = True
            self.lbl_status.configure(text="● CONNECTING...", text_color="#F59E0B")
            self._log("Process detected. Waiting for Lobby to load...", "sys")

            time.sleep(15)
            self._log("UNLEASH YOUR POWER! ⚔️", "hype")
            self.lbl_status.configure(text="● READY FOR ACTION", text_color="#FF4655")

            if self.cfg.get("auto_high_priority", True):
                try:
                    psutil.Process(target_pid).nice(psutil.HIGH_PRIORITY_CLASS)
                    self._log("CPU Priority Booster Engaged (Max FPS locked).", "ok")
                except Exception: pass

            proc = psutil.Process(target_pid)
            while True:
                try:
                    if not proc.is_running() or proc.status() == psutil.STATUS_ZOMBIE: break
                except psutil.NoSuchProcess: break
                time.sleep(3)

        except Exception as e:
            self._log(f"System Error: {str(e)}", "err")
        finally:
            if self.game_running:
                self._log("Game terminated. System standing by.", "sys")
            self.after(0, self._cleanup_to_idle)

    def _cleanup_to_idle(self):
        self.game_running = False
        WinAPI.force_resolution(self.cfg["exit_res"].get("x", 1920), self.cfg["exit_res"].get("y", 1080))
        WinAPI.toggle_taskbar(hide=False)
        self.lbl_status.configure(text="● SYSTEM READY", text_color="#10B981")
        self.btn_play.update_state("▶ INJECT GAME", fg_color="#FF4655", hover_color="#D82A3A")

    def on_force_exit(self):
        self.game_running = False
        WinAPI.force_resolution(self.cfg["exit_res"].get("x", 1920), self.cfg["exit_res"].get("y", 1080))
        WinAPI.toggle_taskbar(hide=False)
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    app = UltimateUI()
    app.mainloop()