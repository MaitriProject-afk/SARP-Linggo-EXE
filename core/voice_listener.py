import io
import wave
import time
import threading
from collections import deque
import numpy as np
import sounddevice as sd
import keyboard
import pyperclip
from PyQt6.QtCore import QObject, pyqtSignal, QThread

class VoiceListener(QThread):
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    status_changed = pyqtSignal(str, str) # (message, color_hex)
    voice_translated = pyqtSignal(dict)   # (item_data)

    def __init__(self, translator=None, config_manager=None, license_manager=None):
        super().__init__()
        self.translator = translator
        self.config = config_manager
        self.license_mgr = license_manager
        
        self.sample_rate = 16000
        self.channels = 1
        self.is_recording = False
        self.audio_frames = []
        self.pre_buffer = deque(maxlen=15) # Holds ~450ms pre-recording audio
        self.stream = None
        self.running = True
        self.hotkey_hook_pressed = None
        self.hotkey_hook_released = None
        self.current_hotkey = None
        self.lock = threading.Lock()

    def update_hotkey(self):
        """Re-binds global hotkey listener based on current config."""
        if not self.config:
            return

        enabled = self.config.get("enable_voice_input", True)
        hotkey = self.config.get("voice_hotkey", "f4").strip().lower()

        if self.current_hotkey == hotkey and enabled:
            return

        self._unhook_hotkeys()

        if enabled and hotkey:
            try:
                self.hotkey_hook_pressed = keyboard.on_press_key(hotkey, self._on_key_press, suppress=False)
                self.hotkey_hook_released = keyboard.on_release_key(hotkey, self._on_key_release, suppress=False)
                self.current_hotkey = hotkey
                print(f"[VoiceListener] Hotkey bound to: '{hotkey.upper()}'", flush=True)
            except Exception as e:
                print(f"[VoiceListener] Failed to bind hotkey '{hotkey}': {e}", flush=True)

    def _unhook_hotkeys(self):
        if self.hotkey_hook_pressed:
            try:
                keyboard.unhook(self.hotkey_hook_pressed)
            except Exception:
                pass
            self.hotkey_hook_pressed = None

        if self.hotkey_hook_released:
            try:
                keyboard.unhook(self.hotkey_hook_released)
            except Exception:
                pass
            self.hotkey_hook_released = None
        self.current_hotkey = None

    def _on_key_press(self, e):
        if not self.config.get("enable_voice_input", True):
            return
        if self.license_mgr and not self.license_mgr.is_active():
            return
        
        with self.lock:
            if not self.is_recording:
                self.start_recording()

    def _on_key_release(self, e):
        if not self.config.get("enable_voice_input", True):
            return
        
        with self.lock:
            if self.is_recording:
                self.stop_and_process()

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            print(f"[VoiceListener Audio Warning] {status}", flush=True)
        chunk = indata.copy()
        self.pre_buffer.append(chunk)
        if self.is_recording:
            self.audio_frames.append(chunk)

    def ensure_stream_active(self):
        """Keeps InputStream open continuously so there is 0ms start latency on hotkey press."""
        if self.stream is None:
            try:
                self.stream = sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype='int16',
                    callback=self._audio_callback
                )
                self.stream.start()
                print("[VoiceListener] Continuous Audio InputStream active.", flush=True)
            except Exception as e:
                print(f"[VoiceListener Stream Start Error] {e}", flush=True)
                self.stream = None

    def start_recording(self):
        self.ensure_stream_active()
        self.is_recording = True
        # Pre-fill audio_frames with the pre-buffer (captures ~400ms before key press)
        self.audio_frames = list(self.pre_buffer)
        self.status_changed.emit("🎙️ Recording Voice... (Release Key to Send)", "#EF4444")
        self.recording_started.emit()

    def stop_and_process(self):
        self.is_recording = False
        self.recording_stopped.emit()

        frames_to_process = list(self.audio_frames)
        self.audio_frames = []

        if not frames_to_process:
            self.status_changed.emit("⚠️ Short Recording (No Audio)", "#F59E0B")
            return

        # Combine audio frames
        audio_data = np.concatenate(frames_to_process, axis=0)
        duration = len(audio_data) / self.sample_rate

        # Ignore accidental micro-taps under 0.35 seconds
        if duration < 0.35:
            self.status_changed.emit("⚠️ Hold hotkey longer to talk", "#F59E0B")
            return

        # Convert numpy frames to in-memory WAV byte buffer
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2) # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data.tobytes())

        wav_bytes = wav_buffer.getvalue()
        
        # Process transcription & translation in background thread
        threading.Thread(target=self._process_worker, args=(wav_bytes, duration), daemon=True).start()

    def _process_worker(self, wav_bytes, duration):
        try:
            self.status_changed.emit(f"⚡ Transcribing Voice ({duration:.1f}s)...", "#38BDF8")

            if not self.translator:
                self.status_changed.emit("⚠️ Translator Not Ready", "#EF4444")
                return

            # Step 1: Transcribe via Groq Whisper API
            indonesian_text, err = self.translator.transcribe_audio(wav_bytes)
            if err or not indonesian_text:
                self.status_changed.emit(f"⚠️ {err if err else 'Speech Not Recognized'}", "#F59E0B")
                return

            # Normalize all phonetic misinterpretations by Whisper (e.g. Persesmi, Selesmi, Slashmi, Slasmi, Selasmi, me, slash do, do, pasar -> dasar)
            import re
            def clean_rp_action(text):
                if not text:
                    return text
                # 1. Strip leading Whisper hallucinated prefix words (Pertama, Terima, Kamera, Satu, Tes, Test, etc.)
                text = re.sub(r'^(?:pertama(?:\s+pertama)?|terima|kamera|satu|tes|test|halo|hello)[,\.\s]+', '', text, flags=re.IGNORECASE)
                # 2. Strip leading whitespace and punctuation
                text = re.sub(r'^[,\.\-\?!\s]+', '', text)
                # 3. Fix common speech misheard words
                text = re.sub(r'^(?:pasar|sar)\s+(mahluk|manusia|anjing|bangsat|tolol|bego)', r'dasar \1', text, flags=re.IGNORECASE)
                text = re.sub(r'\bdiuntuk\b', 'diuntung', text, flags=re.IGNORECASE)

                if re.search(r'^(?:[a-z]*(?:sdo|shdo)|(?:slash|selas|seles|slas|sles|proses|perses|plas)\s*do|do)\b[,\.\s]*', text, re.IGNORECASE):
                    return "/do " + re.sub(r'^(?:[a-z]*(?:sdo|shdo)|(?:slash|selas|seles|slas|sles|proses|perses|plas)\s*do|do)\b[,\.\s]*', '', text, flags=re.IGNORECASE)
                if re.search(r'^(?:[a-z]*(?:smi|shmi|sme|shme)|(?:slash|selas|seles|slas|sles|proses|perses|plas)\s*(?:mi|me)?|me)\b[,\.\s]*', text, re.IGNORECASE):
                    return "/me " + re.sub(r'^(?:[a-z]*(?:smi|shmi|sme|shme)|(?:slash|selas|seles|slas|sles|proses|perses|plas)\s*(?:mi|me)?|me)\b[,\.\s]*', '', text, flags=re.IGNORECASE)
                return text

            indonesian_text = clean_rp_action(indonesian_text)

            # Step 2: Translate to selected Outbound Style
            style = self.config.get("outbound_style", "Standard English") if self.config else "Standard English"
            self.status_changed.emit(f"⚡ Translating to {style}...", "#38BDF8")

            translated_text = self.translator.translate_outbound(indonesian_text, style=style)
            if not translated_text:
                self.status_changed.emit("⚠️ Translation Failed", "#EF4444")
                return

            # Step 3: Copy to Windows Clipboard automatically
            try:
                pyperclip.copy(translated_text)
                if hasattr(self, "clipboard_listener") and self.clipboard_listener:
                    self.clipboard_listener.last_translated_text = translated_text
                    self.clipboard_listener.last_processed_text = translated_text
            except Exception as e:
                print(f"[VoiceListener Clipboard Error] {e}", flush=True)

            # Step 4: Emit completion event
            rpd_rem = self.translator.last_rpd_remaining
            rpd_lim = self.translator.last_rpd_limit

            item_data = {
                "type": "OUTBOUND_VOICE",
                "speaker": f"MIC ({style.upper()})",
                "original": f"🎙️ {indonesian_text}",
                "translated": translated_text,
                "style": style,
                "timestamp": time.strftime("%H:%M:%S"),
                "rpd_remaining": rpd_rem,
                "rpd_limit": rpd_lim
            }

            rpd_str = f" | RPD: {rpd_rem}/{rpd_lim if rpd_lim else 1000}" if rpd_rem is not None else ""
            self.status_changed.emit(f"● Voice Outbound Ready! (Press CTRL+V){rpd_str}", "#06B6D4")
            self.voice_translated.emit(item_data)
        except Exception as e:
            print(f"[VoiceListener Worker Unhandled Error] {e}", flush=True)
            self.status_changed.emit(f"⚠️ Error: {e}", "#EF4444")

    def run(self):
        self.update_hotkey()
        self.ensure_stream_active()
        while self.running:
            self.msleep(200)

    def stop(self):
        self.running = False
        self._unhook_hotkeys()
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
        self.quit()
        self.wait()
