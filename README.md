<div align="center">

# 🎮 SA-RP Linggo

**Real-Time AI Translation Overlay for GTA SA-MP Roleplay**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.0+-41CD52?style=flat-square&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![Groq API](https://img.shields.io/badge/Groq-llama--3.1--8b--instant-F55036?style=flat-square)](https://console.groq.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

*Terjemahkan chat GTA SA-MP secara real-time dengan AI — tanpa ganggu gameplay!*

</div>

---

## ✨ Fitur Utama

| Fitur | Deskripsi |
|---|---|
| 🔍 **Inbound Translation** | Menerjemahkan chat pemain lain (SAYS, /me, /do) ke Bahasa Indonesia secara otomatis |
| ⌨️ **Outbound Translation** | Ketik Bahasa Indonesia → `CTRL+C` → AI terjemahkan → `CTRL+V` langsung ke game |
| 🧠 **Full-Sentence AI Reasoning** | Memahami konteks penuh kalimat, bukan terjemahan kata per kata |
| 🎭 **Subculture Slang** | Mengerti slang American Hood, Cartel, Italian Mob, dll. |
| 🎨 **Matte Slate UI** | Overlay transparan bergaya gelap dengan ikon SVG profesional |
| 🔒 **Click-Through Mode** | Overlay tidak menghalangi klik mouse saat bermain |
| ⚡ **Anti-Loop Protection** | Tidak akan memangil API berulang untuk teks yang sama |

---

## 📋 Prasyarat

- **Python 3.11+**
- **GTA San Andreas** + **SA-MP (0.3.7 / SAMP-RP)**
- **[Groq API Key](https://console.groq.com)** (Gratis — 14.400 request/hari)

---

## 🚀 Instalasi & Cara Pakai

### Option 1: Download `.exe` Standalone (Untuk Pemain — Tanpa Python!)

1. **Download Aplikasi**:
   Buka halaman [Releases](https://github.com/YOUR_USERNAME/sa-rp-linggo/releases) di GitHub dan download `SA-RP Linggo.exe`.
2. **Jalankan Aplikasi**:
   Double click `SA-RP Linggo.exe`.
3. **Setting Groq API Key**:
   Buka tombol **Settings ⚙️** pada overlay, lalu masukkan **Groq API Key** kamu. (Gratis di [console.groq.com](https://console.groq.com)).
4. **Selesai!** Aplikasi siap digunakan saat bermain SA-MP.

---

### Option 2: Jalankan dari Source (Untuk Developer)

```bash
# 1. Clone Repository
git clone https://github.com/YOUR_USERNAME/sa-rp-linggo.git
cd sa-rp-linggo

# 2. Install Dependencies
pip install -r requirements.txt

# 3. Setup Config
copy config.example.json config.json

# 4. Jalankan Aplikasi
python main.py
```

### 🛠️ Build Executable Sendiri (.exe)
Jika ingin mengompilasi `.exe` sendiri dari source:
```bash
# Cukup jalankan batch file build
build.bat
```
Hasil `.exe` akan berada di folder `dist\SA-RP Linggo.exe`.

---

## 🎮 Cara Penggunaan

### Inbound (Terjemahan Chat Orang Lain)
Overlay akan otomatis mendeteksi chat bahasa asing dan menerjemahkannya ke Bahasa Indonesia. Tidak perlu melakukan apa-apa!

### Outbound (Kamu Mau Bicara Bahasa Inggris)
1. Aktifkan fitur di **Settings → Enable Outbound Translation** ✅
2. Ketik kalimat Bahasa Indonesia di chatbox SAMP
3. Tekan `CTRL+A` → `CTRL+C`
4. SA-RP Linggo menerjemahkan otomatis
5. Tekan `CTRL+V` → `ENTER` — kirim!

**Style Tersedia:**
- 💼 `Standard English` — Bahasa Inggris baku dan jelas *(default)*
- 🇺🇸 `American Hood` — Street gangster slang authentic

### Perintah RP Khusus
| Perintah | Perlakuan |
|---|---|
| `/me membuka pintu mobil` | `/me opens the car door` (3rd person action) |
| `/do apakah ada yang melihat?` | `/do Is anyone watching?` (environment state) |
| `teks biasa` | Dialog percakapan sesuai style |

---

## ⚙️ Konfigurasi

| Key | Default | Keterangan |
|---|---|---|
| `groq_api_key` | `""` | API key dari console.groq.com |
| `groq_model` | `llama-3.3-70b-versatile` | Model AI yang digunakan |
| `chatlog_path` | *(kosong)* | Path ke chatlog.txt SAMP |
| `outbound_style` | `Standard English` | Style bahasa outbound |
| `enable_clipboard_outbound` | `true` | Aktif/nonaktif fitur outbound |
| `opacity` | `0.9` | Transparansi overlay (0.1–1.0) |
| `font_size` | `11` | Ukuran font overlay |
| `max_feed_items` | `50` | Maks item di feed overlay |

---

## 🏗️ Struktur Project

```
sa-rp-linggo/
├── main.py                  # Entry point aplikasi
├── requirements.txt         # Python dependencies
├── config.example.json      # Template konfigurasi
│
├── core/
│   ├── translator.py        # AI Translation Engine (Groq API)
│   ├── chat_listener.py     # Chatlog file watcher
│   ├── clipboard_listener.py # Outbound clipboard handler
│   └── config.py            # Config manager
│
└── ui/
    ├── overlay.py           # Main overlay window & settings
    ├── styles.py            # CSS stylesheet
    └── icons.py             # SVG icon definitions
```

---

## 🤝 Kontribusi

Pull Request sangat disambut! Untuk perubahan besar, buka Issue terlebih dahulu.

1. Fork repository ini
2. Buat branch fitur: `git checkout -b feature/NamaFitur`
3. Commit: `git commit -m 'Add: NamaFitur'`
4. Push: `git push origin feature/NamaFitur`
5. Buat Pull Request

---

## 📄 Lisensi

Didistribusikan di bawah **MIT License**. Lihat [LICENSE](LICENSE) untuk informasi lebih lanjut.

---

<div align="center">
  Made with ❤️ for the SA-MP Roleplay Community
</div>
