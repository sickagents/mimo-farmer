# mimo-farmer Documentation

## Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [Anti-Detection](#anti-detection)
- [CAPTCHA Handling](#captcha-handling)
- [Siklus Mode](#siklus-mode)
- [Email Handling](#email-handling)
- [Terms Dialog](#terms-dialog)
- [API Key Extraction](#api-key-extraction)
- [Risk Control](#risk-control)
- [Configuration](#configuration)
- [CLI Reference](#cli-reference)
- [API Reference](#api-reference)
- [FAQ](#faq)

---

## Overview

mimo-farmer automates the Xiaomi MiMo account creation pipeline. Each account receives:
- **$0.72** sign-up bonus (automatic)
- **$2.00** referral bonus (if referral code works)
- **API key** for MiMo's AI platform

The tool handles browser anti-detection, CAPTCHA solving (automated reCAPTCHA + manual Xiaomi text), email verification, and credential extraction. Output is a single batch file per run — no per-account file clutter.

---

## How It Works

### Pipeline Phases

| Phase | Duration | Description |
|-------|----------|-------------|
| 1. Anti-Detect Setup | <1s | Stealth browser: UA, viewport, timezone, WebGL, webdriver |
| 2. Navigate | 4s | Open Xiaomi signup URL via Patchright |
| 3. Fill Form | 1.5s | Enter random email + password |
| 4. CAPTCHA | varies | reCAPTCHA audio (~17s) OR manual Xiaomi text CAPTCHA |
| 5. OTP Wait | ~11s | Poll generator.email for code |
| 6. OTP Entry | 4s | Type 6-digit code |
| 7. Identity Verify | ~81s | Second OTP (Xiaomi security) |
| 8. Terms Dialog | 6s | Checkbox + Confirm (React fix) |
| 9. Cookie Clear | <1s | Prevent stale session |
| 10. Balance Page | 7s | Navigate to MiMo platform |
| 11. Referral | 9s | Enter referral code |
| 12. Risk Check | <1s | Detect if flagged |
| 13. Balance Verify | 2s | Confirm $2.72 |
| 14. API Key | 17s | Create + extract full key |
| 15. Save | <1s | Write to batch file |

**Total: ~160-200 seconds per account** (varies with CAPTCHA type and OTP speed)

### Browser: Patchright

[Patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright) is a fork of Playwright with anti-detection patches. Combined with `anti_detect.py`, it:
- Removes `navigator.webdriver` flag
- Patches Chrome DevTools Protocol detection
- Spoofs WebGL vendor/renderer
- Injects `window.chrome` runtime
- Randomizes viewport, timezone, locale
- Simulates human typing speed (150-600ms per keystroke)

---

## Anti-Detection

### anti_detect.py

The stealth module applies these patches before every browser launch:

| Technique | Implementation |
|-----------|---------------|
| **User Agent** | Rotated from pool of real Chrome UAs |
| **Viewport** | Randomized from common resolutions (1366x768, 1920x1080, etc.) |
| **Timezone** | Auto-detected from locale setting |
| **Webdriver** | `Object.defineProperty(navigator, 'webdriver', {get: () => false})` |
| **WebGL** | Spoofed `UNMASKED_VENDOR_WEBGL` and `UNMASKED_RENDERER_WEBGL` |
| **Chrome Runtime** | `window.chrome = {runtime: {...}}` injected |
| **Typing Speed** | Random 150-600ms delays between keystrokes |
| **Fast Mode** | Reduced to 50-200ms delays |

### Why It Matters

Xiaomi's anti-bot system checks for:
- `navigator.webdriver === true` (Playwright/Selenium default)
- Missing `window.chrome` object
- WebGL fingerprint matching known headless signatures
- Inhuman typing speed (instant field fills)

---

## CAPTCHA Handling

mimo-farmer handles **two types** of CAPTCHA:

### 1. reCAPTCHA v2 — Automated Audio Solver

Used when reCAPTCHA iframe is detected (standard Google reCAPTCHA).

**Flow:**
1. Find `recaptcha/anchor` frame (up to 15s retry)
2. Click `#recaptcha-anchor` checkbox
3. If `aria-checked=true` → auto-pass, no challenge needed
4. Otherwise, find `enterprise/bframe` frame
5. Click `#recaptcha-audio-button` to switch to audio challenge
6. Download MP3 from bframe context (NOT main page — CORS blocks)
7. Convert MP3 → WAV via ffmpeg (16kHz mono)
8. Transcribe via `speech_recognition.recognize_google()` (free web API)
9. Normalize number words ("twenty one" → "21")
10. Type answer + click Verify (force=True + JS fallback)

**Accuracy:** ~90% on first attempt, retries up to 5 times.

### 2. Xiaomi Text CAPTCHA — Manual Solve

Used when Xiaomi's own text CAPTCHA popup appears (distorted text image).

**Why manual?**
- ddddocr (OCR library) accuracy: ~50% — wastes more time retrying than manual solve
- Manual solve: 100% accuracy, ~10-15 seconds of user time

**Flow:**
1. Tool detects "Enter verification code" popup with captcha image
2. Prints message to terminal: **"Solve captcha manually in browser"**
3. Waits for user to type code in browser
4. Detects when popup disappears (solved)
5. Continues pipeline automatically

**Note:** If running via agent (Hermes), the browser opens in agent's session — not visible on user's desktop. Run in CMD/terminal directly for manual CAPTCHA.

### Detection Logic

```python
# In creator.py, after form submission:
1. Check for reCAPTCHA anchor frame → solve_recaptcha()
2. Check for Xiaomi text CAPTCHA popup → wait for manual solve
3. Neither → continue (no CAPTCHA needed)
```

---

## Siklus Mode

### What Is It?

Siklus mode creates accounts in **cycles of 6**:
1. **Main account** — created without referral, generates own referral code
2. **5 children** — each uses main account's referral code, gets $2.72 bonus

### Why Siklus?

- Maximizes referral bonus: $0.72 + (5 × $2.72) = **$14.32 per siklus**
- Self-sustaining: no need for external referral codes
- Built-in cooldown between cycles

### Usage

```bash
# Single siklus (6 accounts)
mimo create --siklus

# Multiple siklus (interactive prompt)
mimo create --siklus
# → "Mau berapa siklus? (1 siklus = 1 akun utama + 5 anak): 3"
# → Creates 18 accounts total

# Fast mode
mimo create --siklus --fast
```

### Flow Per Siklus

```
1. Create main account (no referral)
2. Extract own_referral code from "Refer & earn" dialog
3. Cooldown 30-60s (random)
4. Create child 1 (referral: own_referral)
5. Create child 2 (referral: own_referral)
6. Create child 3 (referral: own_referral)
7. Create child 4 (referral: own_referral)
8. Create child 5 (referral: own_referral)
9. IP rotation prompt (every siklus)
10. Cooldown between siklus cycles
```

### Referral Extraction

After main account is created, the tool:
1. Clicks "Refer & earn" button on MiMo dashboard
2. Extracts 6-character referral code from the dialog
3. Closes dialog
4. Uses this code for all 5 children

### Error Handling

- **Main account fails** → skip entire siklus
- **Child fails** → skip that child, continue with remaining
- **Risk control** → stop all siklus
- **IP rotation** → prompted after each siklus (user can switch VPN/hotspot)

---

## Email Handling

### generator.email

The tool uses [generator.email](https://generator.email) for temporary email addresses:

1. **Domain Scraping** — Auto-discovers 15+ available domains from generator.email homepage
2. **Random Selection** — Picks random domain each attempt
3. **"Not Safe" Detection** — If Xiaomi rejects the email domain, automatically retries with new domain/email
4. **Unlimited Retry** — Keeps retrying until a working domain is found
5. **OTP Polling** — Refreshes inbox every 1.5 seconds (up to 180s timeout)
6. **Body Extraction** — Clicks email rows to read body content
7. **Code Parsing** — Regex extracts 6-digit code from email body

### Email Retry Logic

```python
while True:  # unlimited retries
    email = generate_random_email()
    # fill form, submit
    if "not safe" in page_content:
        # domain rejected by Xiaomi
        continue  # try new email
    # proceed with OTP
    break
```

### Rate Limiting

Xiaomi rate-limits temp email domains after several signups. If OTP doesn't arrive:
- The tool automatically retries with new email/domain
- If all domains fail, wait 10-15 minutes or switch IP

---

## Terms Dialog

### The Problem

Xiaomi's Terms dialog uses React/Ant Design with a checkbox that:
- Ignores `force=True` Playwright clicks (untrusted events)
- Ignores JS `.checked = true` (React state not updated)
- Only responds to native `input[type="checkbox"]` click (trusted event)

### The Solution

```python
# WRONG — label click (untrusted, React ignores)
await page.locator('label.ant-checkbox-wrapper').click(force=True)

# RIGHT — input click (trusted, React recognizes)
await page.locator('input[type="checkbox"]').click()
```

The tool clicks the actual `<input>` element, which sends a trusted browser event that React's synthetic event system recognizes.

---

## API Key Extraction

### The Problem

Xiaomi shows API keys in two places:
1. **Network response** — Returns masked key with `****` asterisks
2. **`input[disabled].value`** — Returns masked key with `...` dots

### The Solution

3-tier fallback:

1. **Network Intercept** — Captures POST response from `/api/v1/api-keys/create`
   - Checks for `*` characters in captured key
   - If masked, falls through to next method

2. **Clipboard Copy** — Clicks the Copy button in the success dialog
   - `navigator.clipboard.readText()` returns full unmasked key
   - Validates: starts with `sk-`, length ≥ 40, no asterisks

3. **DOM Scan** — Searches all visible elements for full `sk-` key
   - Checks `code`, `pre`, `span`, `div`, `p`, `td` elements
   - Filters: starts with `sk-`, length ≥ 40, no `*` or `...`

---

## Risk Control

### What Is It?

Xiaomi flags accounts after multiple signups from the same IP. When flagged:
- Referral code binding silently fails
- Balance stays at $0.72 (no $2 referral bonus)
- Error message: "Your account has risk control restrictions"

### Detection

The tool checks for "risk control" text on the balance page after entering the referral code.

### Response

When risk control is detected:
1. Account is still created (with $0.72 balance)
2. Batch stops immediately
3. Message: "Create a NEW referral code and try again"
4. In siklus mode: stops remaining children and siklus cycles

### Prevention

- **Use `--siklus`** — Built-in cooldown between accounts and cycles
- **Rotate referral codes** — Don't use same code for 10+ accounts
- **Switch IPs** — Mobile hotspot or residential VPN (prompted every siklus)
- **Space out signups** — Random 30-60s cooldown between accounts

---

## Configuration

### config.py

```python
DEFAULT_REFERRAL_CODE = "FHAZMU"
DEFAULT_PASSWORD = "papoi123"
SIGNUP_URL = "https://global.account.xiaomi.com/fe/service/register?..."
BALANCE_URL = "https://platform.xiaomimimo.com/console/balance"
API_KEYS_URL = "https://platform.xiaomimimo.com/console/api-keys"
OTP_TIMEOUT_SECONDS = 180
OTP_POLL_INTERVAL_SECONDS = 1.5
CAPTCHA_MAX_RETRIES = 5
FAST_MODE_MULTIPLIER = 0.4
HUMAN_DELAY_MIN_MS = 150
HUMAN_DELAY_MAX_MS = 600
EMAIL_DOMAINS = ["banri.xyz"]  # fallback if dynamic scraping fails
```

### Environment Variables

None required. All configuration is in `config.py` or via CLI arguments.

---

## CLI Reference

### `mimo create`

Create MiMo accounts.

```
Usage: mimo create [OPTIONS]

Options:
  -r, --referral CODE   Referral code (prompted if not provided)
  -n, --count N         Number of accounts (prompted if not provided)
  -f, --fast            Fast mode — reduced delays
  -p, --parallel N      Parallel browser instances
  -c, --continuous      Keep creating until risk control
  -s, --siklus          Cycle mode (1 main + 5 children per cycle)
```

#### Mode Combinations

| Flags | Behavior |
|-------|----------|
| (none) | Interactive: prompts for referral + count |
| `--referral X --count N` | Sequential: N accounts with referral X |
| `--referral X --count N --fast` | Sequential fast mode |
| `--referral X --count N --parallel 3` | Parallel: 3 browsers at once |
| `--referral X --continuous` | Continuous until risk control |
| `--siklus` | Cycle mode (ignores --count, --referral, --parallel) |
| `--siklus --fast` | Cycle mode fast |

#### Invalid Combinations (will error)

- `--siklus` + `--continuous`
- `--siklus` + `--count`
- `--siklus` + `--parallel`
- `--continuous` + `--parallel`
- `--continuous` + `--count`

### `mimo accounts`

List all created accounts from `accounts/` directory.

### `mimo export`

Export credentials to file.

```
Usage: mimo export [OPTIONS]

Options:
  -o, --output PATH     Output file path
  --format FORMAT       json (default) or text
```

---

## API Reference

### `create_account()`

```python
async def create_account(
    referral_code: str = DEFAULT_REFERRAL_CODE,
    fast: bool = False,
    account_num: int = 0,
) -> dict | None
```

Returns:
```python
{
    "email": "abc123@rexornge.net",
    "password": "MmRai9ILb2!9",
    "balance": "$2.72",
    "referral": "985C86",
    "api_key": "sk-s47bzoi...a2avasrip8",  # 51 chars, full
    "risk_control": False,
    "own_referral": "XJ6YSS",
    "created": "2026-06-16 03:00:24"
}
```

Returns `None` if creation fails.

### `solve_recaptcha()`

```python
async def solve_recaptcha(page, max_retries: int = 5) -> bool
```

Returns `True` if CAPTCHA solved, `False` otherwise.

### `detect_risk_control()`

```python
async def detect_risk_control(page) -> bool
```

Returns `True` if "risk control" text found on page.

---

## FAQ

**Q: Why manual Xiaomi CAPTCHA instead of automated OCR?**
A: ddddocr accuracy is ~50% — for every 2 attempts, 1 fails and wastes 15-20s. Manual solve takes 10-15s with 100% accuracy. Net time saved.

**Q: Why not use paid CAPTCHA services (2captcha, capsolver)?**
A: reCAPTCHA is already solved for free via audio STT. Xiaomi text CAPTCHA is rare and fast to solve manually. Paid services add cost with minimal benefit.

**Q: Can I run this headless (no visible browser)?**
A: Not recommended — Xiaomi text CAPTCHA requires manual input. If headless is needed, you'd need to re-enable ddddocr and accept lower success rate.

**Q: Why does the browser open in a different session?**
A: Agent tools (like Hermes) run in a separate terminal session. The browser is not visible on your desktop. For manual CAPTCHA, run directly in CMD/terminal.

**Q: How many accounts can I create before risk control?**
A: Varies by IP, referral code, and timing. Typically 4-8 accounts per IP before flagging. Use `--siklus` with IP rotation for best results.

**Q: What email domains work?**
A: The tool auto-scrapes 15+ domains from generator.email. Domain availability changes. If a domain gets "not safe" error, the tool automatically retries with another.

**Q: Why batch-only output (no per-account files)?**
A: Per-account files (`auto_N_full.txt`, `auto_N.json`) cluttered the accounts directory. Single batch file contains everything needed. Simplified in v2.1.0.

**Q: What is `own_referral` in the output?**
A: The referral code generated by this account (from "Refer & earn"). Used in siklus mode to link child accounts.
