<p align="center">
  <img src="docs/banner_chatgpt.png" alt="mimo-farmer" width="100%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/version-2.1.0-00ff88.svg?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg?style=for-the-badge" alt="Platform">
</p>

<p align="center">
  <b>Automated Xiaomi MiMo account creation with referral bonuses, anti-detect browser, and API key extraction.</b><br>
  <sub>Siklus mode (1 main + 5 children) | reCAPTCHA audio bypass | Manual Xiaomi CAPTCHA | Batch output</sub>
</p>

---

## Features

| Feature | Description |
|---------|-------------|
| 🔄 **Siklus Mode** | Auto-create 1 main + 5 children per cycle — 6 accounts, each child uses own referral |
| 🎙 **reCAPTCHA v2 Audio Solver** | Free Google STT — no paid API needed |
| 🖊 **Manual Xiaomi CAPTCHA** | Text CAPTCHA shown to user for manual solve (more reliable than OCR) |
| 📧 **Auto OTP** | generator.email integration with auto-polling and body code extraction |
| 🔐 **Identity Verification** | Handles Xiaomi's double-OTP verification automatically |
| 📋 **Terms Dialog** | React/Ant Design checkbox fix via trusted click events |
| 🎁 **Referral Codes** | Automatic referral code binding via UI flow |
| 🛡 **Risk Control Detection** | Detects flagged accounts, stops batch, suggests new referral code |
| 💰 **Balance Verification** | Confirms $2.72 referral bonus before proceeding |
| 🔑 **API Key Extraction** | Network intercept + clipboard fallback for full unmasked keys |
| 🕵️ **Anti-Detection** | UA/viewport/timezone spoofing, webdriver override, WebGL spoof, human typing |
| 📦 **Batch Output** | Single `batch_*.txt` file with all `[N] Mail/Pw/Api-Key` — no per-account files |
| ⚡ **Fast Mode** | Reduced delays for quicker creation |
| 🔄 **Parallel Mode** | Multiple browser instances simultaneously |
| ♾️ **Continuous Mode** | Keep creating until risk control detected |
| 🔄 **IP Rotation** | Prompted every 4 accounts in continuous/siklus mode |

## Pipeline

1. **Anti-Detect Setup** — Stealth browser with spoofed UA, viewport, timezone, WebGL, webdriver override
2. **Navigate** — Opens Xiaomi signup page via Patchright
3. **Fill Form** — Random email (generator.email) + random password
4. **CAPTCHA Handling**:
   - **reCAPTCHA v2** → Automated audio solver (Google STT, ~90% accuracy)
   - **Xiaomi text CAPTCHA** → Manual solve (user types code in browser)
5. **OTP** — Polls generator.email inbox for 6-digit verification code
6. **Identity Verification** — Handles Xiaomi's second OTP (Send → wait → enter code)
7. **Terms Dialog** — Trusted checkbox click + Confirm
8. **Cookie Clear** — Prevents "own invitation code" error from stale sessions
9. **Balance Page** — Navigates to MiMo platform (auto-login via Xiaomi session)
10. **Referral** — Enters referral code via UI input fields
11. **Risk Control** — Detects if account is flagged; stops batch if detected
12. **Balance Verify** — Confirms $2.72 via regex extraction
13. **API Key** — Creates key, captures full 51-char key via network intercept (fallback: clipboard)
14. **Save** — Credentials saved to single batch file in `accounts/`

### Siklus Mode Flow

```
Siklus 1:
  ├─ Main account (no referral) → own_referral = XJ6YSS
  ├─ Child 1 (referral: XJ6YSS) → $2.72 balance
  ├─ Child 2 (referral: XJ6YSS) → $2.72 balance
  ├─ Child 3 (referral: XJ6YSS) → $2.72 balance
  ├─ Child 4 (referral: XJ6YSS) → $2.72 balance
  └─ Child 5 (referral: XJ6YSS) → $2.72 balance

Total: 6 accounts, $14.32 combined balance
```

## Installation

```bash
# Clone the repo
git clone https://github.com/rapoii/mimo-farmer.git
cd mimo-farmer

# Install Python dependencies
pip install -e .

# Install ffmpeg (required for audio conversion)
# Windows:
winget install ffmpeg
# macOS:
brew install ffmpeg
# Linux:
sudo apt install ffmpeg

# Install Patchright browser (anti-detect Chromium)
python -m patchright install chromium
```

### Requirements

- Python 3.10+ (3.12 recommended)
- ffmpeg (system dependency)
- Patchright (auto-installed with pip)

## Usage

### Siklus Mode (Recommended)

```bash
# 1 siklus = 1 main + 5 children = 6 accounts
mimo create --siklus

# Multiple siklus
# (interactive prompt asks how many)

# Fast mode
mimo create --siklus --fast
```

### Single Account

```bash
mimo create --referral ABC123 --count 1
```

### Multiple Accounts

```bash
mimo create --referral ABC123 --count 5
mimo create --referral ABC123 --count 5 --fast
```

### Parallel Mode

```bash
mimo create --referral ABC123 --count 10 --parallel 3
```

### Continuous Mode

```bash
# Keep creating until risk control detected
mimo create --referral ABC123 --continuous
mimo create --referral ABC123 -c --fast
```

### Account Management

```bash
# List all created accounts
mimo accounts

# Export credentials to JSON
mimo export

# Export to text format
mimo export --format text

# Custom output path
mimo export --output my_accounts.json
```

### Output Format

Single batch file in `accounts/batch_YYYYMMDD_HHMMSS.txt`:

```
[MAIN]
Mail: 4cniy0m9q8@rexornge.net
Pw: MmaTUm11MU!9
Api-Key: sk-s2nnxo2l...sg58
Referral: -
Own-Referral: XJ6YSS
Balance: $0.72

[1]
Mail: h7vb2k4@rexornge.net
Pw: MmKp3Xnq7!9
Api-Key: sk-t98abcd...xyz12345
Referral: XJ6YSS
Balance: $2.72

[2]
...
```

> **Note:** API keys are only saved to local files — they are never transmitted anywhere.

## Configuration

### Default Settings

| Setting | Default | Description |
|---------|---------|-------------|
| Referral Code | `FHAZMU` | Default referral code |
| Password | `papoi123` | Default password (overridable) |
| Email Domains | 15+ domains | Auto-scraped from generator.email (fallback: `banri.xyz`) |
| Browser | Patchright | Anti-detect Playwright (Chromium) |
| OTP Timeout | 180s | Max wait for verification email |
| CAPTCHA | Manual (Xiaomi), Auto (reCAPTCHA) | Text CAPTCHA → user solves; reCAPTCHA → audio STT |

### Anti-Detection Features

| Feature | Implementation |
|---------|---------------|
| User Agent | Real Chrome UA from pool |
| Viewport | Randomized common resolutions |
| Timezone | Auto-detected from locale |
| Webdriver | `navigator.webdriver = false` |
| WebGL | Spoofed vendor + renderer |
| Chrome Runtime | `window.chrome` + runtime inject |
| Typing Speed | Random delays between keystrokes (150-600ms) |
| Mouse Movement | Human-like randomized paths |

### Working Email Domains

The tool auto-scrapes available domains from generator.email. If a domain gets "not safe" error from Xiaomi, it automatically retries with a new domain/email. This loop continues until a working domain is found.

## Architecture

```
mimo-farmer/
├── mimo_farmer/
│   ├── __init__.py       # Package version
│   ├── __main__.py       # Entry point (python -m mimo_farmer)
│   ├── cli.py            # Argparse CLI — siklus, continuous, parallel, sequential
│   ├── creator.py        # Core pipeline: signup, CAPTCHA, OTP, referral, API key
│   ├── captcha.py        # reCAPTCHA v2 audio solver + Xiaomi text CAPTCHA detection
│   ├── email_handler.py  # generator.email OTP polling
│   ├── config.py         # Default settings + constants
│   └── anti_detect.py    # Stealth browser config (UA, viewport, WebGL, etc.)
├── accounts/             # Batch output files (gitignored)
├── docs/
│   ├── DOCUMENTATION.md  # Full technical documentation
│   ├── banner_chatgpt.png
│   ├── demo.png
│   └── pipeline.png
├── CHANGELOG.md
├── README.md
├── LICENSE               # MIT License
├── requirements.txt
├── setup.py
└── run.bat               # Windows quick-run script
```

### Key Technical Decisions

| Decision | Why |
|----------|-----|
| **Patchright** over Playwright | Anti-detect fingerprint avoids bot detection |
| **Manual Xiaomi CAPTCHA** | ddddocr accuracy ~50%, manual is faster than wasted retries |
| **reCAPTCHA audio** over image | Free Google STT > paid captcha services |
| **Network intercept** for API keys | `input[disabled].value` returns masked key |
| **`input[type="checkbox"]`** click | Trusted event that React recognizes (label click doesn't work) |
| **Cookie clearing** between phases | Prevents "own invitation code" from stale sessions |
| **Unlimited email retry** | Some domains get "not safe", keep retrying until accepted |
| **Batch-only output** | Single file per run, no per-account file clutter |

## Troubleshooting

### Xiaomi text CAPTCHA appears

This is normal. The tool will pause and wait for you to manually type the verification code in the browser window. After solving, the tool automatically continues.

### reCAPTCHA not loading

1. **Password too long** — Xiaomi max 16 chars. Keep password ≤16.
2. **IP flagged** — Wait 30-60 minutes or switch IP (VPN/mobile hotspot).
3. **Patchright detected** — Rare. Try again later.

### "Risk control restrictions" error

Xiaomi flags accounts after multiple signups from same IP.

1. **Create new referral code** — Old codes get flagged
2. **Switch IP** — Mobile hotspot or residential VPN
3. **Wait** — IP cooldown takes 1-2 hours
4. **Use `--siklus`** — Built-in cooldown between cycles

### Email "not safe" error

Xiaomi rejects certain temp email domains. The tool automatically retries with a new email/domain. If it keeps failing:
1. generator.email may be rate-limited — wait 10-15 minutes
2. Switch IP
3. Check if generator.email is accessible

### API key shows masked (asterisks)

The tool automatically falls back to clipboard copy button. If both fail, re-run to get a fresh key.

### Identity verification timeout

Xiaomi requires a second OTP. The tool waits up to 180 seconds. If timeout:
1. Check if generator.email is accessible
2. Email domain may be rate-limited — wait 10-15 minutes
3. Switch IP

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for full version history.

## Legal Disclaimer

This tool is for **educational and research purposes only**. Users are responsible for compliance with Xiaomi's Terms of Service and applicable laws. The authors are not responsible for any misuse.

## License

[MIT](LICENSE)

---

<p align="center">
  <sub>Built with ❤️ and Python</sub>
</p>
