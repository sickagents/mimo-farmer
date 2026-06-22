# Changelog

All notable changes to mimo-farmer are documented here.

## [2.2.0] — 2026-06-22

### Added
- **Auto-Farm Mode** (`--target-balance`) — create accounts until total bonus reaches target
  - Main account (no referral) → $0.72 signup bonus → extract own referral code
  - Child accounts (with referral) → $2.72 each ($0.72 signup + $2.00 referral)
  - Smart balance tracking: includes parent bonus (+$2.00 per child)
  - Stops automatically when target reached
  - Ctrl+C handler saves progress before exit
- **CDP Mode** (default) — connect to real Chrome via Chrome DevTools Protocol
  - `--cdp-url http://localhost:9222` (default, no flag needed)
  - `--no-cdp` to disable and use Patchright browser instead
  - Real Chrome = `navigator.webdriver = false` naturally (no JS patch)
  - Higher reCAPTCHA trust score vs Patchright
  - Cookie/storage auto-clear per account (incognito-like behavior)
- **ADB IP Rotation** (`--ip-rotate`) — automatic IP rotation via Android USB tethering
  - `--ip-rotate adb` — airplane mode toggle (~15s per rotation)
  - `--ip-rotate data` — mobile data toggle (~8s per rotation, faster)
  - Auto-detects ADB device, shows device info and current IP
  - Falls back to manual VPN prompt if no device connected
- **Anti-Detect Enhancements** (14 layers total)
  - WebRTC IP leak prevention (blocks real IP behind VPN/proxy)
  - Navigator.connection spoofing (4g, downlink, rtt randomization)
  - Battery API spoofing (level, charging status, chargingTime)
  - Screen properties spoofing (colorDepth, pixelDepth)
  - Font fingerprint evasion (platform-specific font filtering)
  - Canvas noise injection (seeded deterministic per profile)
  - AudioContext fingerprint evasion
  - Bezier-curve mouse movement
  - Variable typing speed per character
- **IP Check Display** — shows current IP before starting and after each rotation
- **Random Inter-Account Delay** — 40-60s between accounts (anti-detection)
- **Manual VPN Prompt** — waits for user to press Enter after IP change
- **Parent Bonus Tracking** — each child adds +$2.00 to parent's total

### Changed
- **CDP mode is now default** — Patchright only used with `--no-cdp` flag
- **Main account display** — shows "Referral: (none — main account)" instead of default code
- **Child account optimization** — skips referral code extraction (saves 4-5s per child)
- **Balance calculation** — includes parent bonus ($2.00 per child, not just child's $2.72)
- **CDP tab handling** — create new tab before closing old ones (prevents "Failed to open new tab" crash)
- **Terms dialog** — better detection with auto-confirm on balance page

### Fixed
- **Ctrl+C crash** — saves all created accounts before exit
- **CDP connection errors** — better error handling and recovery
- **Terms popup loop** — improved checkbox detection and click logic
- **Balance verification** — handles $0.72 (main) and $2.72 (child) correctly
- **Referral extraction** — only extracts for main accounts, skips for children

### New Files
- `mimo_farmer/adb_ip_rotate.py` — ADB-based IP rotation via Android USB tethering
- `mimo_farmer/proxy_manager.py` — free proxy fetching from 7 sources

### Documentation
- Updated README.md with CDP mode, auto-farm, ADB features, and CLI examples
- Added configuration guide and anti-detect feature list
- Version bump to 2.2.0

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
