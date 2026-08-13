@echo off
echo.
-- Forces the batch file to focus on the folder it is located in
cd /d "%~dp0"

set file=noname.c
set out=noname.exe

where gcc >nul 2>&1
if %errorlevel% equ 0 (
    echo [SYSTEM] GCC installed! Compiling %file%...
    gcc -o "%out%" "%file%"
) else (
    echo.
    echo [SYSTEM] GCC is not installed!
)
