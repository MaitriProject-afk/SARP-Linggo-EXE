<div align="center">

# 🎮 SA-RP Linggo v1.3.6 (EXE Version)

**Real-Time AI Translation & Slang Converter Overlay for GTA SA-MP Roleplay**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.0+-41CD52?style=flat-square&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![Groq API](https://img.shields.io/badge/Groq-llama--3.3--70b--versatile-F55036?style=flat-square)](https://console.groq.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/Status-100%25%20Free%20%26%20Open%20Source-blue.svg)](https://github.com/MaitriProject-afk/SARP-Linggo-EXE)

*Terjemahkan chat GTA SA-MP secara real-time dengan AI — 100% Bebas Lisensi & Lisensi Gratis!*

</div>

---

Mulai versi 1.3.0+, **SA-RP Linggo telah resmi menjadi proyek 100% Free & Open-Source (MIT License)** di bawah naungan **MaitriProject**. Seluruh sistem lisensi/token telah dihapus penuh — Anda cukup memasukkan Groq API Key milik sendiri (gratis) untuk langsung menggunakannya.

---

## ✨ Fitur Utama v1.3.6

| Fitur | Deskripsi |
|---|---|
| 🔍 **Inbound Live Chat Translator** | Menerjemahkan chat pemain lain (SAYS, /me, /do) ke Bahasa Indonesia secara otomatis dari `chatlog.txt` |
| ⌨️ **Outbound Auto-Translate** | Ketik Bahasa Indonesia → `CTRL+C` → AI terjemahkan → `CTRL+V` langsung ke game |
| 🇺🇸 **American Hood & Ghetto Slang Mode** | Pilihan terjemahan gaya bahasa jalanan Amerika (AAVE / Gangster Slang) |
| 🧠 **Full-Sentence AI Reasoning** | Memahami konteks penuh kalimat, bukan sekadar terjemahan kata per kata |
| 🔑 **Rolling Groq Token Pool** | Mendukung multiple API Key Groq dengan rotasi otomatis saat rate limit hit |
| 🔓 **100% License-Free** | Tanpa token lisensi Discord, tanpa HWID lock, tanpa pengumpulan data pribadi |
| 🎨 **Matte Slate UI** | Overlay transparan bergaya gelap dengan font responsif dan ikon SVG profesional |
| 🔒 **Click-Through Mode** | Overlay tidak menghalangi klik mouse saat bermain game |
| ⚡ **Anti-Loop Protection** | Tidak akan memanggil API berulang untuk teks yang sama |

---

## 📋 Prasyarat

- **Windows 10 / 11 (64-bit)**
- **GTA San Andreas** + **SA-MP (0.3.7 / SAMP-RP)**
- **[Groq API Key](https://console.groq.com)** (Gratis — Pembuatan instant tanpa kartu kredit)

---

## 🚀 Instalasi & Cara Pakai

### Option 1: Download `.exe` Standalone (Untuk Pemain — Tanpa Instalasi Python!)

1. **Download Aplikasi**:
   Buka halaman **[Releases](https://github.com/MaitriProject-afk/SARP-Linggo-EXE/releases)** di GitHub dan download `SA-RP Linggo.exe`.
2. **Jalankan Aplikasi**:
   Double click `SA-RP Linggo.exe`.
3. **Setting Groq API Key**:
   Buka tombol **Settings ⚙️** pada overlay, lalu masukkan **Groq API Key** Anda (Gratis di [console.groq.com](https://console.groq.com)).
4. **Selesai!** Aplikasi siap digunakan saat bermain SA-MP.

---

### Option 2: Jalankan dari Source (Untuk Developer)

```bash
# 1. Clone Repository
git clone https://github.com/MaitriProject-afk/SARP-Linggo-EXE.git
cd SARP-Linggo-EXE

# 2. Install Dependencies
pip install -r requirements.txt

# 3. Jalankan Aplikasi
python main.py
```

### 🛠️ Build Executable Sendiri (.exe)
Jika ingin mengompilasi `.exe` sendiri dari source:
```bash
python -m PyInstaller --noconfirm --onefile --windowed --name "SA-RP Linggo" main.py
```
Hasil `.exe` akan berada di folder `dist\SA-RP Linggo.exe`.

---

## 🎮 Cara Penggunaan

### Inbound (Terjemahan Chat Orang Lain)
Overlay akan otomatis mendeteksi chat bahasa asing di `chatlog.txt` dan menerjemahkannya ke Bahasa Indonesia.

### Outbound (Kamu Mau Bicara Bahasa Inggris)
1. Aktifkan fitur di **Settings → Enable Outbound Translation** ✅
2. Ketik kalimat Bahasa Indonesia di chatbox SAMP
3. Tekan `CTRL+A` → `CTRL+C`
4. SA-RP Linggo menerjemahkan otomatis ke clipboard
5. Tekan `CTRL+V` → `ENTER` untuk mengirim chat ke game!

**Style Tersedia:**
- 💼 `Standard English` — Bahasa Inggris baku dan jelas *(default)*
- 🇺🇸 `American Hood` — Street gangster slang authentic

---

## 📄 Lisensi & Attribution

Didistribusikan di bawah **[MIT License](LICENSE)** - 100% Free & Open Source.

Dikembangkan & Dipelihara oleh **[MaitriProject](https://github.com/MaitriProject-afk)** untuk mendukung komunitas Roleplay GTA SA-MP Indonesia.
