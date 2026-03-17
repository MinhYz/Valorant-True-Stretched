@echo off
:: Kiểm tra quyền Admin
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"

:: Nếu chưa có quyền Admin, nó sẽ tự động gọi lệnh yêu cầu quyền
if '%errorlevel%' NEQ '0' (
    echo Dang yeu cau quyen Administrator...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )
    pushd "%~dp0"

:: --- PHẦN CODE CHÍNH CỦA BẠN Ở DƯỚI ĐÂY ---
python Stretche.py
pause