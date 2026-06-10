# Minecraft AI Builder — Bedrock Edition (WebSocket)

Build bangunan di Minecraft Bedrock pakai prompt AI!

---

## Cara Pakai

### 1. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Jalankan backend

```bash
python main.py
```

Output yang muncul:
```
🟢  Minecraft AI Builder (Bedrock WebSocket)
    AI     : Groq / llama-3.3-70b-versatile
    WS     : ws://0.0.0.0:8080
    API    : http://0.0.0.0:8000
  Di Minecraft Bedrock, ketik di chat:
  /connect ws://YOUR_PC_IP:8080
```

### 3. Buka frontend

Buka file `frontend/index.html` di browser.

### 4. Hubungkan Minecraft

1. Buka Minecraft Bedrock
2. Masuk ke world (mode Creative direkomendasikan)
3. Ketik di chat:
   ```
   /connect ws://localhost:8080
   ```
   Kalau Minecraft di device lain (HP/tablet), ganti `localhost` dengan IP PC kamu.
4. Status di frontend berubah jadi **"Minecraft terhubung ✓"**

### 5. Build!

Ketik prompt di frontend → klik **Build in Minecraft!** → bangunan muncul di depan karakter kamu.

---

## Cari IP PC kamu

**Windows:** Buka CMD → ketik `ipconfig` → lihat "IPv4 Address"  
**Mac/Linux:** Buka Terminal → ketik `ifconfig` atau `ip addr`

Biasanya formatnya `192.168.x.x`

---

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| Status tetap "Belum terhubung" | Backend belum jalan, atau port 8080 diblokir firewall |
| `/connect` error di Minecraft | Coba ganti `localhost` dengan IP PC (misal `192.168.1.5`) |
| Command gagal semua | Pastikan mode Creative dan cheats diaktifkan di world |
| AI error | Cek `GROQ_API_KEY` di file `.env` |

---

## Struktur Project

```
mc-bedrock-builder/
├── backend/
│   ├── main.py          ← Server utama (FastAPI + WebSocket)
│   ├── .env             ← API key & config
│   └── requirements.txt
└── frontend/
    ├── index.html       ← UI web
    └── script.js        ← Logic frontend
```
