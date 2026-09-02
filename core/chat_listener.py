import os
import re
import time
from PyQt6.QtCore import QThread, pyqtSignal

class ChatlogListener(QThread):
    """
    Background worker thread that monitors SAMP's chatlog.txt file.
    Streams newly added lines and filters strictly for IC speech, /me, and /do actions.
    Supports names with spaces (e.g. JGRP / Jogjagamers format: 'Ashford Moonveil' or 'Mask 182700').
    """

    new_chat_item = pyqtSignal(dict)
    status_changed = pyqtSignal(str)

    TIMESTAMP_REGEX = re.compile(r"^\[(\d{2}:\d{2}:\d{2})\]\s*")

    # IC Spoken Chat: e.g. "Ashford Moonveil says: Hello!" or "Mask 182700 shouts (cellphone): Stop!"
    SAYS_REGEX = re.compile(
        r"^(.+?)\s+(says|shouts|whispers)(?:\s+\([^\)]+\))?:\s*(.+)$",
        re.IGNORECASE
    )

    # /do Action: e.g. "* Is the car door locked? (( Ashford Moonveil ))"
    DO_REGEX = re.compile(
        r"^\*\s+(.+?)\s*\(\(\s*(.+?)\s*\)\)$"
    )

    # Prefixes that must be ignored
    IGNORE_PREFIXES = [
        "PAYCHECK:", "SERVER:", "MOTD:", "MASK:", "Ad:", "Contact Info:",
        "[ADMIN]", "[NEWS]", "[AD]", "[RADIO]", "[R]", "Screenshot",
        "Connecting to", "Connected.", "MOTD:"
    ]

    def __init__(self, chatlog_path="", poll_interval=0.25, use_codsmp=True):
        super().__init__()
        self.chatlog_path = chatlog_path
        self.poll_interval = poll_interval
        self.use_codsmp = use_codsmp
        self.running = True

    def set_path(self, new_path):
        self.chatlog_path = new_path

    def set_use_codsmp(self, use_codsmp):
        self.use_codsmp = use_codsmp

    def stop(self):
        self.running = False
        self.wait()

    def get_active_chatlog_path(self):
        """
        Resolves the active chatlog file.
        If use_codsmp is True:
            1. Checks chatlog.txt for explicit 'Your chatlog has been saved to: <path>' redirect line.
            2. Scans SAMP/logs/ directory and picks the latest timestamped .txt file.
        If use_codsmp is False:
            Directly reads standard SAMP chatlog.txt.
        """
        if not self.chatlog_path:
            return ""

        path = os.path.abspath(self.chatlog_path)
        if os.path.isdir(path):
            samp_dir = path
        else:
            parent = os.path.dirname(path)
            if os.path.basename(parent).lower() == "logs":
                samp_dir = os.path.dirname(parent)
            else:
                samp_dir = parent

        chatlog_txt = os.path.join(samp_dir, "chatlog.txt")

        if self.use_codsmp:
            # 1. Check if chatlog.txt explicitly specifies a CodSMP redirected log file
            if os.path.exists(chatlog_txt):
                try:
                    with open(chatlog_txt, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        m = re.search(r"Your chatlog has been saved to:\s*(.+?\.txt)", content, re.IGNORECASE)
                        if m:
                            target_codsmp = m.group(1).strip()
                            if os.path.exists(target_codsmp):
                                return target_codsmp
                except Exception:
                    pass

            # 2. Find absolute most recently modified file in logs/
            logs_dir = os.path.join(samp_dir, "logs")
            if os.path.exists(logs_dir) and os.path.isdir(logs_dir):
                import glob
                log_files = glob.glob(os.path.join(logs_dir, "*.txt"))
                if log_files:
                    log_files.sort(key=lambda x: os.path.getmtime(x))
                    return log_files[-1]

        return chatlog_txt if os.path.exists(chatlog_txt) else path

    def run(self):
        self.status_changed.emit("Waiting for chatlog file...")

        while self.running:
            active_path = self.get_active_chatlog_path()
            if not active_path or not os.path.exists(active_path):
                self.status_changed.emit(f"File not found: {self.chatlog_path or 'Not configured'}")
                time.sleep(1.0)
                continue

            is_codsmp = "logs" in active_path.lower()
            file_label = os.path.basename(active_path)
            self.status_changed.emit(f"Monitoring {file_label} ({'CodSMP' if is_codsmp else 'SAMP'})")

            try:
                with open(active_path, "r", encoding="utf-8", errors="ignore") as f:
                    # Seek straight to EOF on startup so old logs from past sessions are ignored
                    f.seek(0, os.SEEK_END)
                    last_pos = f.tell()

                    # Continuous polling for NEW incoming lines only
                    while self.running:
                        # Check periodically if a new CodSMP file or updated target path exists
                        new_target = self.get_active_chatlog_path()
                        if new_target != active_path:
                            # Hot switch to new active log file (e.g. CodSMP generated a new file upon relog)
                            break

                        if not os.path.exists(active_path):
                            break

                        current_size = os.path.getsize(active_path)
                        
                        # Handle log file truncation/reset
                        if current_size < last_pos:
                            f.seek(0, os.SEEK_SET)
                            last_pos = 0

                        # Re-seek to last_pos to reset EOF status on Windows
                        if current_size > last_pos:
                            f.seek(last_pos)
                            while self.running:
                                line = f.readline()
                                if not line:
                                    break
                                last_pos = f.tell()
                                parsed = self.parse_line(line.strip())
                                if parsed:
                                    self.new_chat_item.emit(parsed)
                        else:
                            time.sleep(self.poll_interval)

            except Exception as e:
                self.status_changed.emit(f"Error reading log: {e}")
                time.sleep(1.0)

    def parse_line(self, line):
        """
        Parses a single chatlog line and returns a structured dict if it passes strict filters.
        """
        if not line:
            return None

        # Extract timestamp
        timestamp = ""
        match_ts = self.TIMESTAMP_REGEX.match(line)
        clean_line = line
        if match_ts:
            timestamp = match_ts.group(1)
            clean_line = line[match_ts.end():].strip()

        # Ignore obvious system messages & OOC lines
        if clean_line.startswith("((") and not "))" in clean_line:
            return None
        if any(clean_line.startswith(prefix) for prefix in self.IGNORE_PREFIXES):
            return None

        # 1. Check for /do action
        if clean_line.startswith("* "):
            match_do = self.DO_REGEX.match(clean_line)
            if match_do:
                content = match_do.group(1).strip()
                speaker = match_do.group(2).strip()
                return {
                    "timestamp": timestamp,
                    "type": "DO",
                    "speaker": speaker,
                    "content": content,
                    "raw": line
                }

            # 2. Check for /me action
            line_body = clean_line[2:].strip()
            # Separate speaker and action text
            parts = line_body.split(maxsplit=2)
            if len(parts) >= 2:
                if parts[0].lower() == "mask" and len(parts) >= 3:
                    speaker = f"{parts[0]} {parts[1]}"
                    content = parts[2]
                elif "_" in parts[0]:
                    speaker = parts[0]
                    content = line_body[len(speaker):].strip()
                elif len(parts) >= 3 and parts[0][0].isupper() and parts[1][0].isupper():
                    speaker = f"{parts[0]} {parts[1]}"
                    content = parts[2]
                else:
                    speaker = parts[0]
                    content = line_body[len(speaker):].strip()
            else:
                speaker = "Unknown"
                content = line_body

            return {
                "timestamp": timestamp,
                "type": "ME",
                "speaker": speaker,
                "content": content,
                "raw": line
            }

        # 3. Check for IC Spoken Chat (says, shouts, whispers)
        match_says = self.SAYS_REGEX.match(clean_line)
        if match_says:
            speaker = match_says.group(1).strip()
            verb = match_says.group(2).strip().lower()
            content = match_says.group(3).strip()

            # Ignore system lines that happen to contain 'says'
            if any(speaker.startswith(p) for p in self.IGNORE_PREFIXES):
                return None

            if len(content) < 2:
                return None

            return {
                "timestamp": timestamp,
                "type": "SAYS",
                "verb": verb,
                "speaker": speaker,
                "content": content,
                "raw": line
            }

        return None
