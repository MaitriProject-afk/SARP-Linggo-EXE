import os
import time
import requests
import json
import re
from PyQt6.QtCore import QThread, pyqtSignal, QObject

INDONESIAN_MARKERS = {
    "apa", "apakah", "siapa", "dimana", "kapan", "mengapa", "kenapa", "bagaimana",
    "gimana", "kamu", "saya", "aku", "dia", "mereka", "kita", "kami", "anda", "ini",
    "itu", "yang", "dan", "atau", "tidak", "gak", "nggak", "ngga", "ga", "tak", "bukan",
    "ada", "bisa", "bila", "jika", "kalau", "sudah", "udah", "belum", "akan", "mau",
    "ingin", "harus", "adalah", "lagi", "sedang", "dapat", "sama", "dengan", "ke",
    "di", "dari", "untuk", "pada", "kabar", "baik", "tolong", "makasih", "terima",
    "kasih", "mas", "mbak", "gan", "min", "halo", "selamat", "pagi", "siang", "malam",
    "sore", "iya", "ya", "enggak", "gua", "gue", "lu", "sampe", "sampai", "bener",
    "benar", "sih", "dong", "kan", "lah", "deh", "kok", "noh", "tuh", "nih", "nanti",
    "kemarin", "besok", "mana", "sini", "situ", "sana", "brapa", "berapa", "bang",
    "orang", "kerja", "jalan", "makan", "minum", "beli", "jual", "rumah", "mobil", "motor",
    "sepertinya", "kehabisan", "bensin", "kayaknya", "rasanya", "pasti", "bikin", "buat",
    "lihat", "pergi", "datang", "naik", "turun", "bawa", "polisi", "senjata", "peluru",
    "buka", "tutup", "mati", "hidup", "rusak", "bakar", "hilang", "cari", "temu", "tarik",
    "dorong", "pukul", "tendang", "lari", "duduk", "tidur", "bangun", "serang", "kabur",
    "kelakuan", "mu", "sungguh", "memalukan", "parah", "banget", "parahbanget", "anjir",
    "anjg", "jir", "jirrr", "panteq", "pantek", "goblok", "tolol", "bego", "kontol",
    "memek", "peler", "bgst", "asli", "wkwk", "wkwkwk", "woi", "woii", "bro", "bray",
    "jangan", "berbuat", "sial", "keterlaluan", "bahaya", "diri", "aduh", "kasihan", "kasian",
    "artinya", "penggunaan", "melarang", "modifikasi", "berbasis", "aplikasi", "sistem",
    "fitur", "tombol", "halaman", "pesan", "folder", "file", "baca", "tulis", "simpan",
    "hapus", "kirim", "terima", "pilihan", "pilih", "tambah", "ubah", "ganti", "bantu",
    "tentang", "cara", "main", "mainkan", "pakai", "pake", "server", "bebas", "luas",
    "banyak", "sedikit", "semua", "setiap", "beberapa", "apapun", "siapapun", "manapun",
    "tetap", "selalu", "sering", "kadang", "jarang", "pernah", "dulu", "sekarang", "nantinya",
    "tinggal", "tekan", "kolom", "chat", "menempelkan", "hasil", "terjemahannya", "mirip",
    "kode", "struktur", "membaca", "tanpa"
}

ENGLISH_MARKERS = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it", "for", "not",
    "on", "with", "he", "as", "you", "do", "at", "this", "but", "his", "by", "from",
    "they", "we", "say", "her", "she", "or", "an", "will", "my", "one", "all", "would",
    "there", "their", "what", "so", "up", "out", "if", "about", "who", "get", "which",
    "go", "me", "when", "make", "can", "like", "time", "no", "just", "him", "know",
    "take", "people", "into", "year", "your", "good", "some", "could", "them", "see",
    "other", "than", "then", "now", "look", "only", "come", "its", "over", "think",
    "also", "back", "after", "use", "two", "how", "our", "work", "first", "well",
    "way", "even", "new", "want", "because", "any", "these", "give", "day", "most",
    "us", "gonna", "wanna", "gotta", "tryna", "finna", "bruh", "homie", "fool", "fuck",
    "fucking", "shit", "bitch", "ass", "asshole", "damn", "motherfucker", "nigga",
    "cops", "police", "car", "gun", "drop", "hands", "freeze", "stop", "move", "deadass",
    "straight", "useless", "damn", "meet", "met", "cellphone", "says", "shouts", "whispers"
}

def is_indonesian_text(text):
    """
    Checks if a given string is natively written in Indonesian or contains Indonesian words.
    """
    if not text:
        return False

    clean_text = text.lower().strip()
    words = re.findall(r'\b[a-z]{2,}\b', clean_text)
    if not words:
        return False

    match_count = sum(1 for w in words if w in INDONESIAN_MARKERS)
    return match_count >= 1

def should_translate_inbound(text):
    """
    Determines if an inbound chatlog line should be translated to Indonesian.
    Returns True if the line contains English words or is not purely Indonesian.
    """
    if not text:
        return False
    clean_text = text.lower().strip()
    words = re.findall(r'\b[a-z]{2,}\b', clean_text)
    if not words:
        return False

    english_matches = sum(1 for w in words if w in ENGLISH_MARKERS)
    indonesian_matches = sum(1 for w in words if w in INDONESIAN_MARKERS)

    # 1. If it contains clear English words or slang markers, translate it!
    if english_matches >= 1:
        return True

    # 2. If it contains Indonesian markers and no English markers, it's native Indonesian (skip)
    if indonesian_matches >= 1:
        return False

    # 3. Foreign text or unknown words (e.g. Spanish, French, etc.) -> translate
    return True


class KeyPoolManager:
    """
    Dynamic Rolling API Token Pool Manager with automatic rate-limit cooldown tracking.
    Prioritizes per-minute limits (RPM/TPM 429) over daily limits (RPD 429) and handles round-robin key rotation.
    """
    def __init__(self, raw_keys_str=""):
        self.keys = []
        self.key_states = {}
        self.current_index = 0
        self.update_keys(raw_keys_str)

    def update_keys(self, raw_keys_str):
        if not raw_keys_str:
            self.keys = []
            return

        parsed = [k.strip() for k in re.split(r'[\s,\n;]+', raw_keys_str.strip()) if k.strip()]
        new_keys = []
        for k in parsed:
            if not k.startswith("gsk_") and len(k) > 20:
                k = "gsk_" + k
            if k and k not in new_keys:
                new_keys.append(k)

        self.keys = new_keys
        now = time.time()
        for k in self.keys:
            if k not in self.key_states:
                self.key_states[k] = {
                    "cooldown_until": 0,
                    "rpd_remaining": None,
                    "rpd_limit": None,
                    "rpd_reset": None,
                    "status": "ACTIVE",
                    "failure_count": 0
                }

        if self.keys:
            self.current_index = self.current_index % len(self.keys)
        else:
            self.current_index = 0

    def get_next_working_key(self):
        """
        Returns (key_string, key_index, masked_key) for the next active/ready key.
        If all keys are on cooldown, picks the key with the shortest cooldown remaining.
        """
        if not self.keys:
            return None, -1, None

        now = time.time()
        n = len(self.keys)

        # 1. Round-robin scan starting from current_index
        for offset in range(n):
            idx = (self.current_index + offset) % n
            k = self.keys[idx]
            st = self.key_states.get(k, {})
            if now >= st.get("cooldown_until", 0) and st.get("status") != "INVALID":
                self.current_index = idx
                masked = k[:6] + "..." + k[-4:] if len(k) > 10 else "***"
                return k, idx, masked

        # 2. All keys on cooldown/invalid -> pick valid key with shortest cooldown
        valid_keys = [k for k in self.keys if self.key_states.get(k, {}).get("status") != "INVALID"]
        candidate_pool = valid_keys if valid_keys else self.keys

        best_key = min(candidate_pool, key=lambda k: self.key_states.get(k, {}).get("cooldown_until", 0))
        idx = self.keys.index(best_key)
        self.current_index = idx
        masked = best_key[:6] + "..." + best_key[-4:] if len(best_key) > 10 else "***"
        return best_key, idx, masked

    def mark_rate_limited(self, key, response_status, response_headers=None, response_text=""):
        """
        Marks a key as rate-limited (HTTP 429) or invalid (HTTP 401) and rotates pointer.
        Per-Minute limit: 60s cooldown.
        Daily RPD limit: 1h cooldown.
        Invalid key: 24h cooldown.
        """
        st = self.key_states.get(key)
        if not st:
            return f"⚠️ Key status missing"

        now = time.time()
        idx = self.keys.index(key) if key in self.keys else 0
        masked = key[:6] + "..." + key[-4:] if len(key) > 10 else "***"

        if response_status == 401:
            st["status"] = "INVALID"
            st["cooldown_until"] = now + 86400
            if self.keys:
                self.current_index = (self.current_index + 1) % len(self.keys)
            return f"❌ Key #{idx+1} ({masked}) Invalid API Key (HTTP 401). Rolling to next key."

        if response_status == 429:
            retry_after = 60
            if response_headers:
                ra_header = response_headers.get("retry-after") or response_headers.get("Retry-After")
                if ra_header:
                    try:
                        retry_after = int(ra_header)
                    except ValueError:
                        pass

            rpd_rem = response_headers.get("x-ratelimit-remaining-requests") if response_headers else None
            if rpd_rem == "0" or "daily" in response_text.lower():
                st["status"] = "EXHAUSTED_DAILY"
                st["cooldown_until"] = now + 3600
                limit_type = "Daily RPD Limit"
            else:
                st["status"] = "COOLDOWN_MINUTE"
                st["cooldown_until"] = now + max(retry_after, 60)
                limit_type = "Per-Minute Limit (60s)"

            st["failure_count"] += 1
            if self.keys:
                next_idx = (self.current_index + 1) % len(self.keys)
                self.current_index = next_idx
                next_masked = self.keys[next_idx][:6] + "..." + self.keys[next_idx][-4:] if len(self.keys[next_idx]) > 10 else "***"
                return f"⚠️ Key #{idx+1} ({masked}) hit {limit_type} (429)! Cooldown {int(st['cooldown_until'] - now)}s. Rolling to Key #{next_idx+1} ({next_masked})"

        if self.keys:
            self.current_index = (self.current_index + 1) % len(self.keys)
        return f"⚠️ Key #{idx+1} ({masked}) Error HTTP {response_status}"

    def update_key_metrics(self, key, rpd_rem, rpd_lim, rpd_rst):
        st = self.key_states.get(key)
        if st:
            st["status"] = "ACTIVE"
            st["rpd_remaining"] = rpd_rem
            st["rpd_limit"] = rpd_lim
            st["rpd_reset"] = rpd_rst
            st["failure_count"] = 0
            st["cooldown_until"] = 0

    def get_pool_summary(self):
        total = len(self.keys)
        if total == 0:
            return "Tidak ada API key terdaftar"

        now = time.time()
        ready_count = sum(1 for k in self.keys if now >= self.key_states.get(k, {}).get("cooldown_until", 0) and self.key_states.get(k, {}).get("status") != "INVALID")
        curr_idx = self.current_index + 1 if total > 0 else 0
        return f"🔑 {total} Token Terdaftar | Rolling Pointer: Key #{curr_idx} ({ready_count}/{total} Siap)"


class GroqTranslator(QObject):
    """
    Master Contextual Reasoning Translation Engine powered by openai/gpt-oss-20b.
    Supports Dynamic Rolling Token Pool (Multi-Key Rotation).
    NO CACHE - every translation is always fresh from the AI.
    """
    ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key="", model="openai/gpt-oss-20b", target_lang="Indonesian", developer_mode=False):
        super().__init__()
        self.api_key = api_key
        self.model = "openai/gpt-oss-20b"
        self.target_lang = target_lang
        self.developer_mode = developer_mode
        self.key_pool = KeyPoolManager(api_key)
        self.last_rpd_remaining = None
        self.last_rpd_limit = None
        self.last_rpd_reset = None
        self.last_error_detail = "[Translation Error]"

    def set_api_key(self, api_key):
        self.api_key = api_key
        self.key_pool.update_keys(api_key)

    def set_model(self, model):
        self.model = "openai/gpt-oss-20b"

    def set_target_lang(self, target_lang):
        self.target_lang = target_lang

    def set_developer_mode(self, enabled):
        self.developer_mode = enabled

    def log_debug(self, message):
        """Appends timestamped debug log messages to debug_log.txt in the application directory."""
        try:
            from core.config import BASE_DIR
            log_file = os.path.join(BASE_DIR, "debug_log.txt")
            t_stamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{t_stamp} {message}\n")
        except Exception as e:
            print(f"[DebugLog Error] {e}", flush=True)

    def _get_api_keys(self):
        """Parses comma, space, or newline separated Groq API keys."""
        return self.key_pool.keys

    def _clean_translation_output(self, out_text):
        if not out_text:
            return ""
        out_text = out_text.strip()
        out_text = re.sub(r'<think>.*?(?:</think>|$)', '', out_text, flags=re.DOTALL).strip()
        out_text = re.sub(r"^Here's a thinking process:.*$", "", out_text, flags=re.MULTILINE | re.IGNORECASE).strip()

        # If output contains multiple lines, grab the final valid translated line
        if "\n" in out_text:
            lines = [l.strip('"`* ') for l in out_text.split("\n") if l.strip()]
            valid_lines = [l for l in lines if not any(l.lower().startswith(p) for p in ["we need", "translate", "the sentence", "here is", "is not indonesian", "note:", "actually"])]
            if valid_lines:
                out_text = valid_lines[-1]
            elif lines:
                out_text = lines[-1]

        out_text = out_text.strip('"`* ')

        out_text = re.sub(r'\bmotherf[*#@%]+er\b', 'motherfucker', out_text, flags=re.IGNORECASE)
        out_text = re.sub(r'\bmotherf[*#@%]+ers\b', 'motherfuckers', out_text, flags=re.IGNORECASE)
        out_text = re.sub(r'\bf[*#@%]+k\b', 'fuck', out_text, flags=re.IGNORECASE)
        out_text = re.sub(r'\bf[*#@%]+king\b', 'fucking', out_text, flags=re.IGNORECASE)
        out_text = re.sub(r'\bf[*#@%]+ker\b', 'fucker', out_text, flags=re.IGNORECASE)
        out_text = re.sub(r'\bb[*#@%]+ch\b', 'bitch', out_text, flags=re.IGNORECASE)
        out_text = re.sub(r'\bb[*#@%]+ches\b', 'bitches', out_text, flags=re.IGNORECASE)
        out_text = re.sub(r'\ba[*#@%]+s\b', 'ass', out_text, flags=re.IGNORECASE)
        out_text = re.sub(r'\ba[*#@%]+shole\b', 'asshole', out_text, flags=re.IGNORECASE)
        out_text = re.sub(r'\bn[*#@%]+ga\b', 'nigga', out_text, flags=re.IGNORECASE)
        out_text = re.sub(r'\bn[*#@%]+gas\b', 'niggas', out_text, flags=re.IGNORECASE)

        # Clean AI meta refusal / thinking lead-ins if present
        refusal_patterns = [
            r"^.*is not indonesian.*$",
            r"^is a profanity.*$",
            r"^contains profanity.*$",
            r"^I cannot translate.*$",
            r"^As an AI language model.*$"
        ]
        for pat in refusal_patterns:
            out_text = re.sub(pat, '', out_text, flags=re.IGNORECASE | re.MULTILINE).strip()

        out_text = out_text.replace("—", ", ").replace("–", ", ").replace(" -- ", ", ").replace("--", ", ")
        out_text = re.sub(r',\s*,', ',', out_text)
        out_text = re.sub(r'\s+', ' ', out_text).strip()
        return out_text

    def _send_api_request(self, payload_messages, temperature=0.1):
        return self._send_groq_api_request(payload_messages, temperature)

    def _send_groq_api_request(self, payload_messages, temperature=0.1):
        if not self.key_pool.keys:
            self.last_error_detail = "[Groq API Key Belum Diisi]"
            return None, self.last_error_detail

        active_model = self.model if self.model else "openai/gpt-oss-20b"
        total_attempts = len(self.key_pool.keys)

        for attempt in range(total_attempts):
            key, key_idx, masked_key = self.key_pool.get_next_working_key()
            if not key:
                break

            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "User-Agent": "SA-RP-Linggo/1.3"
            }
            max_toks = 1200 if any(rm in active_model.lower() for rm in ["gpt-oss", "qwen", "deepseek"]) else 300
            payload = {
                "model": active_model,
                "messages": payload_messages,
                "temperature": temperature,
                "max_tokens": max_toks
            }

            try:
                response = requests.post(self.ENDPOINT, headers=headers, json=payload, timeout=12.0)

                rem = response.headers.get("x-ratelimit-remaining-requests")
                lim = response.headers.get("x-ratelimit-limit-requests")
                rst = response.headers.get("x-ratelimit-reset-requests")
                if rem is not None:
                    try: self.last_rpd_remaining = int(rem)
                    except ValueError: self.last_rpd_remaining = rem
                if lim is not None:
                    try: self.last_rpd_limit = int(lim)
                    except ValueError: self.last_rpd_limit = lim
                if rst is not None:
                    self.last_rpd_reset = str(rst)

                if response.status_code == 200:
                    self.key_pool.update_key_metrics(key, self.last_rpd_remaining, self.last_rpd_limit, self.last_rpd_reset)

                    result_json = response.json()
                    msg_obj = result_json["choices"][0]["message"]
                    raw_content = msg_obj.get("content", "") or ""

                    usage_info = result_json.get("usage", {})
                    p_toks = usage_info.get("prompt_tokens", 0)
                    c_toks = usage_info.get("completion_tokens", 0)
                    t_toks = usage_info.get("total_tokens", 0)
                    c_details = usage_info.get("completion_tokens_details", {}) or {}
                    r_toks = c_details.get("reasoning_tokens", 0) if isinstance(c_details, dict) else 0

                    self.last_token_usage = {
                        "prompt_tokens": p_toks,
                        "completion_tokens": c_toks,
                        "reasoning_tokens": r_toks,
                        "total_tokens": t_toks
                    }

                    # Fallback if reasoning model has text in reasoning instead of content
                    if not raw_content.strip() and "reasoning" in msg_obj:
                        raw_reasoning = msg_obj.get("reasoning", "")
                        quoted_strings = re.findall(r'"([^"\n]{6,})"', raw_reasoning)
                        if quoted_strings:
                            valid_quotes = [q for q in quoted_strings if not q.startswith("We need") and not q.startswith("Translate") and not q.startswith("Actually")]
                            if valid_quotes:
                                raw_content = valid_quotes[-1]
                            else:
                                raw_content = quoted_strings[-1]

                    out_text = self._clean_translation_output(raw_content)

                    if out_text:
                        rpd_str = f"RPD: {self.last_rpd_remaining}/{self.last_rpd_limit}" if self.last_rpd_remaining is not None else "RPD: N/A"
                        tok_str = f"Tokens: [Prompt={p_toks}, Output={c_toks} (Reasoning={r_toks}), Total={t_toks}]"
                        self.log_debug(f"Groq API Success | Key #{key_idx+1} ({masked_key}) | Model: {active_model} | {tok_str} | {rpd_str} | Output: {out_text}")
                        self.last_error_detail = None
                        return out_text, None
                    else:
                        err_msg = "[Groq Empty Response]"
                        self.last_error_detail = err_msg
                        self.log_debug(f"Groq API Empty Response | Key #{key_idx+1} ({masked_key})")
                else:
                    log_msg = self.key_pool.mark_rate_limited(key, response.status_code, response.headers, response.text)
                    self.last_error_detail = f"Key #{key_idx+1} ({masked_key}) HTTP {response.status_code}"
                    self.log_debug(f"[Rolling Key Rotation] {log_msg}")

            except Exception as e:
                log_msg = self.key_pool.mark_rate_limited(key, 500)
                self.last_error_detail = f"Groq Exception: {e}"
                self.log_debug(f"[Rolling Key Exception] Key #{key_idx+1} ({masked_key}): {e}")

        fallback = self.last_error_detail if self.developer_mode else "Semua API key sedang rate-limited / error"
        return None, fallback

    def transcribe_audio(self, audio_bytes):
        """Transcribes recorded speech audio using Groq Whisper model with Key Rotation."""
        if not self.key_pool.keys:
            return None, "[Groq API Key Belum Diisi]"

        stt_endpoint = "https://api.groq.com/openai/v1/audio/transcriptions"
        total_attempts = len(self.key_pool.keys)

        for attempt in range(total_attempts):
            key, key_idx, masked_key = self.key_pool.get_next_working_key()
            if not key:
                break
            headers = {
                "Authorization": f"Bearer {key}",
                "User-Agent": "SA-RP-Linggo/1.3"
            }
            files = {
                'file': ('speech.wav', audio_bytes, 'audio/wav'),
                'model': (None, 'whisper-large-v3-turbo'),
                'language': (None, 'id'),
                'prompt': (None, 'Percakapan Bahasa Indonesia SAMP Roleplay: /me, /do, slash me, slash do, dasar, mahluk, manusia, kamu, lu, gue, bangsat, anjing, kontol, bajingan, tidak tahu diri, tidak tahu diuntung.'),
                'response_format': (None, 'json')
            }
            try:
                response = requests.post(stt_endpoint, headers=headers, files=files, timeout=10.0)
                if response.status_code == 200:
                    result_json = response.json()
                    raw_text = result_json.get("text", "").strip()
                    if raw_text:
                        self.log_debug(f"Voice Whisper STT Success | Key #{key_idx+1} ({masked_key}) | Result: {raw_text}")
                        return raw_text, None
                else:
                    log_msg = self.key_pool.mark_rate_limited(key, response.status_code, response.headers, response.text)
                    self.log_debug(f"Voice Whisper STT Rate Limited | Key #{key_idx+1} ({masked_key}): {log_msg}")
            except Exception as e:
                log_msg = self.key_pool.mark_rate_limited(key, 500)
                self.log_debug(f"Voice Whisper STT Exception | Key #{key_idx+1} ({masked_key}): {e}")

        return None, "[Voice Transcription Failed]"

    def check_rpd_quota(self):
        """Sends a lightweight request to Groq to retrieve live RPD quota and status for all keys in the pool."""
        if not self.key_pool.keys:
            return False, "API Key Kosong", None, None, None

        active_model = self.model if self.model else "openai/gpt-oss-20b"
        pool_status_lines = []
        overall_success = False

        for i, key in enumerate(self.key_pool.keys):
            masked = key[:6] + "..." + key[-4:] if len(key) > 10 else "***"
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "User-Agent": "SA-RP-Linggo/1.3"
            }
            payload = {
                "model": active_model,
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 1
            }
            try:
                response = requests.post(self.ENDPOINT, headers=headers, json=payload, timeout=5.0)
                rem = response.headers.get("x-ratelimit-remaining-requests")
                lim = response.headers.get("x-ratelimit-limit-requests")
                rst = response.headers.get("x-ratelimit-reset-requests")

                if response.status_code == 200:
                    overall_success = True
                    self.key_pool.update_key_metrics(key, rem, lim, rst)
                    pool_status_lines.append(f"Key #{i+1} ({masked}): Sisa RPD {rem}/{lim} (Reset: {rst})")
                elif response.status_code == 429:
                    log_msg = self.key_pool.mark_rate_limited(key, 429, response.headers, response.text)
                    pool_status_lines.append(f"Key #{i+1} ({masked}): ⚠️ Rate-Limited (429)")
                elif response.status_code == 401:
                    log_msg = self.key_pool.mark_rate_limited(key, 401)
                    pool_status_lines.append(f"Key #{i+1} ({masked}): ❌ Invalid Key (401)")
                else:
                    pool_status_lines.append(f"Key #{i+1} ({masked}): Error HTTP {response.status_code}")
            except Exception as e:
                pool_status_lines.append(f"Key #{i+1} ({masked}): Connection Error ({e})")

        summary = "\n".join(pool_status_lines) if pool_status_lines else "Tidak ada status key"
        return overall_success, summary, self.last_rpd_remaining, self.last_rpd_limit, self.last_rpd_reset

    def translate(self, text, chat_type="SAYS"):
        """
        Translates foreign text by evaluating full-sentence intent and subculture context
        into authentic street Indonesian. No caching - always fresh.
        """
        if not text or not text.strip():
            return text

        clean_text = text.strip()

        # Master Concise Inbound Translation System Prompt
        system_prompt = (
            f"You are a master street slang & roleplay translator for GTA SA-MP.\n"
            f"Translate the user input text into authentic, natural street {self.target_lang} (Indonesian roleplay lingo using 'lu', 'gue', 'bro', 'sob', 'isilop', 'senpi', etc.).\n\n"
            f"CRITICAL DIRECTIVES:\n"
            f"1. OUTPUT ONLY THE FINAL INDONESIAN TRANSLATION SENTENCE.\n"
            f"2. DO NOT output any reasoning, thinking, explanations, meta-comments, quotes, or language detection notes (such as 'is not Indonesian' or 'Here is the translation').\n"
            f"3. UNFILTERED PROFANITY: Translate all swear words, profanity, and insults directly into matching raw, uncensored Indonesian swear words ('bangsat', 'anjing', 'kontol', 'memek', 'goblok', 'bedebah', 'sialan'). NEVER censor with asterisks (*).\n"
            f"4. PRONOUN MAPPING: 'you / your' MUST be translated as 'lu' or 'kamu', 'I / my' MUST be translated as 'gue' or 'aku'."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": clean_text}
        ]

        result, err = self._send_api_request(messages, temperature=0.1)
        return result if result else err

    def translate_outbound(self, text, style="Standard English"):
        """
        Translates Indonesian outbound chat into English (2 styles: Standard English / American Hood).
        - /me -> 3rd person RP action in selected style
        - /do -> environment/state description in selected style
        - Plain text -> dialogue in selected style
        No caching - always fresh translation.
        """
        if not text or not text.strip():
            return text

        clean_text = text.strip()

        # Normalize to valid style (only 2 supported)
        active_style = style if style in ("Standard English", "American Hood") else "Standard English"

        # Style flavor definitions
        me_flavor = {
            "Standard English": (
                "fluent ENGLISH THIRD-PERSON PRESENT TENSE descriptive roleplay action "
                "(e.g., 'opens the fuel tank and checks the fuel level inside', 'takes out a cigarette and lights it'). "
                "Formal and clear."
            ),
            "American Hood": (
                "gritty African-American HOOD / STREET GANGSTER style THIRD-PERSON PRESENT TENSE action "
                "(e.g., 'slides his hand into his waistband and grips the blicky', 'peeks around the corner watching for opps'). "
                "Raw, street-authentic."
            ),
        }[active_style]

        do_flavor = {
            "Standard English": (
                "fluent ENGLISH descriptive roleplay environment/state "
                "(e.g., 'Is the silver watch visible on the table?', 'The fuel tank appears to be completely empty.'). "
                "Clear and formal."
            ),
            "American Hood": (
                "gritty HOOD / STREET GANGSTER style environment/state "
                "(e.g., 'Can the blicky be seen tucked in his waistband?', 'The whip looks like it is bone dry, no gas left.'). "
                "Raw and street-authentic."
            ),
        }[active_style]

        dialogue_instruction = {
            "Standard English": (
                "Translate the input sentence (Indonesian, regional dialects like Javanese/Sundanese, slang, typos, or profanity) into natural, clear Standard English for GTA SA-MP roleplay. "
                "Preserve all swear words, aggression, and emotion without censorship."
            ),
            "American Hood": (
                "Translate the input sentence (Indonesian, regional dialects like Javanese/Sundanese, slang, typos, or profanity like 'bedebah', 'sialan', 'bangsat', 'anjing', 'kontol') into authentic African-American Hood / Street Gangster English. "
                "CRITICAL RULES: "
                "1. UNCENSORED PROFANITY: Translate all Indonesian insults and swear words ('bedebah', 'sialan', 'bangsat', 'anjing', 'kontol', 'bajingan') into matching raw English swear words ('motherfucker', 'fucking bastard', 'bitch', 'shit', 'dumbass'). NEVER censor with asterisks (*), NEVER refuse, NEVER output meta-commentary. "
                "2. TRANSLATE ALL REGIONAL DIALECTS & SLANG: Translate Javanese, Sundanese, regional slang, typos, and informal speech accurately. "
                "3. Use hood slang NATURALLY (e.g., 'bruh', 'deadass', 'on god', 'no cap', 'fam', 'fool', 'dawg', 'homie', 'ain\'t', 'gonna', 'tryna'). "
                "4. OUTPUT ONLY the final translated English text without quotes or explanations."
            ),
        }[active_style]

        few_shot_me = {
            "Standard English": [
                ("/me mengambil senapan dari dalam tas lalu mengokang senjata.", "/me takes out a rifle from the bag and cocks the firearm."),
                ("/me menyalakan rokok dan menghisapnya perlahan.", "/me lights a cigarette and takes a slow drag."),
            ],
            "American Hood": [
                ("/me membuka tas mengambil senjata lalu mengokang senjata tersebut.", "/me opens the bag, pulls out the strap, and cocks that bitch."),
                ("/me menyalakan rokok dan menghisapnya perlahan.", "/me sparks up a cigarette and takes a slow drag, deadass."),
            ],
        }[active_style]

        few_shot_do = {
            "Standard English": [
                ("/do Jam tangan perak terlihat di atas meja?", "/do Is the silver watch visible on top of the table?"),
                ("/do Tangki bensin terlihat kosong total.", "/do The fuel tank appears to be completely empty."),
            ],
            "American Hood": [
                ("/do Jam tangan perak terlihat di atas meja?", "/do Can you see that silver rollie sitting on the table?"),
                ("/do Tangki bensin terlihat kosong total.", "/do The gas tank is bone dry, no cap."),
            ],
        }[active_style]

        few_shot_dialogue = {
            "Standard English": [
                ("Dasar bedebah sialan, mati saja kamu.", "You damn bastard, just die."),
                ("Dasar bodoh, berkendara yang benar tolol.", "You're an idiot, learn how to drive, fool."),
                ("Hei, kamu mau pergi kemana?", "Hey, where are you headed?"),
            ],
            "American Hood": [
                ("Dasar bedebah sialan, mati saja kamu.", "You motherfucking bastard, just die, deadass."),
                ("Dasar bodoh, berkendara yang benar tolol.", "Bruh you stupid as hell, learn how to drive, fool."),
                ("Hei, kamu mau pergi kemana?", "Aye, where you finna go, homie?"),
                ("Aku mau cari masalah sama kamu.", "I'm on yo head, no cap, on god."),
            ],
        }[active_style]

        lower_text = clean_text.lower()

        if lower_text.startswith("/me"):
            system_prompt = (
                f"You are a master GTA SA-MP roleplay translator. "
                f"Translate the input action into {active_style.upper()} English. "
                f"RULES:\n"
                f"1. Output MUST start with '/me '.\n"
                f"2. Translate third-person action body into natural {me_flavor}.\n"
                f"3. OUTPUT ONLY the final translated '/me [ENGLISH ACTION]' string without quotes, explanations, or thinking steps."
            )
        elif lower_text.startswith("/do"):
            system_prompt = (
                f"You are a master GTA SA-MP roleplay translator. "
                f"Translate the environment/state input into {active_style.upper()} English. "
                f"RULES:\n"
                f"1. Output MUST start with '/do '.\n"
                f"2. Translate environment/state description into natural {do_flavor}.\n"
                f"3. OUTPUT ONLY the final translated '/do [ENGLISH STATE]' string without quotes, explanations, or thinking steps."
            )
        else:
            system_prompt = (
                f"You are a master GTA SA-MP roleplay outbound translator converting Indonesian text (slang, regional dialects, or typos) into spoken English.\n"
                f"STYLE GOAL: {active_style.upper()}\n"
                f"INSTRUCTION: {dialogue_instruction}\n"
                f"RULES:\n"
                f"1. Output ONLY the final translated English text.\n"
                f"2. Do NOT include quotes, explanations, or original text."
            )

        messages = [{"role": "system", "content": system_prompt}]
        if lower_text.startswith("/me"):
            for u_ex, a_ex in few_shot_me:
                messages.append({"role": "user", "content": u_ex})
                messages.append({"role": "assistant", "content": a_ex})
        elif lower_text.startswith("/do"):
            for u_ex, a_ex in few_shot_do:
                messages.append({"role": "user", "content": u_ex})
                messages.append({"role": "assistant", "content": a_ex})
        else:
            for u_ex, a_ex in few_shot_dialogue:
                messages.append({"role": "user", "content": u_ex})
                messages.append({"role": "assistant", "content": a_ex})

        messages.append({"role": "user", "content": clean_text})

        result, err = self._send_api_request(messages, temperature=0.2)
        return result if result else text


class TranslationWorker(QThread):
    """
    Async QThread queue worker to process translation items sequentially without freezing UI.
    Ignores native Indonesian chat to conserve API quota and keep overlay clean.
    """
    translation_complete = pyqtSignal(dict)  # Emits item dict with added 'translated' key

    def __init__(self, translator):
        super().__init__()
        self.translator = translator
        self.queue = []
        self.running = True

    def add_job(self, chat_item):
        self.queue.append(chat_item)

    def stop(self):
        self.running = False
        self.wait()

    def run(self):
        import time
        while self.running:
            if self.queue:
                item = self.queue.pop(0)
                original_content = item.get("content", "")
                chat_type = item.get("type", "SAYS")

                # Filter out pure native Indonesian chat before making API request
                if not should_translate_inbound(original_content):
                    continue

                # Perform translation for foreign text
                translated = self.translator.translate(original_content, chat_type=chat_type)

                # If translation failed or returned identical string, skip displaying
                clean_orig = original_content.strip().lower()
                clean_trans = translated.strip().lower()
                if clean_orig == clean_trans:
                    continue

                item["translated"] = translated
                item["rpd_remaining"] = self.translator.last_rpd_remaining
                item["rpd_limit"] = self.translator.last_rpd_limit
                item["rpd_reset"] = self.translator.last_rpd_reset
                self.translation_complete.emit(item)
            else:
                time.sleep(0.1)
