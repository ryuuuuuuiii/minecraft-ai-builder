# ⛏ Minecraft AI Builder

Web app yang memungkinkan kamu mendeskripsikan bangunan dalam bahasa natural, lalu AI secara otomatis akan membangunnya langsung di Minecraft Bedrock Edition via WebSocket.

---

## 📋 Arsitektur

```
Browser (frontend/index.html)
        │  HTTP POST /build
        ▼
FastAPI Server (port 8000)
        │  Groq AI (llama-3.3-70b-versatile)
        │  WebSocket send command
        ▼
WebSocket Server (port 8080)
        │  ws://IP:8080
        ▼
Minecraft Bedrock Edition
```

---

## 🚀 Cara Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Konfigurasi environment

```bash
cp .env.example .env
```

Edit `.env` dan isi `GROQ_API_KEY` dengan API key dari [console.groq.com](https://console.groq.com) (gratis).

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=llama-3.3-70b-versatile
WS_HOST=0.0.0.0
WS_PORT=8080
API_HOST=0.0.0.0
API_PORT=8000
```

### 3. Jalankan backend

```bash
python main.py
```

Output yang diharapkan:
```
[WS] Starting Minecraft WebSocket server on ws://0.0.0.0:8080
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 4. Buka frontend

Buka file `frontend/index.html` di browser (double-click atau drag ke browser).

### 5. Hubungkan Minecraft

1. Buka Minecraft Bedrock Edition
2. Masuk ke world (singleplayer atau multiplayer)
3. Tekan `T` untuk membuka chat
4. Ketik: `/connect ws://IP_PC_KAMU:8080`
   - Cari IP kamu: Windows → `ipconfig`, Mac/Linux → `ifconfig`
   - Contoh: `/connect ws://192.168.1.5:8080`
5. Status di frontend berubah **hijau** = berhasil terhubung ✓

### 6. Build!

Ketik deskripsi bangunan di textarea, lalu klik **BUILD NOW**.

---

## 💡 Contoh Prompt

| Prompt | Hasil |
|--------|-------|
| `rumah kayu 5x5 dengan atap cobblestone` | Rumah sederhana dari kayu |
| `menara batu setinggi 10 lantai ukuran 3x3` | Menara tinggi dari stone |
| `kastil kecil dari cobblestone` | Kastil dengan tembok |
| `jembatan kayu sepanjang 15 blok` | Jembatan memanjang |
| `piramida batu ukuran 7x7` | Piramida bertingkat |

---

## 🔧 Struktur Project

```
minecraft-ai-builder/
├── main.py              # FastAPI + WebSocket server
├── requirements.txt     # Python dependencies
├── .env.example         # Template environment variables
├── .env                 # (kamu buat sendiri, tidak di-commit)
└── frontend/
    └── index.html       # Web app (single file, tidak perlu server)
```

---

## ⚠️ Troubleshooting

**Status tetap merah / "Belum terhubung"**
- Pastikan `python main.py` sudah berjalan
- Pastikan firewall Windows tidak memblokir port 8080
- Coba: `Windows Defender Firewall → Allow an app → Python`

**`/connect` di Minecraft tidak berhasil**
- Minecraft Bedrock butuh mode "developer" diaktifkan
- Windows: Settings → Privacy → Local Network → Aktifkan untuk Minecraft

**AI menghasilkan command yang error**
- Ini normal untuk struktur kompleks; coba prompt yang lebih sederhana
- Command yang gagal ditampilkan di log dengan warna merah

**CORS error di browser**
- Pastikan buka `index.html` langsung sebagai file, bukan via `localhost`
- Atau gunakan server seperti `python -m http.server 3000` di folder frontend

---

## 🛠️ Teknologi

- **Backend**: Python, FastAPI, websockets, Groq SDK
- **AI**: Groq Cloud (llama-3.3-70b-versatile) — gratis, sangat cepat
- **Frontend**: Vanilla HTML/CSS/JS, tema Minecraft pixel-art
- **Protokol**: Minecraft Bedrock WebSocket API (JSON packets)
