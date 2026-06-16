# DCD — Context Diagram (Level 0)

## Sistem: mimo-farmer Web UI

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                        ┌─────────────┐                          │
│                        │   Browser   │                          │
│                        │  (User UI)  │                          │
│                        └──────┬──────┘                          │
│                               │                                 │
│                          HTTP │ WebSocket                        │
│                               ▼                                 │
│  ┌────────────┐      ┌───────────────┐      ┌───────────────┐  │
│  │ generator  │◄────►│               │◄────►│   accounts/   │  │
│  │  .email    │      │  mimo-farmer  │      │  batch_*.txt  │  │
│  └────────────┘      │   Web Server  │      └───────────────┘  │
│                      │  (FastAPI)    │                          │
│  ┌────────────┐      │               │      ┌───────────────┐  │
│  │  Xiaomi    │◄────►│               │◄────►│  Playwright   │  │
│  │  Account   │      │               │      │  Browser      │  │
│  │  Server    │      └───────────────┘      └───────────────┘  │
│  └────────────┘             ▲                                   │
│                             │                                   │
│                      ┌──────┴──────┐                            │
│                      │   config.py │                            │
│                      └─────────────┘                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Entitas Eksternal

| Entitas | Koneksi | Data Masuk | Data Keluar |
|---------|---------|------------|-------------|
| **Browser (User)** | HTTP + WebSocket | Account data, stats, progress | Create request, settings, export request |
| **Xiaomi Account Server** | HTTPS (via Playwright) | Signup pages, OTP, CAPTCHA | Form data, credentials |
| **generator.email** | HTTPS (via Playwright) | OTP emails, domain list | Inbox polling requests |
| **accounts/batch_*.txt** | File system (read/write) | — | Account credentials, batch data |
| **config.py** | Python import | — | Default settings, URLs |
| **Playwright Browser** | CDP (Chrome DevTools Protocol) | Page state, network | Click, type, navigate |

## Keterangan

- **User** berinteraksi hanya melalui browser (localhost:8080)
- **FastAPI server** adalah central hub yang mengorkestrasi semua komponen
- **Playwright** menjalankan automation pipeline (sama seperti CLI)
- **File system** digunakan sebagai persistent storage (tidak ada database)
- Semua koneksi eksternal (Xiaomi, generator.email) terjadi melalui Playwright, bukan langsung dari server
