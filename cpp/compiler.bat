@echo off
echo.
-- Forces the batch file to focus on the folder it is located in
cd /d "%~dp0"

set file=noname.cpp
set out=noname.exe

where g++ >nul 2>&1
if %errorlevel% equ 0 (
    echo [SYSTEM] G++ installed! Compiling %file%...
    g++ -o "%out%" "%file%"
) else (
    echo.
    echo [SYSTEM] G++ is not installed!
)