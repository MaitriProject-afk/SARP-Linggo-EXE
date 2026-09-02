import sys
import os
import signal
import ctypes
import requests
import keyboard
import sounddevice
import numpy
import wave
import pyperclip
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QMessageBox
from core.config import ConfigManager
from core.chat_listener import ChatlogListener
from core.clipboard_listener import ClipboardListener
from core.translator import GroqTranslator, TranslationWorker
from ui.overlay import OverlayWindow

mutex_handle = None

def acquire_single_instance_lock():
    """Prevents multiple instances of SA-RP Linggo from running simultaneously."""
    global mutex_handle
    if os.name == 'nt':
        mutex_name = "Global\\SARPLinggoSingleInstanceMutex"
        kernel32 = ctypes.windll.kernel32
        mutex_handle = kernel32.CreateMutexW(None, False, mutex_name)
        last_error = kernel32.GetLastError()
        ERROR_ALREADY_EXISTS = 183
        if last_error == ERROR_ALREADY_EXISTS:
            return False
    return True

def main():
    print("[SA-RP Linggo] Starting overlay application...", flush=True)
    
    # Enable Ctrl+C interrupt in console/terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Enable High DPI scaling for Windows
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    app = QApplication(sys.argv)
    app.setApplicationName("SA-RP Linggo")
    app.setQuitOnLastWindowClosed(False)

    # 0. Enforce Single Instance
    if not acquire_single_instance_lock():
        print("[SA-RP Linggo] Another instance is already running!", flush=True)
        QMessageBox.warning(
            None,
            "SA-RP Linggo Sudah Berjalan",
            "Aplikasi SA-RP Linggo sudah berjalan di latar belakang (Background)!\n\nSilakan cek ikon System Tray di kanan bawah taskbar."
        )
        sys.exit(0)

    # Periodically process Python signals to handle Ctrl+C instantly
    sig_timer = QTimer()
    sig_timer.start(200)
    sig_timer.timeout.connect(lambda: None)

    # 1. Load Configuration
    config = ConfigManager()

    # 2. Initialize Overlay UI
    overlay = OverlayWindow(config)
    overlay.show()

    # 3. Initialize Groq Translator
    api_key = config.get("groq_api_key", "")
    model = config.get("groq_model", "openai/gpt-oss-20b")
    target_lang = config.get("target_language", "Indonesian")

    dev_mode = config.get("developer_mode", False)
    translator = GroqTranslator(
        api_key=api_key,
        model=model,
        target_lang=target_lang,
        developer_mode=dev_mode
    )
    overlay.set_translator(translator)
    trans_worker = TranslationWorker(translator)
    trans_worker.start()

    # 4. Initialize Chatlog Listener
    chatlog_path = config.get("chatlog_path", "")
    use_codsmp = config.get("use_codsmp", True)
    chat_listener = ChatlogListener(chatlog_path=chatlog_path, use_codsmp=use_codsmp)
    chat_listener.start()

    # 5. Initialize License Manager, Clipboard Listener & Voice Listener
    from core.licensing import LicenseManager
    from core.voice_listener import VoiceListener
    license_mgr = LicenseManager()

    clipboard_listener = ClipboardListener(translator=translator, config_manager=config, license_manager=license_mgr)
    voice_listener = VoiceListener(translator=translator, config_manager=config, license_manager=license_mgr)
    voice_listener.clipboard_listener = clipboard_listener
    voice_listener.start()

    # 6. Connect Signal Flow
    def on_new_chat_line(chat_item):
        if not license_mgr.is_active():
            overlay.set_status("🔒 UNLICENSED (Enter Token in Settings)", "#EF4444")
            return
        chat_type = chat_item.get("type", "SAYS")
        if chat_type == "SAYS" and not config.get("auto_translate_ic", True):
            return
        if chat_type in ["ME", "DO"] and not config.get("auto_translate_me_do", True):
            return
        trans_worker.add_job(chat_item)

    def on_translation_done(chat_item):
        overlay.add_chat_card(chat_item)

    def on_listener_status(status_msg):
        if not license_mgr.is_active():
            overlay.set_status("🔒 UNLICENSED (Enter Token in Settings)", "#EF4444")
            return
        if "Monitoring" in status_msg:
            status_text = "🔒 Click-Through" if overlay.is_locked else "🟢 Move Mode"
            color = "#EF4444" if overlay.is_locked else "#10B981"
            overlay.set_status(status_text, color)
        elif "Error" in status_msg or "not found" in status_msg.lower():
            overlay.set_status("⚠️ Check Chatlog Path", "#F59E0B")
        else:
            overlay.set_status(status_msg, "#A0AEC0")

    def on_outbound_translated(item_data):
        if not license_mgr.is_active():
            overlay.set_status("🔒 UNLICENSED (Enter Token in Settings)", "#EF4444")
            return
        if item_data.get("type") == "OUTBOUND_IGNORED":
            orig = item_data.get("original", "")[:35]
            reason = item_data.get("reason", "Bukan B.Indonesia")
            overlay.set_status(f"ℹ️ Clipboard Diabaikan ({reason}): \"{orig}...\"", "#F59E0B")
            return
        overlay.add_chat_card(item_data)
        if item_data.get("error"):
            err_msg = item_data.get("error")
            overlay.set_status(f"⚠️ {err_msg}", "#EF4444")
        else:
            rpd_rem = item_data.get("rpd_remaining")
            rpd_lim = item_data.get("rpd_limit")
            rpd_str = f" | RPD: {rpd_rem}/{rpd_lim if rpd_lim else 1000}" if rpd_rem is not None else ""
            overlay.set_status(f"● Outbound Ready! (Press CTRL+V){rpd_str}", "#06B6D4")

    def on_voice_status(status_msg, color_hex):
        if not license_mgr.is_active():
            overlay.set_status("🔒 UNLICENSED (Enter Token in Settings)", "#EF4444")
            return
        overlay.set_status(status_msg, color_hex)

    def on_voice_translated(item_data):
        if not license_mgr.is_active():
            overlay.set_status("🔒 UNLICENSED (Enter Token in Settings)", "#EF4444")
            return
        overlay.add_chat_card(item_data)

    import time
    import keyboard
    from PyQt6.QtCore import QObject, pyqtSignal

    class HotkeyNotifier(QObject):
        toggle_signal = pyqtSignal()

        def __init__(self):
            super().__init__()
            self.last_toggle_time = 0
            self.key_is_down = False

        def on_key_press(self, e):
            now = time.time()
            if not self.key_is_down and (now - self.last_toggle_time >= 0.4):
                self.key_is_down = True
                self.last_toggle_time = now
                self.toggle_signal.emit()

        def on_key_release(self, e):
            self.key_is_down = False

    hotkey_notifier = HotkeyNotifier()
    hotkey_notifier.toggle_signal.connect(overlay.toggle_visibility)

    current_toggle_hooks = []
    current_toggle_hk = None

    def update_visibility_hotkey():
        nonlocal current_toggle_hooks, current_toggle_hk
        hk = config.get("toggle_visibility_hotkey", "f7").strip().lower()
        if current_toggle_hk == hk and current_toggle_hooks:
            return

        for h in current_toggle_hooks:
            try:
                keyboard.unhook(h)
            except Exception:
                pass
        current_toggle_hooks = []

        if hk:
            try:
                h_press = keyboard.on_press_key(hk, hotkey_notifier.on_key_press, suppress=False)
                h_release = keyboard.on_release_key(hk, hotkey_notifier.on_key_release, suppress=False)
                current_toggle_hooks = [h_press, h_release]
                current_toggle_hk = hk
                print(f"[SA-RP Linggo] Total Hide Toggle Hotkey bound to '{hk.upper()}'", flush=True)
            except Exception as e:
                print(f"[SA-RP Linggo] Failed to bind toggle hotkey '{hk}': {e}", flush=True)

    update_visibility_hotkey()

    def on_settings_updated():
        new_key = config.get("groq_api_key", "")
        new_model = config.get("groq_model", "openai/gpt-oss-20b")
        new_lang = config.get("target_language", "Indonesian")
        new_dev = config.get("developer_mode", False)
        
        translator.set_api_key(new_key)
        translator.set_model(new_model)
        translator.set_target_lang(new_lang)
        translator.set_developer_mode(new_dev)

        new_path = config.get("chatlog_path", "")
        chat_listener.set_path(new_path)
        chat_listener.set_use_codsmp(config.get("use_codsmp", True))
        clipboard_listener.set_enabled(config.get("enable_clipboard_outbound", True))
        # Reset clipboard listener state so next CTRL+C is processed fresh
        clipboard_listener.last_processed_text = ""
        clipboard_listener.last_translated_text = ""
        voice_listener.update_hotkey()
        update_visibility_hotkey()

    chat_listener.new_chat_item.connect(on_new_chat_line)
    chat_listener.status_changed.connect(on_listener_status)
    trans_worker.translation_complete.connect(on_translation_done)
    clipboard_listener.outbound_translated.connect(on_outbound_translated)
    voice_listener.status_changed.connect(on_voice_status)
    voice_listener.voice_translated.connect(on_voice_translated)
    overlay.settings_saved_signal.connect(on_settings_updated)

    def cleanup():
        print("[SA-RP Linggo] Shutting down application cleanly...", flush=True)
        try:
            if current_toggle_hook:
                keyboard.unhook(current_toggle_hook)
            chat_listener.stop()
            trans_worker.stop()
            voice_listener.stop()
        except Exception:
            pass
        os._exit(0)

    app.aboutToQuit.connect(cleanup)

    print("[SA-RP Linggo] Application started successfully! Overlay is active.", flush=True)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
