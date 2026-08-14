@echo off
REM WINDOWS icin: bu dosyaya cift tikla.
cd /d "%~dp0"
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)
python baslat.py
pause
