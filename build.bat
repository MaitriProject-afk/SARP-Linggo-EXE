@echo off
echo ========================================================
echo Building SA-RP Linggo Protected Executable (.exe)...
echo ========================================================

pip install -r requirements.txt
pip install pyinstaller pyarmor

python build_protected.py

pause
