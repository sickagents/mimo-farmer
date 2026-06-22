"""Default configuration for MiMo CLI."""

import os

# Referral
DEFAULT_REFERRAL_CODE = "M57JCH"
DEFAULT_PASSWORD = "papoi123"

# URLs
SIGNUP_URL = "https://global.account.xiaomi.com/fe/service/register?_locale=en&source=&region=ID&sid=api-platform"
PLATFORM_URL = "https://platform.xiaomimimo.com"
BALANCE_URL = "https://platform.xiaomimimo.com/console/balance"
API_KEYS_URL = "https://platform.xiaomimimo.com/console/api-keys"
LOGOUT_URL = "https://account.xiaomi.com/pass/logout"

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCOUNTS_DIR = os.path.join(PROJECT_ROOT, "accounts")
AUDIO_DIR = os.path.join(PROJECT_ROOT, ".audio_cache")

# Timing
HUMAN_DELAY_MIN_MS = 150
HUMAN_DELAY_MAX_MS = 600

# CAPTCHA modes: "auto" (reCAPTCHA audio STT, Xiaomi manual) or "manual" (all manual)
CAPTCHA_MODE_DEFAULT = "auto"

# Auto-farm
TARGET_BALANCE_DEFAULT = 10.0

# OTP
OTP_TIMEOUT_SECONDS = 180
OTP_POLL_INTERVAL_SECONDS = 1.5

# reCAPTCHA
CAPTCHA_MAX_RETRIES = 5

# Email domains for generator.email
# Fallback if dynamic scraping fails
EMAIL_DOMAINS = ["ferd.live", "gudri.com", "cihuy.net"]

# Domains flagged by Xiaomi — always excluded even if scraped
DOMAINS_BLOCKLIST = ["banri.xyz", "embege.xyz"]


def add_domain_to_blocklist(domain: str, reason: str = "") -> bool:
    """Add a domain to blocklist and persist it to this config file."""
    domain = (domain or "").strip().lower()
    if not domain or domain in DOMAINS_BLOCKLIST:
        return False

    DOMAINS_BLOCKLIST.append(domain)
    DOMAINS_BLOCKLIST.sort()

    try:
        from pathlib import Path
        path = Path(__file__)
        text = path.read_text(encoding="utf-8")
        old = text.split("DOMAINS_BLOCKLIST = ", 1)[1].split("\n", 1)[0]
        new = repr(DOMAINS_BLOCKLIST)
        path.write_text(text.replace(f"DOMAINS_BLOCKLIST = {old}", f"DOMAINS_BLOCKLIST = {new}", 1), encoding="utf-8")
    except Exception:
        pass

    note = f" ({reason})" if reason else ""
    print(f"  [!] Domain '{domain}' added to persistent blocklist{note}")
    return True
