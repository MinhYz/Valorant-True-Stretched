# ⚔️ VALORANT CORE | ELITE EDITION

**VALORANT CORE** is a high-performance system utility engineered for competitive players who demand a perfect "True Stretched" experience. This tool automates complex environment optimizations, ensuring zero latency and maximum visual clarity with a single click.

## ✨ Elite Features

- **True Stretched Overdrive**: Forces hardware-level resolution scaling using embedded `qres` and native Win32 kernel APIs.
- **GPU Safety Radar**: Real-time hardware scanning validates custom resolutions before deployment to prevent display hangs or black screens.
- **High-Fidelity Animations**: Delta-time based 144Hz smooth transitions (Ease-Out-Quint) for a premium, responsive UI feel.
- **CPU Priority Booster**: Dynamically elevates Valorant to "High Priority" in the Windows kernel to minimize frame-time variance and input lag.
- **Aggressive Environment Control**: Automatic Taskbar management and PnP monitor pulsing to fix common Windows 11 stretching bugs.
- **Persistent Log Console**: Real-time feedback and session history remain available after game termination for performance auditing.

## 🚀 Setup & Build

### Prerequisites
- Windows 10/11 (64-bit)
- **Run as Administrator** (Required for display and process priority modifications)

### Installation
1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Build the standalone executable:
   ```bash
   python -m PyInstaller --noconsole --onefile --icon=valorant_logo.ico --add-data "qres.exe;." Stretche.py
   ```

## 🎮 How to Use

1. **Dashboard**: Enter your target resolution (e.g., `1280x960`). The system will automatically validate and save your settings.
2. **Core Engine**: Ensure your Riot Client path is detected. Toggle advanced behaviors like *FPS Booster* or *Monitor Pulse*.
3. **Settings**: Fine-tune the UI font scale and animation speed to match your monitor's refresh rate.
4. **Deploy**: Click **▶ INJECT GAME**. The tool will optimize your PC and launch the game.
5. **Session End**: When you close Valorant, the tool will restore your native desktop resolution and log the session results.

## 🛠 Technical Stack
- **Framework**: CustomTkinter (Modern Fluent Design)
- **Engine**: Python 3.14 / Win32 API
- **Optimization**: Time-based Delta Interpolation
- **Utilities**: QRes (Hardware Scaling)

## ⚠️ Disclaimer
VALORANT CORE modifies system-level display settings and process priorities. It does not interfere with game memory or local files, ensuring compliance with standard anti-cheat policies. However, use it at your own risk. Not affiliated with Riot Games.

---
*Engineered for 0 Latency. Maximum Yield.*
