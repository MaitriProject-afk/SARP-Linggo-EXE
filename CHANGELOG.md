# 📋 SA-RP Linggo - Changelog

All notable changes to the **SA-RP Linggo** project are documented here.

## 🚀 [v1.3.5] - 2026-08-25

### 🌟 Fitur Utama & Pembaruan Sistem (Major Features & Enhancements)
- **🔑 Multi-Key API Rolling Engine (Dynamic Token Pool)**:
  - Rotasi kunci API Groq secara otomatis (*round-robin*) tanpa batas jumlah token yang diinput pengguna.
  - Penanganan *Rate Limit* (HTTP 429 & 401) otomatis yang memisahkan *cooldown* per-menit (60 detik) dengan *cooldown* harian RPD (1 jam).
  - *Fail-safe Recovery*: Apabila seluruh token terkena *cooldown*, sistem secara cerdas memilih token dengan durasi pemulihan tersingkat agar aplikasi tidak *freeze* atau mati.
  - UI Input Dinamis di menu Pengaturan (`QPlainTextEdit`) yang mendukung pendaftaran token sebanyak-banyaknya (dipisahkan koma atau baris baru) dengan indikator status real-time (`🔑 X Token Terdaftar | Rolling Pointer: Key #1`).
  - Fitur **"Cek Sisa RPD 🔄"** kini menampilkan rincian sisa kuota harian untuk setiap token di dalam pool secara transparan.

- **⚡ Token Budget Optimization (<1000 Tokens/Request)**:
  - Mengatasi masalah *Reasoning Bloat / Token Leak* pada model `openai/gpt-oss-20b` yang sebelumnya memakan 1500–1800+ token per request singkat akibat pemikiran internal model.
  - Mempersingkat *System Prompt* dan memperketat pengontrolan *max_tokens* sehingga penggunaan token per terjemahan ditekan secara drastis hingga jauh di bawah 1000 token per request (rata-rata 300–500 token total).

- **🛠️ Mode Pengembang & Pemantauan Log Real-Time (Developer Mode)**:
  - Penambahan sakelar **Developer Mode** pada menu Pengaturan.
  - Pencatatan rinci ke file `debug_log.txt` yang mencakup: Masked Key #, Nama Model, Rincian Token (`Prompt`, `Output`, `Reasoning`, `Total`), Sisa Kuota RPD (`x-ratelimit-remaining`), Kode Status HTTP, serta Teks Hasil Terjemahan.
  - Akses cepat tombol **"Buka Debug Log 📜"** di menu Pengaturan untuk membuka file log secara langsung tanpa harus men-minimize game.

### 🛠️ Perbaikan Bug & Efisiensi Engine (Fixes & Engine Improvements)
- **🧠 Reasoning Leak & Output Purification**:
  - Mengeliminasi teks *lead-in* pemikiran AI (seperti `"We need to translate..."`, `"is not Indonesian..."`, `"Here is the translation:"`) agar tidak bocor ke obrolan game SAMP.
  - Filter otomatis multi-baris yang menjamin hanya baris kalimat terjemahan akhir yang ditampilkan.
- **🤬 Uncensored Roleplay Profanity & Pronoun Mapping**:
  - Mengubah instruksi *system prompt* untuk mempertahankan umpatan kasar tanpa sensor asterisk (`bangsat`, `anjing`, `kontol`, `memek`, `goblok`, `bedebah`, `sialan`) demi kebutuhan *mature roleplay*.
  - Pemetaan kata ganti yang konsisten (`you/your` $\rightarrow$ `lu/kamu`, `I/my` $\rightarrow$ `gue/aku`).
- **📋 Clipboard Outbound Stability & Universal Inbound Filter**:
  - Memperbaiki bug fitur *Clipboard Outbound* yang hang/freeze saat pengguna melakukan spam terjemahan secara beruntun.
  - Menghapus pembatasan bahasa ketat pada translasi obrolan masuk (*chatlog inbound*), sehingga obrolan dengan gaul/slang daerah tetap diterjemahkan secara mulus ke Bahasa Indonesia tanpa error skip.

---

## 🚀 [v1.3.0] - 2026-08-23

### 🌟 Fitur Utama & Peningkatan Arsitektur (Major Features & Architecture)
- **🖥️ Forced Win32 Native TopMost Overlay Engine (Exclusive Fullscreen Support)**:
  - Memaksa overlay SA-RP Linggo tetap tampil melayang di atas layar game GTA:SA / SA-MP bahkan dalam mode **Exclusive Fullscreen** tanpa memerlukan mod windowed.
  - Memanfaatkan Windows API low-level (`SetWindowLongPtrW` & `SetWindowPos`) dengan flag `WS_EX_TOPMOST` & `WS_EX_NOACTIVATE` pada tingkat Windows Desktop Window Manager (DWM).
  - Dilengkapi *1-Second Win32 Force Enforcement Loop* untuk mencegah *render pipeline* DirectX 9 menimpa tampilan overlay.
- **🚫 Anti-Alt Tab / Anti-Minimize In-Game Settings Dialog**:
  - Menu Pengaturan (`SettingsDialog`) kini dapat dibuka dan diatur langsung di dalam game GTA **tanpa memicu GTA ter-Alt-Tab atau ter-minimize ke taskbar**.
  - Menyuntikkan flag `WS_EX_NOACTIVATE` pada jendela Pengaturan dan seluruh popup notifikasi (`show_noactivate_msgbox`), menjamin GTA tetap berjalan mulus di latar belakang saat pengoperasian.
- **🖱️ Fix QComboBox Dropdown Interaction**:
  - Memperbaiki bug menu *dropdown* (pilihan Hotkey Mic, Hotkey Hide, Pilihan Bahasa, dan Style) yang sebelumnya tertutup atau tidak bisa diklik saat overlay aktif.
  - Memastikan seluruh menu *dropdown* memiliki prioritas z-order paling atas di layar.
- **⚡ Smart Keyboard Hook Optimization**:
  - Mengoptimalkan manajemen *keyboard hook* Windows agar tidak melakukan *unhook/re-hook* palsu saat menyimpan pengaturan jika hotkey tidak diubah.
- **💻 Arsitektur Modern & Kompatibilitas ARM64**:
  - Kompatibel 100% Native 64-bit untuk Windows 10 & 11 (x64), serta laptop Windows 11 ARM (Snapdragon X Series) via Windows Prism Emulation Engine.

---

## 🚀 [v1.2.0] - 2026-08-19

### 🌟 Fitur Baru (New Features)
- **🙈 Total Hide / Stealth Mode (`F7` Hotkey & System Tray)**:
  - Fitur menyembunyikan overlay 100% dari layar untuk kebutuhan *streamer* atau *screenshot roleplay*.
  - Terintegrasi penuh dengan **Windows System Tray Icon** (sebelah jam) dengan notifikasi status & kontrol Show/Hide.
  - Hotkey toggle dapat diubah sesuai preferensi melalui menu Settings.
- **🎙️ Tampilan Transkrip Suara Asli (Original Voice Display)**:
  - Kartu feed mikrofon kini menampilkan 2 baris informasi transparan:
    - **Baris 1**: Transkrip Bahasa Indonesia asli yang didengar oleh AI Mic (`[HH:MM:SS] 🎙️ Transkrip Suara (ID): "..."`).
    - **Baris 2**: Hasil terjemahan English (Standard/American Hood) + tombol Salin (`📋 Salin`) & indikator kuota RPD.
- **🧠 Phonetic Wildcard Normalization Engine**:
  - Algoritma pembersih kata otomatis yang menangkap salah dengar Whisper STT (seperti *"Persesmi"*, *"Selesmi"*, *"Slashmi"*, *"Slasmi"*, *"proses do"*) dan mengonversinya secara paksa menjadi perintah RP resmi `/me` atau `/do`.

---

### 🛠️ Peningkatan & Perbaikan (Fixes & Improvements)
- **🚫 Anti-AI Em-Dash Cleaner**:
  - Mengeliminasi tanda *em-dash* (`—`), *en-dash* (`–`), dan *double-hyphen* (`--`) bawaan LLM yang membuat teks terjemahan terlihat kaku seperti buatan AI.
  - Hasil terjemahan kini menggunakan tanda baca alami (koma & titik) yang otentik untuk obrolan game SAMP.
- **🎙️ Pre-Warmed Continuous Audio Ring Buffer (0ms Mic Start Lag)**:
  - Memperbaiki bug kata pertama terpotong saat menekan hotkey mic (seperti *"Dasar"* terpotong menjadi *"Pasar"* atau *"Sar"*).
  - Microphone kini mengelola *ring buffer* 450ms *pre-recording*, menangkap kata pertama 100% utuh tanpa *delay* inisialisasi driver audio.
- **⚡ Hotkey Debouncing & Anti-Blinking Engine**:
  - Memperbaiki bug *blinking* (kedap-kedip berulang saat menekan hotkey hide) akibat pemicuan sinyal *auto-repeat* OS Windows.
  - Menggunakan *Press-State Lock* dengan *cooldown* 400ms untuk menjamin 1 kali respon toggle yang solid.
- **📚 Enhanced Whisper STT Vocabulary Prompt**:
  - Mengoptimalkan prompt model Groq Whisper API dengan daftar kosakata khusus SAMP Roleplay & kata-kata sehari-hari Bahasa Indonesia untuk akurasi transkripsi tingkat tinggi.
- **🔔 System Tray Activation Optimization**:
  - Memperbaiki *double-trigger* pada aksi tray icon agar tidak memicu toggle ganda saat diklik.

---

## 📦 [v1.1.0] - 2026-08-10
- **Fitur Voice Outbound (Speech-to-Text to Translation)**.
- **Dynamic Outbound Roleplay Styles (Standard English & American Hood)**.
- **Pembersih Profanity Asterisk (Uncensored Street Slang)**.

---

## 📦 [v1.0.0] - 2026-08-07
- Initial Release of **SA-RP Linggo**.
- Real-time SAMP Chatlog Inbound & Outbound Clipboard Translation.
