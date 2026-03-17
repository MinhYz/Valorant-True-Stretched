import subprocess
import time
import psutil
import winreg
import os
import json
import ctypes
import sys
from tkinter import Tk, filedialog
from colorama import init, Fore

# Initialize colors
init(autoreset=True)

# Constants for Windows API
SPI_SETMOUSESPEED = 0x0071
SPI_GETMOUSESPEED = 0x0070
SPI_SETMOUSE = 0x0004
SW_HIDE = 0
SW_SHOW = 5

ASCII_ART = r"""
 ██▒   █▓ ▄▄▄         ██▓     ▒█████    ██▀███   ▄▄▄         ███▄   █ ▄▄▄█████▓
▓██░   █▒▒████▄      ▓██▒     ▒██▒   ██▒▓██ ▒ ██▒▒████▄       ██ ▀█   █ ▓  ██▒ ▓▒
 ▓██  █▒░▒██  ▀█▄    ▒██░     ▒██░   ██▒▓██ ░▄█ ▒▒██  ▀█▄     ▓██  ▀█ ██▒▒ ▓██░ ▒░
  ▒██ █░░░██▄▄▄▄██  ▒██░     ▒██   ██░▒██▀▀█▄  ░██▄▄▄▄██  ▓██▒  ▐▌██▒░ ▓██▓ ░ 
   ▒▀█░   ▓█   ▓██▒░██████▒░ ████▓▒░░██▓ ▒██▒ ▓█   ▓██▒▒██░   ▓██░  ▒██▒ ░ 
"""

class ConfigManager:
    def __init__(self, folder_name="config", file_name="settings.json"):
        # Create config folder if it doesn't exist
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            print(Fore.YELLOW + f"[*] Created directory: {folder_name}")
            
        self.path = os.path.join(folder_name, file_name)
        self.config = self.load_config()

    def choose_file(self, title):
        root = Tk()
        root.withdraw()
        path = filedialog.askopenfilename(title=title)
        root.destroy()
        return path

    def load_config(self):
        default = {
            "run_womic": False,
            "womic_path": "",
            "valorant_path": "",
            "game_res": {"x": 1280, "y": 960},
            "exit_res": {"x": 1920, "y": 1080},
            "mouse_settings": {"game_speed": 10, "disable_accel": True}
        }
        
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                # Ensure all keys exist
                for k, v in default.items():
                    if k not in cfg: 
                        cfg[k] = v
                self.config = cfg
        else:
            self.config = default

        changed = False
        if not self.config.get("valorant_path"):
            print(Fore.YELLOW + "[CONFIG] Selecting Valorant path...")
            self.config["valorant_path"] = self.choose_file("Select RiotClientServices.exe")
            changed = True
            
        if changed: 
            self.save_config()
            
        return self.config

    def save_config(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)

class SystemOptimizer:
    def __init__(self):
        self.original_speed = self.get_mouse_speed()

    @staticmethod
    def get_mouse_speed():
        speed = ctypes.c_int()
        ctypes.windll.user32.SystemParametersInfoW(SPI_GETMOUSESPEED, 0, ctypes.byref(speed), 0)
        return speed.value

    def apply_mouse_settings(self, speed, disable_accel):
        ctypes.windll.user32.SystemParametersInfoW(SPI_SETMOUSESPEED, 0, speed, 0)
        if disable_accel:
            params = (ctypes.c_int * 3)(0, 0, 0)
            ctypes.windll.user32.SystemParametersInfoW(SPI_SETMOUSE, 0, params, 1)
        print(Fore.GREEN + f"[OK] Mouse: Speed {speed} | Accel: {'OFF' if disable_accel else 'ON'}")

    @staticmethod
    def set_nvidia_settings():
        print(Fore.CYAN + "[*] Checking NVIDIA Scaling...")
        path = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_ALL_ACCESS) as key:
                try:
                    scaling_val, _ = winreg.QueryValueEx(key, "Scaling")
                except FileNotFoundError:
                    scaling_val = None
                    
                try:
                    override_val, _ = winreg.QueryValueEx(key, "Scaling.Override")
                except FileNotFoundError:
                    override_val = None

                # Check for "Full-screen" (Scaling = 2) AND "Override..." checkbox (Scaling.Override = 1)
                if scaling_val == 2 and override_val == 1:
                    print(Fore.YELLOW + "[SKIP] NVIDIA is already set to Full-screen with Override enabled.")
                    return

                # Apply settings if not already correct
                winreg.SetValueEx(key, "Scaling", 0, winreg.REG_DWORD, 2)
                try:
                    # Attempt to set the override checkbox
                    winreg.SetValueEx(key, "Scaling.Override", 0, winreg.REG_DWORD, 1)
                except Exception as e:
                    print(Fore.RED + f"[!] Could not set Scaling.Override: {e}")
                
                print(Fore.GREEN + "[OK] NVIDIA Registry updated to Full-screen with Override.")
        except Exception as e: 
            print(Fore.RED + f"[!] NVIDIA Registry access failed: {e}")

    @staticmethod
    def toggle_taskbar(show=True):
        hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
        ctypes.windll.user32.ShowWindow(hwnd, SW_SHOW if show else SW_HIDE)

    @staticmethod
    def run_qres(x, y):
        qres = os.path.join(os.getcwd(), "QRes.exe")
        if os.path.exists(qres):
            subprocess.run([qres, f"/x:{x}", f"/y:{y}"], capture_output=True)

def main():
    manager = ConfigManager()
    opt = SystemOptimizer()
    cfg = manager.config

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(Fore.RED + ASCII_ART)
        
        opt.set_nvidia_settings()
        opt.apply_mouse_settings(cfg["mouse_settings"]["game_speed"], cfg["mouse_settings"]["disable_accel"])
        
        print(Fore.CYAN + "[1] Hiding Taskbar...")
        opt.toggle_taskbar(False)

        print(Fore.CYAN + "[2] Launching Valorant...")
        subprocess.Popen(f'"{cfg["valorant_path"]}" --launch-product=valorant --launch-patchline=live', shell=True)

        print(Fore.YELLOW + "[3] Waiting for game...")
        while not any("VALORANT-Win64-Shipping" in p.name() for p in psutil.process_iter()):
            time.sleep(1)

        opt.run_qres(cfg['game_res']['x'], cfg['game_res']['y'])
        print(Fore.GREEN + "\n>>> GOOD LUCK<<<")

        while any("VALORANT-Win64-Shipping" in p.name() for p in psutil.process_iter()):
            time.sleep(5)

        print(Fore.YELLOW + "\n[!] Game closed. Restoring...")
        opt.run_qres(cfg['exit_res']['x'], cfg['exit_res']['y'])
        opt.toggle_taskbar(True)
        opt.apply_mouse_settings(opt.original_speed, False) 

        if input(Fore.WHITE + "Press Enter to restart or type 'exit': ").lower() == 'exit': break

if __name__ == "__main__":
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print(Fore.RED + "RUN AS ADMINISTRATOR REQUIRED!")
        sys.exit()
    main()