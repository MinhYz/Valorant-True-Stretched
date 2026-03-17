@echo off
cd /d "%~dp0"

:: Ẩn taskbar trước khi chạy game
echo Taskbar disable..
powershell -command "&{$p='HKCU:SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StuckRects3';$v=(Get-ItemProperty -Path $p).Settings;$v[8]=3;&Set-ItemProperty -Path $p -Name Settings -Value $v;&Stop-Process -f -ProcessName explorer}"


:: Chạy Womic 
Echo Running Womic
start "D:\WOmic\WOMicClient.exe"

:: Khởi chạy game
start "" "D:\Riot Games\Riot Client\RiotClientServices.exe" --launch-product=valorant --launch-patchline=live
echo Valorant is running...

:waitlaunch
tasklist | findstr /i "VALORANT-Win64-Shipping.exe VALORANT.exe" >nul
if %errorlevel% NEQ 0 (
    timeout /t 1 >nul
    goto waitlaunch
)

:: Đợi ổn định
timeout /t 5 >nul

:: Đổi sang stretched
QRes.exe /x:1280 /y:960

:: Đợi đến khi game đóng
:waitclose
timeout /t 5 >nul
tasklist | findstr /i "VALORANT-Win64-Shipping.exe VALORANT.exe" >nul
if %errorlevel%==0 goto waitclose

:: Trả lại độ phân giải
QRes.exe /x:1920 /y:1080

:: Hiện lại taskbar
powershell -command "&{$p='HKCU:SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StuckRects3';$v=(Get-ItemProperty -Path $p).Settings;$v[8]=2;&Set-ItemProperty -Path $p -Name Settings -Value $v;&Stop-Process -f -ProcessName explorer}"
start explorer.exe

echo Bye Bye!
pause
