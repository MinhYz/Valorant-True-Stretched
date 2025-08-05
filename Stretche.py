import subprocess
import time
import psutil
import winreg
import os
import json
import ctypes
from tkinter import Tk, filedialog
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Banner
ascii_art = r"""
 ██▒   █▓ ▄▄▄       ██▓     ▒█████   ██▀███   ▄▄▄       ███▄    █ ▄▄▄█████▓
▓██░   █▒▒████▄    ▓██▒    ▒██▒  ██▒▓██ ▒ ██▒▒████▄     ██ ▀█   █ ▓  ██▒ ▓▒
 ▓██  █▒░▒██  ▀█▄  ▒██░    ▒██░  ██▒▓██ ░▄█ ▒▒██  ▀█▄  ▓██  ▀█ ██▒▒ ▓██░ ▒░
  ▒██ █░░░██▄▄▄▄██ ▒██░    ▒██   ██░▒██▀▀█▄  ░██▄▄▄▄██ ▓██▒  ▐▌██▒░ ▓██▓ ░ 
   ▒▀█░   ▓█   ▓██▒░██████▒░ ████▓▒░░██▓ ▒██▒ ▓█   ▓██▒▒██░   ▓██░  ▒██▒ ░ 
   ░ ▐░   ▒▒   ▓▒█░░ ▒░▓  ░░ ▒░▒░▒░ ░ ▒▓ ░▒▓░ ▒▒   ▓▒█░░ ▒░   ▒ ▒   ▒ ░░   
   ░ ░░    ▒   ▒▒ ░░ ░ ▒  ░  ░ ▒ ▒░   ░▒ ░ ▒░  ▒   ▒▒ ░░ ░░   ░ ▒░    ░    
     ░░    ░   ▒     ░ ░   ░ ░ ░ ▒    ░░   ░   ░   ▒      ░   ░ ░   ░      
      ░        ░  ░    ░  ░    ░ ░     ░           ░  ░         ░          
     ░                                                                     
"""
print(Fore.RED + ascii_art)

# === CONFIG ===

def choose_file_dialog(title):
    root = Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title=title)
    root.destroy()
    return file_path

def load_config(path="config.json"):
    default_config = {
        "run_womic": False,
        "womic_path": "",
        "valorant_path": "",
        "game_resolution": {"x": 1280, "y": 960},
        "exit_resolution": {"x": 1920, "y": 1080}
    }

    if not os.path.exists(path):
        print(Fore.YELLOW + "[CONFIG] First-time setup: Please choose paths for Valorant and WO Mic.")
        womic_path = choose_file_dialog("Select WO Mic Client (WOMicClient.exe)")
        valorant_path = choose_file_dialog("Select Riot Client (RiotClientServices.exe)")

        default_config["womic_path"] = womic_path
        default_config["valorant_path"] = valorant_path

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4)
            print(Fore.GREEN + f"[CONFIG] Config saved to: {path}")
            return default_config
        except Exception as e:
            print(Fore.RED + f"[CONFIG ERROR] Failed to save config: {e}")
            return default_config
    else:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(Fore.RED + f"[CONFIG ERROR] Failed to read config: {e}")
            return default_config

# === HELPERS ===

def set_taskbar_visibility(visible: bool):
    key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StuckRects3"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
            settings, regtype = winreg.QueryValueEx(key, "Settings")
            settings = bytearray(settings)
            settings[8] = 2 if visible else 3
            winreg.SetValueEx(key, "Settings", 0, regtype, bytes(settings))
        subprocess.run("taskkill /f /im explorer.exe", shell=True)
        subprocess.Popen("explorer.exe", shell=True)
    except Exception as e:
        print(Fore.YELLOW + f"[TASKBAR ERROR] {e}")

def is_process_running(name):
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and name.lower() in proc.info['name'].lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def run_qres(x, y):
    qres_path = os.path.join(os.getcwd(), "QRes.exe")
    if not os.path.exists(qres_path):
        print(Fore.RED + "[QRES ERROR] QRes.exe not found!")
        return
    subprocess.run([qres_path, f"/x:{x}", f"/y:{y}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def run_program(path):
    if os.path.exists(path):
        subprocess.Popen(f'"{path}"', shell=True)
    else:
        print(Fore.RED + f"[LAUNCH ERROR] Path not found: {path}")

# === MAIN ===

config = load_config()

print(Fore.CYAN + "[1] Hiding Taskbar...")
set_taskbar_visibility(False)

if config.get("run_womic", False):
    print(Fore.CYAN + "[2] Checking WO Mic...")
    if not is_process_running("WOMicClient"):
        run_program(config.get("womic_path", ""))
        print(Fore.CYAN + "[2] WO Mic launched.")
    else:
        print(Fore.CYAN + "[2] WO Mic already running.")
else:
    print(Fore.YELLOW + "[2] Skipping WO Mic...")

print(Fore.CYAN + "[3] Launching Valorant...")
run_program(config.get("valorant_path", "") + " --launch-product=valorant --launch-patchline=live")

print(Fore.YELLOW + "[4] Waiting for Valorant to start...")
while not is_process_running("VALORANT-Win64-Shipping"):
    time.sleep(1)

res_game = config.get("game_resolution", {"x": 1280, "y": 960})
print(Fore.CYAN + f"[5] Setting resolution to {res_game['x']}x{res_game['y']}...")
run_qres(res_game["x"], res_game["y"])

print(Fore.YELLOW + "[6] Valorant is running...")
while is_process_running("VALORANT-Win64-Shipping"):
    time.sleep(5)

res_exit = config.get("exit_resolution", {"x": 1920, "y": 1080})
print(Fore.CYAN + f"[7] Restoring resolution to {res_exit['x']}x{res_exit['y']}...")
run_qres(res_exit["x"], res_exit["y"])

print(Fore.CYAN + "[8] Restoring Taskbar...")
set_taskbar_visibility(True)

print(Fore.GREEN + "\nFinished.")
input("Press Enter to exit...")
