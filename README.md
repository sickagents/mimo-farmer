# mimo-farmer

Automated Xiaomi MiMo account creator with referral farming, captcha bypass, and parallel worker support.

## Features

- Automated Xiaomi MiMo account registration
- reCAPTCHA v2 bypass via audio speech-to-text (free, no paid captcha service)
- Xiaomi text captcha handling
- Temp email via generator.email (auto OTP polling)
- Referral code chaining (siklus mode)
- API key extraction per account
- **Parallel mode** for high-CPU VPS (up to 50 concurrent workers)
- Anti-detection (14 techniques: fingerprint, canvas, WebGL, audio, WebRTC, etc.)
- Proxy rotation (7 free sources + ADB mobile rotation)

## Requirements

- Python 3.10+
- ffmpeg (for captcha audio conversion)
- Google Chrome or Chromium
- Internet connection

## Installation

```bash
git clone https://github.com/sickagents/mimo-farmer.git
cd mimo-farmer
pip install -e .
```

Dependencies installed automatically: `patchright`, `SpeechRecognition`, `pydub`, `InquirerPy`

## How to Run

### Sequential (1 account at a time)

```bash
python -m mimo_farmer create --referral M57JCH --count 5
```

Short version:

```bash
python -m mimo_farmer create -r M57JCH -n 5
```

If `--referral` or `--count` not provided, CLI asks interactively.

### Parallel (multiple workers simultaneously)

```bash
# 30 accounts with 20 parallel workers
python -m mimo_farmer create -r M57JCH -n 30 --workers 20

# Short version
python -m mimo_farmer create -r M57JCH -n 30 -w 20
```

### Commands Reference

```text
mimo create --referral CODE --count N [--workers W]
```

| Option | Short | Default | Description |
|---|---|---|---|
| `--referral` | `-r` | (ask) | Referral code to use |
| `--count` | `-n` | (ask) | Number of accounts to create |
| `--workers` | `-w` | 1 | Parallel workers (1 = sequential, max 50) |

## Recommended Worker Counts

| VPS Spec | Workers | Expected Speed |
|---|---|---|
| 2-4 vCPU, 4GB RAM | 1 | ~1 account/min |
| 8-16 vCPU, 8GB RAM | 3-5 | ~3-5 accounts/min |
| 32-64 vCPU, 16GB RAM | 10-15 | ~10-15 accounts/min |
| 128-160 vCPU, 32GB+ RAM | 20-30 | ~20-30 accounts/min |

**Notes:**
- Each worker uses a separate proxy IP (Xiaomi detects same-IP bulk registration)
- Bottleneck is usually IP rate limit, not CPU
- Recommended: 20-30 workers max even on 160 vCPU
- One worker failure does not stop other workers

## Where Output is Saved

All output goes to `accounts/` directory (auto-created):

```text
accounts/
├── batch_20260702_153000.txt    # Full account details
└── apikey.txt                   # API keys only (one per line)
```

### batch_YYYYMMDD_HHMMSS.txt

Full account data:

```text
[1] | 02/07/2026
Mail: user123@tmpmail.net
Link: https://generator.email/user123@tmpmail.net
Pw: MyP@ssw0rd
Api-Key: sk-abc123xyz
Balance: $2.72

[2] | 02/07/2026
Mail: user456@tmpmail.net
Link: https://generator.email/user456@tmpmail.net
Pw: MyP@ssw0rd
Api-Key: sk-def456xyz
Balance: $2.72

Total Balance: $5.44

Apikey:
sk-abc123xyz
sk-def456xyz
```

### apikey.txt

API keys only, one per line (for easy copy/paste):

```text
sk-abc123xyz
sk-def456xyz
sk-ghi789xyz
```

## Examples

```bash
# Create 5 accounts sequentially
python -m mimo_farmer create -r M57JCH -n 5

# Create 100 accounts with 25 parallel workers (high-CPU VPS)
python -m mimo_farmer create -r M57JCH -n 100 -w 25

# Interactive mode (asks for referral + count)
python -m mimo_farmer create
```

## Anti-Detection

Built-in evasion techniques:
- Browser fingerprint randomization (12 presets)
- Canvas noise injection (deterministic per profile)
- WebGL parameter spoofing (12 GL constants)
- AudioContext fingerprint evasion
- WebRTC IP leak prevention
- Human-like typing with variable delays
- Bezier curve mouse movement
- Client Hints header matching
- Font fingerprint filtering

## Notes

- Use `Ctrl+C` to stop a running batch
- Account files are git-ignored (do not commit credentials)
- Each account gets $2.72 balance (with referral) or $0.72 (without)
- Xiaomi may trigger risk control after many accounts from same IP — change proxy
- For chain referral mode, each new account uses the previous account's referral code
