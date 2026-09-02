import os
import sys
import shutil
import subprocess

def run_step(cmd, desc):
    print(f"\n========================================================", flush=True)
    print(f"[+] {desc}...", flush=True)
    print(f"========================================================", flush=True)
    res = subprocess.run(cmd, shell=True)
    if res.returncode != 0:
        print(f"[X] Error during: {desc}", flush=True)
        sys.exit(res.returncode)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    obf_dir = os.path.join(base_dir, "dist_obf")
    staging_dir = os.path.join(base_dir, "build_staging")

    # 1. Terminate any running instance of SA-RP Linggo.exe
    print("[1/5] Terminating running SA-RP Linggo.exe processes if active...", flush=True)
    subprocess.run('taskkill /F /IM "SA-RP Linggo.exe"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 2. Obfuscate core package with PyArmor
    run_step("python -m pyarmor.cli gen -O dist_obf core", "[2/5] Obfuscating core logic modules with PyArmor")

    # 3. Create build staging directory
    if os.path.exists(staging_dir):
        shutil.rmtree(staging_dir)
    os.makedirs(staging_dir, exist_ok=True)

    print("[3/5] Setting up protected build staging environment...", flush=True)
    # Copy main.py and ui folder
    shutil.copy(os.path.join(base_dir, "main.py"), os.path.join(staging_dir, "main.py"))
    shutil.copytree(os.path.join(base_dir, "ui"), os.path.join(staging_dir, "ui"))

    # Copy obfuscated core folder and pyarmor_runtime
    shutil.copytree(os.path.join(obf_dir, "core"), os.path.join(staging_dir, "core"))

    # Copy pyarmor_runtime runtime package into staging
    runtime_folder = None
    for f in os.listdir(obf_dir):
        if f.startswith("pyarmor_runtime"):
            runtime_folder = f
            shutil.copytree(os.path.join(obf_dir, f), os.path.join(staging_dir, f))
            break

    # 4. Compile with PyInstaller
    hidden_imports = "--hidden-import requests --hidden-import keyboard --hidden-import sounddevice --hidden-import numpy --hidden-import wave --hidden-import pyperclip --hidden-import PyQt6.QtSvg"
    run_step(
        f'python -m PyInstaller --noconfirm --onefile --windowed {hidden_imports} --name "SA-RP Linggo" "{os.path.join(staging_dir, "main.py")}"',
        "[4/5] Compiling Protected Standalone Executable (.exe)"
    )

    # 5. Cleanup temporary staging directories
    print("[5/5] Cleaning up temporary build artifacts...", flush=True)
    try:
        if os.path.exists(obf_dir):
            shutil.rmtree(obf_dir)
        if os.path.exists(staging_dir):
            shutil.rmtree(staging_dir)
    except Exception as e:
        print(f"Warning cleanup: {e}", flush=True)

    print("\n========================================================", flush=True)
    print("PROTECTED BUILD SUCCESSFUL!", flush=True)
    print(f"Anti-Decompile Binary Saved to: {os.path.join(base_dir, 'dist', 'SA-RP Linggo.exe')}", flush=True)
    print("========================================================\n", flush=True)

if __name__ == "__main__":
    main()
