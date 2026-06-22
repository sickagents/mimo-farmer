"""Default configuration for MiMo CLI."""

import os

# Referral
DEFAULT_REFERRAL_CODE = "M57JCH"
DEFAULT_PASSWORD = "papoi123"

# URLs
SIGNUP_URL = "https://global.account.xiaomi.com/fe/service/register?_locale=en&source=&region=ID&sid=api-platform"
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
