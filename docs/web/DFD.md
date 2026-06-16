# DFD — Data Flow Diagram

## Level 0: Context Diagram

```
┌──────────┐                           ┌──────────────┐
│          │── Create Request ────────►│              │
│          │── Settings Update ───────►│              │
│  User    │                          │  mimo-farmer │
│ (Browser)│◄── Dashboard Stats ──────│  Web Server  │
│          │◄── Progress Updates ─────│  (FastAPI)   │
│          │◄── Account List ─────────│              │
│          │◄── Export File ──────────│              │
└──────────┘                           └──────────────┘
```

## Level 1: Proses Utama

```
                    ┌─────────────────────────────────────────┐
                    │          mimo-farmer Web Server          │
                    │                                         │
┌──────────┐       │  ┌─────────┐    ┌──────────────────┐   │     ┌───────────┐
│          │──1.1─►│  │ P1      │───►│ P2               │───┼────►│ accounts/ │
│          │Create │  │ API     │    │ Account Creator  │   │     │ batch*.txt│
│          │Request│  │ Handler │    │ (Playwright)     │   │     └───────────┘
│          │       │  └────┬────┘    └────────┬─────────┘   │
│          │       │       │                  │              │
│  User    │       │       │ 1.2              │ 2.1          │
│ (Browser)│       │       ▼                  ▼              │
│          │  WS   │  ┌─────────┐    ┌──────────────────┐   │     ┌───────────┐
│          │◄──────│  │ P3      │◄───│ P4               │───┼────►│ Xiaomi    │
│          │Updates│  │ Real-   │    │ External         │   │     │ Server    │
│          │       │  │ time    │    │ Services         │   │     └───────────┘
│          │       │  │ Manager │    │ (Playwright)     │   │
│          │       │  └─────────┘    └────────┬─────────┘   │     ┌───────────┐
│          │       │       │                  │              │     │ generator │
│          │──5.1─►│       │ 3.1              │ 4.1          ├────►│ .email    │
│          │Export │       ▼                  ▼              │     └───────────┘
│          │Request│  ┌─────────┐    ┌──────────────────┐   │
│          │       │  │ P5      │◄───│ P6               │   │     ┌───────────┐
│          │◄──────│  │ File    │    │ Config           │───┼────►│ config.py │
│          │Export │  │ Manager │    │ Manager          │   │     └───────────┘
│          │File   │  └─────────┘    └──────────────────┘   │
└──────────┘       │                                         │
                    └─────────────────────────────────────────┘
```

## Detail Proses

### P1: API Handler
Menerima request HTTP dari frontend, validasi input, routing ke proses yang tepat.

| Flow | Data | Arah |
|------|------|------|
| 1.1 | `{mode, referral, count, fast}` | User → P1 |
| 1.2 | `{mode, referral, count, fast}` | P1 → P2 |
| 1.3 | `{stats, accounts, settings}` | P1 → User (response) |

### P2: Account Creator
Menjalankan Playwright pipeline untuk membuat akun. Berjalan di background thread.

| Flow | Data | Arah |
|------|------|------|
| 2.1 | `{email, password, form_data}` | P2 → Xiaomi Server |
| 2.2 | `{otp_request}` | P2 → generator.email |
| 2.3 | `{step_status, progress, logs}` | P2 → P3 |
| 2.4 | `{account_result}` | P2 → P5 |

### P3: Real-time Manager
Mengelola WebSocket connections dan broadcast progress updates.

| Flow | Data | Arah |
|------|------|------|
| 3.1 | `{step, status, message, progress_pct}` | P2 → P3 |
| 3.2 | `{ws_message}` | P3 → User (WebSocket) |

### P4: External Services
Interface ke layanan eksternal melalui Playwright.

| Flow | Data | Arah |
|------|------|------|
| 4.1 | `{signup_form, captcha, otp}` | P4 → Xiaomi |
| 4.2 | `{email_poll, otp_code}` | P4 → generator.email |
| 4.3 | `{page_state, response}` | Xiaomi → P4 |
| 4.4 | `{email_content, otp}` | generator.email → P4 |

### P5: File Manager
Membaca dan menulis batch files, parsing account data.

| Flow | Data | Arah |
|------|------|------|
| 5.1 | `{batch_data}` | P2 → P5 |
| 5.2 | `{parsed_accounts}` | P5 → P1 (read) |
| 5.3 | `{export_file}` | P5 → User |

### P6: Config Manager
Membaca dan mengupdate konfigurasi.

| Flow | Data | Arah |
|------|------|------|
| 6.1 | `{settings}` | P6 ↔ config.py |
| 6.2 | `{config_values}` | P6 → P2 |

## Data Store

| Store | Tipe | Isi |
|-------|------|-----|
| `accounts/batch_*.txt` | Flat file | Account credentials per batch |
| `config.py` | Python module | Default settings |
| `.audio_cache/` | Temp files | reCAPTCHA audio files |
| WebSocket rooms | In-memory | Active connections + progress state |
