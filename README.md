# mimo-farmer

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.0.0-orange.svg)]()

Automated Xiaomi MiMo account creation CLI tool with referral bonuses.

> **Proven working (2026-06-14)** — full pipeline: signup form, reCAPTCHA v2 audio bypass with manual fallback, OTP via temp email, terms dialog, cookie clearing, referral code, risk control detection, balance verification, API key creation.

## Features

- **reCAPTCHA v2 audio solver** — free Google SpeechRecognition, no API key needed
- **Audio challenge detection** — automatically detects if audio challenge is available; falls back to manual image solving if blocked
- **Risk control detection** — identifies when accounts are flagged by risk control restrictions
- **Temp email OTP** — generator.email integration with auto-polling (banri.xyz domain only)
- **Referral codes** — automatic 6-char code entry via OTP input fields
- **API key creation** — auto-extracts from disabled input fields
- **Balance verification** — confirms $2.72 referral bonus
- **Fast mode** — reduced delays for quicker account creation
- **Parallel mode** — multiple browser instances simultaneously
- **Account management** — list, export credentials

## Requirements

- Python 3.10+
- [ffmpeg](https://ffmpeg.org/) (system dependency for audio conversion)
- [Patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright) (anti-detect Playwright)

## Installation

```bash
# Clone the repo
git clone https://github.com/rapoii/mimo-farmer.git
cd mimo-farmer

# Install
pip install -e .

# Or install dependencies directly
pip install -r requirements.txt

# Install ffmpeg (if not installed)
# Windows: choco install ffmpeg  OR  scoop install ffmpeg
# macOS:   brew install ffmpeg
# Linux:   sudo apt install ffmpeg
```

## Usage

### Create single account

```bash
mimo-farmer create
```

### Create multiple accounts

```bash
mimo-farmer create --count 5
```

### Custom referral code

```bash
mimo-farmer create --referral ABC123
```

### Fast mode (reduced delays)

```bash
mimo-farmer create --fast
```

### Parallel browser instances

```bash
mimo-farmer create --parallel 2
```

### Combine options

```bash
mimo-farmer create --count 10 --parallel 3 --fast --referral MYCODE
```

### List created accounts

```bash
mimo accounts
```

Output:
```
Email                               Balance      Referral   API Key  Created
------------------------------------------------------------------------------------------
abc123@banri.xyz                    $2.72        FHAZMU     OK       2026-06-14 12:00:00
```

### Export credentials

```bash
mimo export                           # JSON format (default)
mimo export --format text             # Text format
mimo export --output my_accounts.json # Custom output path
```

## How It Works

1. **Browser launch** — Patchright (anti-detect Playwright) opens Chromium
2. **Signup form** — fills email, password, agreement checkbox
3. **reCAPTCHA v2** — audio challenge with detection + fallback:
   - Detects if audio challenge is available
   - If available: audio → download from bframe context → ffmpeg → Google free STT
   - If blocked (image-only): pauses for manual solving
4. **OTP** — polls generator.email for 6-digit code (banri.xyz domain)
5. **Terms dialog** — handles ant-modal checkbox + Confirm button
6. **Cookie clearing** — clears all xiaomi.com cookies to prevent stale session issues
7. **Balance page** — navigates to balance (auto-login via Xiaomi session)
8. **Terms dialog** — handles again after re-login
9. **Referral** — enters 6-char code via individual OTP input fields
10. **Risk control** — detects if account is flagged by risk control restrictions
11. **Balance** — verifies $2.72 referral bonus via regex
12. **API key** — creates and extracts from disabled input field
13. **Save** — credentials saved as .txt and .json in `accounts/` (includes risk_control flag)

## Configuration

- **Default referral code**: `FHAZMU`
- **Email domain**: `banri.xyz` (only working domain — other domains are blocked by Xiaomi)
- **Default password**: `papoi123`

## Project Structure

```
mimo-farmer/
├── README.md              # This file
├── LICENSE                # MIT License
├── .gitignore
├── requirements.txt       # Python dependencies
├── setup.py              # Package setup
├── mimo_farmer/
│   ├── __init__.py       # Package init + version
│   ├── __main__.py       # Entry point (python -m mimo_farmer)
│   ├── cli.py            # Argparse CLI (create, accounts, export)
│   ├── creator.py        # Core account creation pipeline
│   ├── captcha.py        # reCAPTCHA v2 audio solver + detection
│   ├── email_handler.py  # generator.email OTP polling
│   └── config.py         # Default settings
└── accounts/             # Generated credentials (gitignored)
```

## Changelog

### v2.0.0 (2026-06-14)
- **Audio challenge detection**: Automatically detects if reCAPTCHA audio challenge is available; falls back to manual image solving when blocked
- **Risk control detection**: Identifies accounts flagged by risk control restrictions
- **Cookie clearing fix**: Clears xiaomi.com cookies before MiMo platform navigation to prevent "own invitation code" errors
- **Terms dialog handling**: Now applied at every page navigation, not just once
- **Default referral**: Changed to `FHAZMU`
- **Email domains**: Restricted to `banri.xyz` only (other domains blocked by Xiaomi)

### v1.0.0 (2026-06-13)
- Initial release

## License

[MIT](LICENSE)
