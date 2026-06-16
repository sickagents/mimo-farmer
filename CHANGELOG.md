# Changelog

All notable changes to mimo-farmer are documented here.

## [2.1.0] — 2026-06-16

### Added
- **Siklus Mode** (`--siklus`) — automated cycle: 1 main account + 5 children per siklus
  - Main account generates own referral code via "Refer & earn" dialog
  - Each child uses main's referral for $2.72 bonus
  - Interactive prompt for number of siklus cycles
  - Built-in cooldown (30-60s random) between accounts and cycles
  - IP rotation prompt after each siklus
- **Anti-Detection Module** (`anti_detect.py`) — stealth browser configuration
  - User Agent rotation from real Chrome UA pool
  - Viewport randomization (common resolutions)
  - Timezone/locale auto-detection
  - `navigator.webdriver = false` override
  - WebGL vendor/renderer spoofing
  - `window.chrome` runtime injection
  - Human-like typing speed simulation (150-600ms per keystroke)
- **"Not Safe" Email Detection** — detects when Xiaomi rejects email domain
  - Automatic retry with new domain/email
  - Unlimited retries until working domain found
- **Manual Xiaomi Text CAPTCHA** — replaces unreliable ddddocr OCR (~50% accuracy)
  - User solves text CAPTCHA manually in browser
  - Tool auto-detects when popup disappears and continues
- **IP Rotation Prompt** — every 4 accounts in continuous mode, every siklus in siklus mode
- **Continuous Mode** (`--continuous`) — keep creating until risk control detected
- **Dynamic Email Domains** — auto-scrapes 15+ domains from generator.email

### Changed
- **Batch-only output** — removed per-account files (`auto_N_full.txt`, `auto_N.json`)
  - Single `batch_YYYYMMDD_HHMMSS.txt` per run
  - Cleaner accounts directory
- **Email retry** — from max 3 retries to unlimited (while True)
- **CAPTCHA handling** — simplified state tracking, no re-solve after page progression
- **Default referral** — `DMRFJP` (was `FHAZMU`)
- **Password default** — `papoi123` (was random per account)

### Fixed
- **Batch file missing main account** — `_save_combined()` filter was `balance == '$2.72'`, excluded main ($0.72). Changed to accept any balance.
- **reCAPTCHA loop re-solve** — track solved CAPTCHA types, break if already progressed past signup
- **Frame detachment** — validate page state after submit, not just popup close
- **reCAPTCHA verify button** — force=True click + JS fallback

### Removed
- **ddddocr auto-solve** for Xiaomi text CAPTCHA (too inaccurate, ~50%)
- **Per-account files** — `auto_N_full.txt` and `auto_N.json` eliminated
- **Debug image saving** — no longer needed since ddddocr removed
- **generator.email "not safe" detection** — removed from email_handler side (kept on Xiaomi side only)

## [2.0.1] — 2026-06-15

### Fixed
- **Random passwords** — each account gets unique 12-char password (anti-bot detection)
- **API key fix** — detects masked keys from API response, falls back to clipboard + DOM scan
- **Risk control batch stop** — stops remaining accounts when risk control detected
- **Password length fix** — 12 chars (was 18, exceeded Xiaomi's 16-char max)
- **Verify button fix** — force=True click + JS fallback for reCAPTCHA verify
- **CLI args fix** — `--referral` and `--count` properly override interactive prompts
- **Faster terms dialog** — reduced sleep times, 6s vs 70-99s previously
- **Debug output** — frame URL logging when reCAPTCHA not found

## [2.0.0] — 2026-06-14

### Added
- Audio challenge detection with manual fallback
- Risk control detection
- Cookie clearing fix
- Terms dialog handling at every page navigation
- Network intercept for API key capture
- Combined batch output format

## [1.0.0] — 2026-06-13

### Added
- Initial release
- Basic account creation pipeline
- reCAPTCHA v2 image challenge
- Manual OTP entry
