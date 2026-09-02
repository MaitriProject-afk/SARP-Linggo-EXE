import os
import sys
import ctypes
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QTimer, QSize
from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QDialog, QLineEdit, QPlainTextEdit, QComboBox, QSpinBox, QFileDialog,
    QCheckBox, QSlider, QMessageBox, QSystemTrayIcon, QMenu, QSizeGrip
)
from PyQt6.QtGui import QIcon, QAction, QPixmap, QColor, QPainter, QFont
from ui.styles import MAIN_STYLE
from ui.icons import get_svg_icon

# Win32 API Constants
GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_LAYERED = 0x00080000

def create_app_icon():
    """Generates vector app icon for window taskbar and tray."""
    return get_svg_icon("app_logo", size=32)


class ChatItemCard(QFrame):
    """
    Compact SAMP Chatlog Style Card.
    Presents original chat line and translated text in clean, compact SAMP game-chat format.
    """
    def __init__(self, item_data, font_size=11):
        super().__init__()
        self.setObjectName("ChatItemCard")
        self.setProperty("class", "ChatItemCard")

        chat_type = item_data.get("type", "SAYS").upper()
        self.setProperty("chat_type", chat_type)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)

        timestamp = item_data.get("timestamp", "")
        ts_str = f"[{timestamp}] " if timestamp else ""
        speaker = item_data.get("speaker", "")
        orig_content = item_data.get("content", "")
        translated_content = item_data.get("translated", orig_content)

        rpd_rem = item_data.get("rpd_remaining")
        rpd_lim = item_data.get("rpd_limit")
        rpd_tag = f"  <span style='color: #64748B; font-size: 9px; font-weight: bold;'>[RPD: {rpd_rem}/{rpd_lim if rpd_lim else 1000}]</span>" if rpd_rem is not None else ""

        # Handle Error / Rate Limit Cards
        error_detail = item_data.get("error")
        if error_detail:
            self.setProperty("chat_type", "ERROR")
            orig_text = f"{ts_str}⚠️ TRANSLATION ERROR / RATE LIMIT ({item_data.get('style', 'Groq API')})"
            trans_text = f"❌ '{item_data.get('original', '')}' -> {error_detail}"

            orig_label = QLabel(orig_text)
            orig_label.setWordWrap(True)
            orig_label.setStyleSheet("color: #F87171; font-weight: bold; font-size: 10px;")

            trans_label = QLabel(trans_text)
            trans_label.setWordWrap(True)
            trans_label.setStyleSheet("color: #EF4444; font-weight: bold; font-size: 11px; background-color: rgba(239, 68, 68, 0.15); padding: 4px; border-radius: 4px;")

            layout.addWidget(orig_label)
            layout.addWidget(trans_label)
            return

        # Line 1: Original SAMP Line / Voice Transcript
        if chat_type == "OUTBOUND":
            style_name = item_data.get("style", "Standard English")
            orig_text = f"{ts_str}[OUTBOUND ({style_name.upper()})] {item_data.get('original', '')}"
            trans_text = f"➔ {item_data.get('translated', '')}  📌 [COPIED! PRESS CTRL+V]{rpd_tag}"
        elif chat_type == "OUTBOUND_VOICE":
            style_name = item_data.get("style", "Standard English")
            orig_val = item_data.get("original", "").replace("🎙️ ", "").strip()
            orig_text = f"{ts_str}🎙️ Transkrip Suara (ID): \"{orig_val}\""
            trans_text = f"➔ {speaker} says: {translated_content}  📌 [COPIED! PRESS CTRL+V]{rpd_tag}"
        elif chat_type == "ME":
            orig_text = f"{ts_str}* {speaker} {orig_content}"
            trans_text = f"➔ * {speaker} {translated_content}{rpd_tag}"
        elif chat_type == "DO":
            orig_text = f"{ts_str}* {orig_content} (( {speaker} ))"
            trans_text = f"➔ * {translated_content} (( {speaker} )){rpd_tag}"
        else:
            orig_text = f"{ts_str}{speaker} says: {orig_content}"
            trans_text = f"➔ {speaker} says: {translated_content}{rpd_tag}"

        orig_label = QLabel(orig_text)
        orig_label.setProperty("class", "OrigLine")
        orig_label.setWordWrap(True)
        orig_label.setStyleSheet(f"font-size: {max(9, font_size - 1)}px;")

        trans_box = QHBoxLayout()
        trans_box.setContentsMargins(0, 0, 0, 0)
        trans_box.setSpacing(6)

        trans_label = QLabel(trans_text)
        trans_label.setProperty("class", "TransLine")
        trans_label.setProperty("chat_type", chat_type)
        trans_label.setWordWrap(True)
        trans_label.setStyleSheet(f"font-size: {font_size}px;")

        copy_btn = QPushButton("📋 Salin")
        copy_btn.setToolTip("Salin teks terjemahan ini ke Clipboard (CTRL+V)")
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284C7;
                color: #FFFFFF;
                font-size: 10px;
                font-weight: bold;
                padding: 2px 8px;
                border-radius: 3px;
                border: none;
            }
            QPushButton:hover {
                background-color: #38BDF8;
            }
            QPushButton:pressed {
                background-color: #0369A1;
            }
        """)

        clean_text_to_copy = item_data.get("translated", "")
        def do_copy():
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtGui import QClipboard
            cb = QApplication.clipboard()
            cb.setText(clean_text_to_copy, QClipboard.Mode.Clipboard)
            copy_btn.setText("✓ Tersalin!")
            copy_btn.setStyleSheet("""
                QPushButton {
                    background-color: #10B981;
                    color: #FFFFFF;
                    font-size: 10px;
                    font-weight: bold;
                    padding: 2px 8px;
                    border-radius: 3px;
                    border: none;
                }
            """)
            QTimer.singleShot(1500, lambda: (
                copy_btn.setText("📋 Salin"),
                copy_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #0284C7;
                        color: #FFFFFF;
                        font-size: 10px;
                        font-weight: bold;
                        padding: 2px 8px;
                        border-radius: 3px;
                        border: none;
                    }
                    QPushButton:hover {
                        background-color: #38BDF8;
                    }
                """)
            ))

        copy_btn.clicked.connect(do_copy)

        trans_box.addWidget(trans_label, 1)
        trans_box.addWidget(copy_btn, 0, Qt.AlignmentFlag.AlignTop)

        layout.addWidget(orig_label)
        layout.addLayout(trans_box)


def show_noactivate_msgbox(parent, title, text, icon=QMessageBox.Icon.Information):
    msg = QMessageBox(parent)
    msg.setIcon(icon)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
    try:
        import ctypes
        from ctypes import wintypes
        hwnd = wintypes.HWND(int(msg.winId()))
        user32 = ctypes.windll.user32
        GWL_EXSTYLE = -20
        WS_EX_TOPMOST = 0x00000008
        WS_EX_NOACTIVATE = 0x08000000
        user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
        user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
        user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t

        curr = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, curr | WS_EX_TOPMOST | WS_EX_NOACTIVATE)
        
        user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
        user32.SetWindowPos.restype = wintypes.BOOL
        user32.SetWindowPos(hwnd, wintypes.HWND(-1), 0, 0, 0, 0, 0x0002 | 0x0001 | 0x0010 | 0x0040)
    except Exception:
        pass
    msg.exec()


class SettingsDialog(QDialog):
    """Dialog to configure API Key, Chatlog Path, and UI preferences."""
    def __init__(self, config_manager, translator=None, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.translator = translator
        self.setWindowTitle("SA-RP Linggo Settings")
        self.setWindowIcon(get_svg_icon("settings", size=24))
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.resize(480, 460)
        self.init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        try:
            import ctypes
            from ctypes import wintypes
            hwnd = wintypes.HWND(int(self.winId()))
            user32 = ctypes.windll.user32
            GWL_EXSTYLE = -20
            WS_EX_TOPMOST = 0x00000008
            user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
            user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
            user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
            user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t

            curr = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
            user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, curr | WS_EX_TOPMOST)
            
            user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
            user32.SetWindowPos.restype = wintypes.BOOL
            # SWP_NOMOVE (0x0002) | SWP_NOSIZE (0x0001) | SWP_SHOWWINDOW (0x0040)
            user32.SetWindowPos(hwnd, wintypes.HWND(-1), 0, 0, 0, 0, 0x0002 | 0x0001 | 0x0040)
        except Exception as e:
            print(f"[SettingsDialog] showEvent exstyle error: {e}", flush=True)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # 1. Groq AI API Key Pool (Rolling Token Dynamic)
        layout.addWidget(QLabel("<b>Groq AI API Key Pool:</b> <span style='color: #A855F7; font-size: 11px;'>(Rolling Token - Pisahkan koma atau baris baru)</span>"))

        self.key_input = QPlainTextEdit()
        self.key_input.setPlainText(self.config.get("groq_api_key", ""))
        self.key_input.setPlaceholderText("Masukkan 1 atau banyak Groq API Key (gsk_...)\nPisahkan dengan koma atau baris baru untuk mendaftarkan banyak token (Dynamic Rolling)")
        self.key_input.setFixedHeight(65)
        self.key_input.setStyleSheet("background-color: #1E222D; color: #FFFFFF; border: 1px solid #373C47; border-radius: 4px; padding: 4px;")
        self.key_input.textChanged.connect(self.update_key_pool_badge)

        self.key_pool_badge = QLabel()
        self.key_pool_badge.setStyleSheet("color: #38BDF8; font-size: 11px; font-weight: bold;")

        detect_key_btn = QPushButton("Auto-Detect Key")
        detect_key_btn.setIcon(get_svg_icon("settings", size=16))
        detect_key_btn.setStyleSheet("background-color: #2D313B; color: #38BDF8; font-weight: 600; padding: 5px 10px; border: 1px solid #373C47; border-radius: 4px;")
        detect_key_btn.clicked.connect(self.auto_detect_key)

        key_top_row = QHBoxLayout()
        key_top_row.addWidget(self.key_pool_badge)
        key_top_row.addStretch()
        key_top_row.addWidget(detect_key_btn)

        layout.addWidget(self.key_input)
        layout.addLayout(key_top_row)
        self.update_key_pool_badge()

        # 2. SAMP Chatlog Path
        layout.addWidget(QLabel("<b>SAMP Chatlog File Path:</b>"))
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit(self.config.get("chatlog_path", ""))
        self.path_input.setPlaceholderText("Path to chatlog.txt")

        browse_btn = QPushButton("Browse...")
        browse_btn.setStyleSheet("background-color: #2D313B; color: #F1F5F9; padding: 5px 10px; border: 1px solid #373C47; border-radius: 4px;")
        browse_btn.clicked.connect(self.browse_chatlog)

        detect_path_btn = QPushButton("Auto-Detect Path")
        detect_path_btn.setStyleSheet("background-color: #2D313B; color: #38BDF8; font-weight: 600; padding: 5px 10px; border: 1px solid #373C47; border-radius: 4px;")
        detect_path_btn.clicked.connect(self.auto_detect_path)
        
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_btn)
        path_layout.addWidget(detect_path_btn)
        layout.addLayout(path_layout)

        # 2b. CodSMP Option Checkbox
        self.codsmp_check = QCheckBox("⚡ Saya Pengguna CodSMP (Otomatis Baca Log Terbaru di Folder /logs/)")
        self.codsmp_check.setChecked(self.config.get("use_codsmp", True))
        self.codsmp_check.setStyleSheet("font-weight: bold; color: #38BDF8;")
        layout.addWidget(self.codsmp_check)

        # 2c. Voice Input Checkbox & Hotkey Selector
        voice_layout = QHBoxLayout()
        self.voice_check = QCheckBox("🎙️ Aktifkan Voice-to-Text Mic (Push-To-Talk)")
        self.voice_check.setChecked(self.config.get("enable_voice_input", True))
        self.voice_check.setStyleSheet("font-weight: bold; color: #A855F7;")

        self.voice_hotkey_combo = QComboBox()
        self.voice_hotkey_combo.addItems(["F4", "F8", "F9", "F10", "F11", "Numpad *", "Numpad +", "Scroll Lock", "Caps Lock"])
        current_hk = self.config.get("voice_hotkey", "f4").strip().upper()
        if current_hk == "NUMPAD_*": current_hk = "Numpad *"
        elif current_hk == "NUMPAD_+": current_hk = "Numpad +"
        elif current_hk == "SCROLL LOCK": current_hk = "Scroll Lock"
        elif current_hk == "CAPS LOCK": current_hk = "Caps Lock"
        self.voice_hotkey_combo.setCurrentText(current_hk if current_hk in ["F4", "F8", "F9", "F10", "F11", "Numpad *", "Numpad +", "Scroll Lock", "Caps Lock"] else "F4")
        
        voice_layout.addWidget(self.voice_check)
        voice_layout.addStretch()
        voice_layout.addWidget(QLabel("<b>Hotkey:</b>"))
        voice_layout.addWidget(self.voice_hotkey_combo)
        layout.addLayout(voice_layout)

        # 2d. Toggle Visibility (Total Hide / Show) Hotkey Selector
        hide_layout = QHBoxLayout()
        hide_label = QLabel("🙈 <b>Hotkey Total Hide / Show Overlay:</b>")
        hide_label.setStyleSheet("color: #10B981; font-weight: bold;")
        
        self.hide_hotkey_combo = QComboBox()
        self.hide_hotkey_combo.addItems(["F7", "F6", "F8", "F9", "F10", "F11", "F12", "Numpad -", "Numpad /"])
        current_hide_hk = self.config.get("toggle_visibility_hotkey", "f7").strip().upper()
        if current_hide_hk == "NUMPAD_-": current_hide_hk = "Numpad -"
        elif current_hide_hk == "NUMPAD_/": current_hide_hk = "Numpad /"
        self.hide_hotkey_combo.setCurrentText(current_hide_hk if current_hide_hk in ["F7", "F6", "F8", "F9", "F10", "F11", "F12", "Numpad -", "Numpad /"] else "F7")

        hide_layout.addWidget(hide_label)
        hide_layout.addStretch()
        hide_layout.addWidget(self.hide_hotkey_combo)
        layout.addLayout(hide_layout)

        # 3. Target Language Selector
        row_layout = QHBoxLayout()
        lang_vbox = QVBoxLayout()
        lang_vbox.addWidget(QLabel("<b>Target Language:</b>"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["Indonesian", "English", "Javanese", "Sundanese"])
        self.lang_combo.setCurrentText(self.config.get("target_language", "Indonesian"))
        lang_vbox.addWidget(self.lang_combo)
        row_layout.addLayout(lang_vbox)
        layout.addLayout(row_layout)

        # 3b. Live RPD Checker Section
        rpd_vbox = QVBoxLayout()
        rpd_hbox = QHBoxLayout()
        self.rpd_status_label = QLabel("Sisa RPD: <b>[Klik tombol Cek Sisa RPD]</b>")
        self.rpd_status_label.setStyleSheet("color: #38BDF8; font-size: 11px;")
        
        check_rpd_btn = QPushButton("Cek Sisa RPD 🔄")
        check_rpd_btn.setStyleSheet("background-color: #0284C7; color: #FFFFFF; font-weight: bold; padding: 5px 12px; border-radius: 4px; border: none;")
        check_rpd_btn.clicked.connect(self.check_live_rpd)
        
        rpd_hbox.addWidget(self.rpd_status_label)
        rpd_hbox.addStretch()
        rpd_hbox.addWidget(check_rpd_btn)
        rpd_vbox.addLayout(rpd_hbox)
        layout.addLayout(rpd_vbox)

        # 4. Font Size & Opacity
        row2_layout = QHBoxLayout()
        
        font_vbox = QVBoxLayout()
        font_vbox.addWidget(QLabel("<b>Font Size:</b>"))
        self.font_spin = QSpinBox()
        self.font_spin.setRange(8, 20)
        self.font_spin.setValue(self.config.get("font_size", 11))
        font_vbox.addWidget(self.font_spin)

        opac_vbox = QVBoxLayout()
        opac_vbox.addWidget(QLabel("<b>Overlay Opacity:</b>"))
        self.opac_slider = QSlider(Qt.Orientation.Horizontal)
        self.opac_slider.setRange(20, 100)
        self.opac_slider.setValue(int(self.config.get("opacity", 0.90) * 100))
        opac_vbox.addWidget(self.opac_slider)

        row2_layout.addLayout(font_vbox)
        row2_layout.addLayout(opac_vbox)
        layout.addLayout(row2_layout)

        # 5. Translation Automation Toggles
        trans_toggle_vbox = QVBoxLayout()
        
        self.chatlog_check = QCheckBox("Enable Inbound Chatlog Auto-Translation (Chatlog ➔ Overlay)")
        chatlog_active = self.config.get("auto_translate_ic", True) or self.config.get("auto_translate_me_do", True)
        self.chatlog_check.setChecked(chatlog_active)
        self.chatlog_check.setStyleSheet("font-weight: bold; color: #10B981;")

        self.outbound_check = QCheckBox("Enable Outbound Clipboard Auto-Translation (ID ➔ EN)")
        self.outbound_check.setChecked(self.config.get("enable_clipboard_outbound", True))
        self.outbound_check.setStyleSheet("font-weight: bold; color: #38BDF8;")
        
        outbound_row = QHBoxLayout()
        outbound_row.addWidget(QLabel("<b>Outbound English Style:</b>"))
        self.outbound_combo = QComboBox()
        self.outbound_combo.addItems([
            "Standard English",
            "American Hood"
        ])
        self.outbound_combo.setCurrentText(self.config.get("outbound_style", "Standard English"))
        outbound_row.addWidget(self.outbound_combo)
        
        trans_toggle_vbox.addWidget(self.chatlog_check)
        trans_toggle_vbox.addWidget(self.outbound_check)
        trans_toggle_vbox.addLayout(outbound_row)
        layout.addLayout(trans_toggle_vbox)

        # 6. Open Source Build Info Section
        lic_vbox = QVBoxLayout()
        lic_vbox.setSpacing(6)
        
        lic_title_row = QHBoxLayout()
        lic_title = QLabel("🔓 <b>Status Aplikasi:</b> <span style='color: #22C55E; font-weight: bold;'>100% FREE & OPEN-SOURCE BUILD</span>")
        lic_title_row.addWidget(lic_title)
        lic_title_row.addStretch()
        
        from core.licensing import LicenseManager
        self.license_manager = LicenseManager()
        self.current_hwid = self.license_manager.get_local_hwid()
        
        lic_vbox.addLayout(lic_title_row)

        self.license_status_label = QLabel("Mod ini <b>100% Gratis dan Bebas Digunakan</b> tanpa perlu aktivasi lisensi. Masukkan Groq API Key milik Anda sendiri untuk langsung menggunakannya.")
        self.license_status_label.setStyleSheet("color: #94A3B8; font-size: 11px;")
        self.license_status_label.setWordWrap(True)
        lic_vbox.addWidget(self.license_status_label)

        layout.addLayout(lic_vbox)

        # 7. Developer Mode & Debug Log Settings
        dev_row = QHBoxLayout()
        self.dev_mode_check = QCheckBox("🔧 Enable Developer Debug Mode (Log Raw Error & Headers)")
        self.dev_mode_check.setChecked(self.config.get("developer_mode", False))
        self.dev_mode_check.setStyleSheet("font-weight: bold; color: #EC4899;")
        
        open_debug_btn = QPushButton("📂 Open debug.log")
        open_debug_btn.setStyleSheet("background-color: #334155; color: #F8FAFC; font-size: 11px; padding: 3px 8px; border-radius: 4px;")
        open_debug_btn.clicked.connect(self.open_debug_log)

        dev_row.addWidget(self.dev_mode_check)
        dev_row.addStretch()
        dev_row.addWidget(open_debug_btn)
        layout.addLayout(dev_row)

        # Buttons Save / Cancel
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        save_btn = QPushButton("Save & Apply")
        save_btn.setStyleSheet("background-color: #38BDF8; color: #0F172A; font-weight: bold; padding: 6px 16px; border-radius: 4px;")
        save_btn.clicked.connect(self.save_settings)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #2D313B; color: #94A3B8; padding: 6px 16px; border-radius: 4px; border: 1px solid #373C47;")
        cancel_btn.clicked.connect(self.reject)

        # Copyright & Credit label
        credit_label = QLabel("SA-RP Linggo v1.3.0 • Developed by MaitriProject • Open Source (MIT)")
        credit_label.setStyleSheet("color: #64748B; font-size: 10px; margin-top: 6px;")
        credit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(credit_label)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def open_debug_log(self):
        from core.config import BASE_DIR
        log_file = os.path.join(BASE_DIR, "debug_log.txt")
        if not os.path.exists(log_file):
            try:
                with open(log_file, "w", encoding="utf-8") as f:
                    f.write("=== SA-RP Linggo Debug Log Initialized ===\n")
            except Exception:
                pass
        try:
            os.startfile(log_file)
        except Exception as e:
            show_noactivate_msgbox(self, "Debug Log", f"Tidak dapat membuka file debug_log.txt: {e}", QMessageBox.Icon.Warning)


    def copy_hwid_to_clipboard(self):
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.current_hwid)
        show_noactivate_msgbox(self, "Copied", f"HWID '{self.current_hwid}' has been copied to clipboard!")

    def activate_license_token(self):
        token_str = self.token_input.text().strip()
        if not token_str:
            show_noactivate_msgbox(self, "Empty Token", "Please paste your license token before clicking Activate!", QMessageBox.Icon.Warning)
            return
        
        success, message = self.license_manager.activate_token(token_str)
        if success:
            show_noactivate_msgbox(self, "Activation Success", message, QMessageBox.Icon.Information)
            info = self.license_manager.get_license_info()
            status_text = f"<b style='color: #22C55E;'>ACTIVE</b> ({info.get('remaining_days', 0)} Days Remaining)"
            self.license_status_label.setText(f"Status: {status_text}")
            self.token_input.clear()
        else:
            show_noactivate_msgbox(self, "Activation Failed", message, QMessageBox.Icon.Critical)

    def update_key_pool_badge(self):
        raw_text = self.key_input.toPlainText().strip()
        if self.translator:
            self.translator.set_api_key(raw_text)
            summary = self.translator.key_pool.get_pool_summary()
            self.key_pool_badge.setText(summary)
        else:
            import re
            keys = [k for k in re.split(r'[\s,\n;]+', raw_text) if k]
            self.key_pool_badge.setText(f"🔑 {len(keys)} Token Terdaftar (Rolling Dynamic)")

    def check_live_rpd(self):
        if not self.translator:
            self.rpd_status_label.setText("Sisa RPD: <b style='color: #EF4444;'>Engine Belum Siap</b>")
            return

        api_key_str = self.key_input.toPlainText().strip()
        if not api_key_str:
            self.rpd_status_label.setText("Sisa RPD: <b style='color: #EF4444;'>API Key Belum Diisi</b>")
            return

        self.translator.set_api_key(api_key_str)
        self.rpd_status_label.setText("<i>Memeriksa status semua token di Groq...</i>")
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        success, summary_text, rem, lim, rst = self.translator.check_rpd_quota()
        if success or summary_text:
            formatted_summary = summary_text.replace('\n', '<br>')
            self.rpd_status_label.setText(f"<b>Status Pool Token Groq:</b><br>{formatted_summary}")
        else:
            self.rpd_status_label.setText(f"Status Token: <b style='color: #EF4444;'>Gagal Cek RPD</b>")

    def auto_detect_key(self):
        detected = self.config.detect_groq_api_key()
        if detected:
            curr = self.key_input.toPlainText().strip()
            if curr and detected not in curr:
                self.key_input.setPlainText(f"{curr}\n{detected}")
            else:
                self.key_input.setPlainText(detected)
            show_noactivate_msgbox(self, "Success", "Found Groq API Key!", QMessageBox.Icon.Information)
        else:
            show_noactivate_msgbox(self, "Not Found", "Could not automatically find Groq API key file in Downloads.", QMessageBox.Icon.Warning)

    def auto_detect_path(self):
        detected = self.config.detect_chatlog_path()
        if detected:
            self.path_input.setText(detected)

    def browse_chatlog(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select SAMP chatlog.txt", "", "Text Files (*.txt);;All Files (*)")
        if filename:
            self.path_input.setText(filename)

    def save_settings(self):
        self.config.set("groq_api_key", self.key_input.toPlainText().strip())
        self.config.set("translation_engine", "groq")
        self.config.set("groq_model", "openai/gpt-oss-20b")
        self.config.set("chatlog_path", self.path_input.text().strip())
        self.config.set("use_codsmp", self.codsmp_check.isChecked())
        self.config.set("target_language", self.lang_combo.currentText())
        self.config.set("auto_translate_ic", self.chatlog_check.isChecked())
        self.config.set("auto_translate_me_do", self.chatlog_check.isChecked())
        self.config.set("outbound_style", self.outbound_combo.currentText())
        self.config.set("enable_clipboard_outbound", self.outbound_check.isChecked())
        self.config.set("enable_voice_input", self.voice_check.isChecked())
        self.config.set("developer_mode", self.dev_mode_check.isChecked())
        hk_map = {
            "F4": "f4", "F8": "f8", "F9": "f9", "F10": "f10", "F11": "f11",
            "Numpad *": "numpad_*", "Numpad +": "numpad_+",
            "Scroll Lock": "scroll lock", "Caps Lock": "caps lock"
        }
        selected_hk = hk_map.get(self.voice_hotkey_combo.currentText(), "f4")
        self.config.set("voice_hotkey", selected_hk)
        
        hide_hk_map = {
            "F7": "f7", "F6": "f6", "F8": "f8", "F9": "f9", "F10": "f10", "F11": "f11", "F12": "f12",
            "Numpad -": "numpad_-", "Numpad /": "numpad_/"
        }
        selected_hide_hk = hide_hk_map.get(self.hide_hotkey_combo.currentText(), "f7")
        self.config.set("toggle_visibility_hotkey", selected_hide_hk)

        self.config.set("font_size", self.font_spin.value())
        self.config.set("opacity", self.opac_slider.value() / 100.0)
        self.accept()


class OverlayWindow(QWidget):
    """
    Main Frameless Modern Glassmorphism Overlay Widget for SA-RP Linggo.
    Supports edge window resizing, auto-scrolling, and SAMP chatlog styling.
    """
    settings_saved_signal = pyqtSignal()
    RESIZE_MARGIN = 8

    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.is_dragging = False
        self.resizing = False
        self.resize_edges = (False, False, False, False)
        self.drag_position = QPoint()
        self.is_locked = False
        self.is_collapsed = False
        self.auto_scroll_enabled = True
        self.translator = None
        self.is_settings_open = False

        self.setMouseTracking(True)
        self.init_window_flags()
        self.init_ui()
        self.init_system_tray()
        self.apply_config_settings()

    def init_window_flags(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setObjectName("OverlayWindow")
        self.setWindowIcon(create_app_icon())

        self.topmost_timer = QTimer(self)
        self.topmost_timer.setInterval(1000)
        self.topmost_timer.timeout.connect(self.force_topmost)
        self.topmost_timer.start()
        QTimer.singleShot(100, self.force_topmost)

    def force_topmost(self):
        """Enforces Win32 TopMost and NOACTIVATE window flags for Exclusive Fullscreen Game Overlays."""
        if not self.isVisible() or getattr(self, 'is_settings_open', False):
            return
        try:
            import ctypes
            from ctypes import wintypes
            hwnd = wintypes.HWND(int(self.winId()))
            user32 = ctypes.windll.user32
            user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
            user32.SetWindowPos.restype = wintypes.BOOL
            
            user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
            user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
            user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
            user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t

            GWL_EXSTYLE = -20
            WS_EX_TOPMOST = 0x00000008
            WS_EX_NOACTIVATE = 0x08000000

            curr = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
            if not (curr & WS_EX_NOACTIVATE) or not (curr & WS_EX_TOPMOST):
                user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, curr | WS_EX_TOPMOST | WS_EX_NOACTIVATE)

            # SWP_NOMOVE (0x0002) | SWP_NOSIZE (0x0001) | SWP_NOACTIVATE (0x0010) | SWP_SHOWWINDOW (0x0040)
            user32.SetWindowPos(hwnd, wintypes.HWND(-1), 0, 0, 0, 0, 0x0002 | 0x0001 | 0x0010 | 0x0040)
        except Exception as e:
            print(f"[Overlay Topmost Error] {e}", flush=True)

    def showEvent(self, event):
        super().showEvent(event)
        self.force_topmost()

    def init_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # Central Glass Widget
        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidget")
        self.central_widget.setStyleSheet(MAIN_STYLE)
        self.central_widget.setMouseTracking(True)

        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header Bar
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(8, 4, 8, 4)
        header_layout.setSpacing(6)

        # Title with Vector SVG Logo
        logo_label = QLabel()
        logo_label.setPixmap(get_svg_icon("app_logo", size=18).pixmap(18, 18))
        
        title_label = QLabel("SA-RP LINGGO")
        title_label.setObjectName("AppTitle")

        self.status_label = QLabel("Active")
        self.status_label.setObjectName("StatusLabel")

        # Vector Icon Control Buttons
        self.chat_toggle_btn = QPushButton("Chat: ON")
        self.chat_toggle_btn.setToolTip("Click to toggle Inbound Chatlog Auto-Translation (ON/OFF)")
        self.chat_toggle_btn.setProperty("class", "HeaderIconBtn")
        self.chat_toggle_btn.setObjectName("ChatToggleBtn")
        self.chat_toggle_btn.setStyleSheet("padding: 2px 6px; font-size: 10px; font-weight: 600; min-width: 65px;")
        self.chat_toggle_btn.clicked.connect(self.toggle_chatlog_inbound)

        self.clip_toggle_btn = QPushButton("Clip: ON")
        self.clip_toggle_btn.setToolTip("Click to toggle Outbound Clipboard Auto-Translation (ON/OFF)")
        self.clip_toggle_btn.setProperty("class", "HeaderIconBtn")
        self.clip_toggle_btn.setObjectName("ClipToggleBtn")
        self.clip_toggle_btn.setStyleSheet("padding: 2px 6px; font-size: 10px; font-weight: 600; min-width: 65px;")
        self.clip_toggle_btn.clicked.connect(self.toggle_clipboard_outbound)

        self.lock_btn = QPushButton("Move Mode")
        self.lock_btn.setIcon(get_svg_icon("move", size=16))
        self.lock_btn.setIconSize(QSize(14, 14))
        self.lock_btn.setToolTip("Click to toggle Lock / Click-Through mode")
        self.lock_btn.setProperty("class", "HeaderIconBtn")
        self.lock_btn.setObjectName("LockBtn")
        self.lock_btn.setStyleSheet("padding: 2px 8px; font-size: 10px; font-weight: 600; min-width: 80px;")
        self.lock_btn.clicked.connect(self.toggle_lock)

        clear_btn = QPushButton()
        clear_btn.setIcon(get_svg_icon("clear", size=16))
        clear_btn.setIconSize(QSize(14, 14))
        clear_btn.setToolTip("Clear Feed")
        clear_btn.setProperty("class", "HeaderIconBtn")
        clear_btn.clicked.connect(self.clear_feed)

        settings_btn = QPushButton()
        settings_btn.setIcon(get_svg_icon("settings", size=16))
        settings_btn.setIconSize(QSize(14, 14))
        settings_btn.setToolTip("Open Settings")
        settings_btn.setProperty("class", "HeaderIconBtn")
        settings_btn.clicked.connect(self.open_settings)

        collapse_btn = QPushButton()
        collapse_btn.setIcon(get_svg_icon("minimize", size=16))
        collapse_btn.setIconSize(QSize(14, 14))
        collapse_btn.setToolTip("Minimize/Expand Feed")
        collapse_btn.setProperty("class", "HeaderIconBtn")
        collapse_btn.clicked.connect(self.toggle_collapse)

        close_btn = QPushButton()
        close_btn.setIcon(get_svg_icon("close", size=16))
        close_btn.setIconSize(QSize(14, 14))
        close_btn.setToolTip("Exit Application")
        close_btn.setProperty("class", "HeaderIconBtn")
        close_btn.setObjectName("CloseBtn")
        close_btn.clicked.connect(self.close_app)

        header_layout.addWidget(logo_label)
        header_layout.addWidget(title_label)
        header_layout.addWidget(self.status_label)
        header_layout.addStretch()
        header_layout.addWidget(self.chat_toggle_btn)
        header_layout.addWidget(self.clip_toggle_btn)
        header_layout.addWidget(self.lock_btn)
        header_layout.addWidget(clear_btn)
        header_layout.addWidget(settings_btn)
        header_layout.addWidget(collapse_btn)
        header_layout.addWidget(close_btn)

        main_layout.addWidget(header_frame)

        # Chat Feed Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.feed_layout = QVBoxLayout(self.scroll_content)
        self.feed_layout.setContentsMargins(6, 6, 6, 6)
        self.feed_layout.setSpacing(2)
        self.feed_layout.addStretch()

        self.scroll_area.setWidget(self.scroll_content)
        
        # Connect vertical scrollbar rangeChanged for 100% reliable auto-scroll
        vbar = self.scroll_area.verticalScrollBar()
        vbar.rangeChanged.connect(self.on_scroll_range_changed)

        main_layout.addWidget(self.scroll_area)

        # Footer Row with QSizeGrip for smooth corner resizing
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 0, 2, 2)
        footer_layout.addStretch()

        self.size_grip = QSizeGrip(self.central_widget)
        footer_layout.addWidget(self.size_grip)

        main_layout.addLayout(footer_layout)

        outer_layout.addWidget(self.central_widget)

        # Set saved geometry or defaults
        w = self.config.get("overlay_width", 440)
        h = self.config.get("overlay_height", 300)
        x = self.config.get("overlay_x", 100)
        y = self.config.get("overlay_y", 100)
        self.setGeometry(x, y, w, h)

    def on_scroll_range_changed(self, min_val, max_val):
        """Auto scroll to bottom whenever new content expands the scrollable range."""
        if self.auto_scroll_enabled:
            self.scroll_area.verticalScrollBar().setValue(max_val)

    def init_system_tray(self):
        """Creates a system tray icon in Windows notification area."""
        try:
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(create_app_icon())
            self.tray_icon.setToolTip("SA-RP Linggo Overlay")
            
            tray_menu = QMenu()
            
            toggle_action = QAction("👁️ Show / Hide Overlay", self)
            toggle_action.triggered.connect(self.toggle_visibility)

            lock_action = QAction(get_svg_icon("lock", size=16), "Toggle Lock Mode", self)
            lock_action.triggered.connect(self.toggle_lock)
            
            clear_action = QAction(get_svg_icon("clear", size=16), "Clear Feed", self)
            clear_action.triggered.connect(self.clear_feed)

            settings_action = QAction(get_svg_icon("settings", size=16), "Settings", self)
            settings_action.triggered.connect(self.open_settings)
            
            exit_action = QAction(get_svg_icon("close", size=16), "Exit Application", self)
            exit_action.triggered.connect(self.close_app)

            tray_menu.addAction(toggle_action)
            tray_menu.addAction(lock_action)
            tray_menu.addAction(clear_action)
            tray_menu.addAction(settings_action)
            tray_menu.addSeparator()
            tray_menu.addAction(exit_action)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self.on_tray_icon_activated)
            self.tray_icon.show()
        except Exception as e:
            print(f"[Overlay] init_system_tray error: {e}", flush=True)

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_visibility()

    def toggle_visibility(self):
        """Toggles complete visibility (Total Hide / Show) of the Overlay Window."""
        try:
            if self.isVisible():
                self.hide()
                if hasattr(self, 'tray_icon'):
                    self.tray_icon.showMessage(
                        "SA-RP Linggo",
                        "Overlay tersembunyi (Total Hide).\nTekan hotkey atau klik tray icon untuk memunculkan kembali.",
                        QSystemTrayIcon.MessageIcon.Information,
                        2000
                    )
            else:
                self.show()
                self.raise_()
                self.activateWindow()
                self.force_topmost()
                if hasattr(self, 'tray_icon'):
                    self.tray_icon.show()
        except Exception as e:
            print(f"[Overlay] toggle_visibility error: {e}", flush=True)

    def toggle_chatlog_inbound(self):
        current = self.config.get("auto_translate_ic", True) or self.config.get("auto_translate_me_do", True)
        new_state = not current
        self.config.set("auto_translate_ic", new_state)
        self.config.set("auto_translate_me_do", new_state)
        self.apply_config_settings()
        self.settings_saved_signal.emit()

    def toggle_clipboard_outbound(self):
        current = self.config.get("enable_clipboard_outbound", True)
        new_state = not current
        self.config.set("enable_clipboard_outbound", new_state)
        self.apply_config_settings()
        self.settings_saved_signal.emit()

    def apply_config_settings(self):
        opacity = self.config.get("opacity", 0.90)
        self.setWindowOpacity(opacity)

        chat_enabled = self.config.get("auto_translate_ic", True) or self.config.get("auto_translate_me_do", True)
        if chat_enabled:
            self.chat_toggle_btn.setText("💬 Chat: ON")
            self.chat_toggle_btn.setStyleSheet("padding: 2px 6px; font-size: 10px; font-weight: bold; background-color: #10B981; color: #FFFFFF; border-radius: 3px;")
            self.chat_toggle_btn.setToolTip("Inbound Chatlog Translation: ENABLED (Click to turn OFF)")
        else:
            self.chat_toggle_btn.setText("🚫 Chat: OFF")
            self.chat_toggle_btn.setStyleSheet("padding: 2px 6px; font-size: 10px; font-weight: bold; background-color: #334155; color: #94A3B8; border-radius: 3px;")
            self.chat_toggle_btn.setToolTip("Inbound Chatlog Translation: DISABLED (Click to turn ON)")

        clip_enabled = self.config.get("enable_clipboard_outbound", True)
        if clip_enabled:
            self.clip_toggle_btn.setText("📋 Clip: ON")
            self.clip_toggle_btn.setStyleSheet("padding: 2px 6px; font-size: 10px; font-weight: bold; background-color: #0284C7; color: #FFFFFF; border-radius: 3px;")
            self.clip_toggle_btn.setToolTip("Clipboard Translation: ENABLED (Click to turn OFF)")
        else:
            self.clip_toggle_btn.setText("🚫 Clip: OFF")
            self.clip_toggle_btn.setStyleSheet("padding: 2px 6px; font-size: 10px; font-weight: bold; background-color: #334155; color: #94A3B8; border-radius: 3px;")
            self.clip_toggle_btn.setToolTip("Clipboard Translation: DISABLED (Click to turn ON)")

        api_key = self.config.get("groq_api_key", "")
        if not api_key:
            self.set_status("● No API Key", "#F59E0B")
        else:
            self.set_status("● Active", "#10B981")

    def set_status(self, message, color_hex="#94A3B8"):
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color_hex}; font-size: 10px; font-weight: bold;")

    def add_chat_card(self, item_data):
        font_size = self.config.get("font_size", 11)
        card = ChatItemCard(item_data, font_size=font_size)

        count = self.feed_layout.count()
        self.feed_layout.insertWidget(count - 1, card)

        # Force scroll to bottom immediately and after layout updates
        vbar = self.scroll_area.verticalScrollBar()
        vbar.setValue(vbar.maximum())
        QTimer.singleShot(30, lambda: vbar.setValue(vbar.maximum()))

        max_items = self.config.get("max_feed_items", 50)
        while self.feed_layout.count() > max_items + 1:
            item = self.feed_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def clear_feed(self):
        while self.feed_layout.count() > 1:
            item = self.feed_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        if self.is_locked:
            self.lock_btn.setText("Locked")
            self.lock_btn.setIcon(get_svg_icon("lock", color="#EF4444", size=14))
            self.lock_btn.setProperty("locked", "true")
            self.set_click_through(True)
            self.set_status("● Locked", "#EF4444")
            self.size_grip.hide()
        else:
            self.set_click_through(False)
            self.lock_btn.setText("Move Mode")
            self.lock_btn.setIcon(get_svg_icon("move", color="#10B981", size=14))
            self.lock_btn.setProperty("locked", "false")
            self.set_status("● Active", "#10B981")
            self.size_grip.show()

        self.lock_btn.style().unpolish(self.lock_btn)
        self.lock_btn.style().polish(self.lock_btn)

    def set_click_through(self, enable):
        """Sets Windows OS click-through transparent mode using Win32 API."""
        if sys.platform == "win32":
            try:
                hwnd = int(self.winId())
                style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                if enable:
                    style |= WS_EX_TRANSPARENT | WS_EX_LAYERED
                else:
                    style &= ~WS_EX_TRANSPARENT
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
            except Exception as e:
                print(f"[Overlay] set_click_through error: {e}", flush=True)

    def toggle_collapse(self):
        self.is_collapsed = not self.is_collapsed
        if self.is_collapsed:
            self.scroll_area.hide()
            self.size_grip.hide()
            self.resize(self.width(), 36)
        else:
            self.scroll_area.show()
            if not self.is_locked:
                self.size_grip.show()
            self.resize(self.width(), self.config.get("overlay_height", 300))

    def set_translator(self, translator):
        self.translator = translator

    def open_settings(self):
        self.is_settings_open = True
        was_locked = self.is_locked
        if was_locked:
            self.set_click_through(False)

        dialog = SettingsDialog(self.config, translator=self.translator, parent=self)
        if dialog.exec():
            self.apply_config_settings()
            self.settings_saved_signal.emit()

        self.is_settings_open = False
        if was_locked:
            self.set_click_through(True)
        self.force_topmost()

    def close_app(self):
        self.config.set("overlay_x", self.x())
        self.config.set("overlay_y", self.y())
        self.config.set("overlay_width", self.width())
        self.config.set("overlay_height", self.height())

        if hasattr(self, "tray_icon"):
            self.tray_icon.hide()

        from PyQt6.QtWidgets import QApplication
        QApplication.quit()

    def closeEvent(self, event):
        self.close_app()
        event.accept()

    # Native Window Dragging & Edge Resizing Logic
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.is_locked:
            if self.is_on_resize_area(event.position()):
                self.resizing = True
            else:
                self.is_dragging = True
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if not self.is_locked:
            if self.resizing:
                self.perform_window_resize(event.globalPosition().toPoint())
                event.accept()
            elif self.is_dragging:
                self.move(event.globalPosition().toPoint() - self.drag_position)
                event.accept()
            else:
                self.update_cursor_shape(event.position())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.resizing = False
            self.unsetCursor()

    def is_on_resize_area(self, pos):
        w, h = self.width(), self.height()
        x, y = pos.x(), pos.y()
        m = self.RESIZE_MARGIN
        top = y <= m
        bottom = y >= (h - m)
        left = x <= m
        right = x >= (w - m)
        self.resize_edges = (top, bottom, left, right)
        return top or bottom or left or right

    def update_cursor_shape(self, pos):
        top, bottom, left, right = self.resize_edges
        if (top and left) or (bottom and right):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif (top and right) or (bottom and left):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif top or bottom:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        elif left or right:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        else:
            self.unsetCursor()

    def perform_window_resize(self, global_pos):
        top, bottom, left, right = self.resize_edges
        geo = self.geometry()
        min_w, min_h = 320, 160

        if right:
            geo.setRight(max(global_pos.x(), geo.left() + min_w))
        if bottom:
            geo.setBottom(max(global_pos.y(), geo.top() + min_h))
        if left:
            geo.setLeft(min(global_pos.x(), geo.right() - min_w))
        if top:
            geo.setTop(min(global_pos.y(), geo.bottom() - min_h))

        self.setGeometry(geo)
