import os
import json
import glob

import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

DEFAULT_CONFIG = {
    "groq_api_key": "",
    "chatlog_path": "",
    "target_language": "Indonesian",
    "groq_model": "openai/gpt-oss-20b",
    "outbound_style": "Standard English",
    "use_codsmp": True,
    "enable_clipboard_outbound": True,
    "enable_voice_input": True,
    "voice_hotkey": "f4",
    "toggle_visibility_hotkey": "f7",
    "font_size": 11,
    "opacity": 0.90,
    "always_on_top": True,
    "click_through": False,
    "auto_translate_ic": True,
    "auto_translate_me_do": True,
    "developer_mode": False,
    "max_feed_items": 50,
    "overlay_x": 100,
    "overlay_y": 100,
    "overlay_width": 420,
    "overlay_height": 320
}

class ConfigManager:
    """Manages application configuration, persistence, and auto-detection."""

    def __init__(self, config_path=CONFIG_FILE):
        self.config_path = config_path
        self.data = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        """Loads configuration from JSON file if it exists."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    saved_data = json.load(f)
                    self.data.update(saved_data)
            except Exception as e:
                print(f"[Config] Error loading config file: {e}")

        # Auto-detect missing values
        if not self.data.get("chatlog_path") or not os.path.exists(self.data.get("chatlog_path", "")):
            detected_path = self.detect_chatlog_path()
            if detected_path:
                self.data["chatlog_path"] = detected_path

        if not self.data.get("groq_api_key"):
            detected_key = self.detect_groq_api_key()
            if detected_key:
                self.data["groq_api_key"] = detected_key

        self.save()

    def save(self):
        """Saves current configuration to JSON file."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"[Config] Error saving config file: {e}")

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()

    @staticmethod
    def detect_chatlog_path():
        """Attempts to auto-detect standard SAMP chatlog.txt locations."""
        user_profile = os.environ.get("USERPROFILE", "")
        possible_paths = [
            os.path.join(user_profile, "Documents", "GTA San Andreas User Files", "SAMP", "chatlog.txt"),
            os.path.join(user_profile, "OneDrive", "Documents", "GTA San Andreas User Files", "SAMP", "chatlog.txt"),
            r"C:\Users\Public\Documents\GTA San Andreas User Files\SAMP\chatlog.txt",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                print(f"[Config] Detected SAMP chatlog path: {path}")
                return path
        return possible_paths[0]  # Fallback to standard path even if file doesn't exist yet

    @staticmethod
    def detect_groq_api_key():
        """Detects Groq API key from environment variable or Downloads directory."""
        # 1. Environment variable
        env_key = os.environ.get("GROQ_API_KEY", "").strip()
        if env_key.startswith("gsk_"):
            return env_key

        # 2. Check Downloads folder for gsk_*.txt file
        user_profile = os.environ.get("USERPROFILE", "")
        downloads_dir = os.path.join(user_profile, "Downloads")
        if os.path.exists(downloads_dir):
            key_files = glob.glob(os.path.join(downloads_dir, "gsk_*.txt"))
            for key_file in key_files:
                try:
                    with open(key_file, "r", encoding="utf-8") as f:
                        key_content = f.read().strip()
                        if key_content.startswith("gsk_"):
                            print(f"[Config] Auto-detected Groq API Key from {key_file}")
                            return key_content
                except Exception:
                    pass
        return ""
