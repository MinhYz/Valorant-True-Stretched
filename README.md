# True Stretched - Valorant Optimizer

A clean and efficient Python script designed to automate system optimizations and force "True Stretched" resolution for Valorant players.

## ✨ Key Features

- **Auto-Resolution**
The script uses QRes.exe to automatically switch your monitor to your stretched resolution (e.g., 1280x960) when the game starts. Once you close the game, it instantly restores your native resolution.

- **Deep Config Injection (True Stretched)**
It deep-scans your `%LOCALAPPDATA%\VALORANT\Saved\Config` folder to find all `GameUserSettings.ini` files. It automatically forces your custom resolution, sets `FullscreenMode=1`, and disables letterboxing (`bShouldLetterbox=False`) directly into the game's engine for a flawless stretched experience.

- **Mouse Precision**
It forces a specific Windows mouse speed and disables "Enhance Pointer Precision" (Mouse Acceleration) via system API to ensure your aim remains raw and consistent.

- **NVIDIA Scaling Guard**
The script checks your Windows Registry to ensure NVIDIA Scaling is set to "Full-screen" with the scaling override enabled. If it is already configured correctly, the script intelligently skips this step.

- **Smart Taskbar Hider**
Using direct Windows API calls, the script hides the Taskbar when you are in-game to prevent any focus issues or accidental clicks, restoring it automatically when you exit.

- **Secondary Monitor Toggle**
If enabled, it automatically disconnects your second monitor while the game is running (to maximize performance and prevent the mouse from drifting off-screen), then safely restores it after you close the game.

- **Process Monitoring**
It continuously monitors system processes to detect exactly when Valorant starts and stops, making the entire optimization cycle fully hands-free.

## 🛠 Requirements

- **Operating System:** Windows 10 or Windows 11.
- **Python Version:** Python 3.x installed.
- **External Utility:** QRes.exe must be located in the same folder as the script.
- **Python Modules:** psutil and colorama.

## 📦 Installation

1. Install the necessary Python libraries using pip:
   `pip install psutil colorama`

2. Download the `Stretche.py` script and place it in a dedicated folder.

3. Ensure `QRes.exe` is in that same folder.

## ⚙️ Configuration Explained

After your first launch, a `settings.json` file will be generated inside a `config` folder. Here is what each setting does:

- **game_res:** Defines the width (x) and height (y) for your stretched resolution.
- **exit_res:** Defines the width (x) and height (y) for your native desktop resolution.
- **mouse_settings:** - **game_speed:** Sets your Windows pointer speed (usually 10 for default).
  - **disable_accel:** Set to true to turn off Windows mouse acceleration.
- **disable_monitor:** Set to true if you want the script to automatically disable your secondary monitor while playing, and false to keep it on.
- **valorant_path:** Stores the location of your RiotClientServices.exe so you don't have to select it again.

## 🚀 How to Use

1. Open your terminal (PowerShell or CMD) as **Administrator** (Required to modify Registry and Mouse settings).
2. Navigate to your folder and run the script:
   `python Stretche.py`
3. The script will ask you to locate your Valorant executable if it's the first time.
4. Keep the script running in the background. Once you launch the game, the script handles the rest automatically.

---
*Developed by Minh*
