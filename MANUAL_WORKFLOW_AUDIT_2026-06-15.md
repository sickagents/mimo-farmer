# MiMo Manual Workflow Audit (2026-06-15)

## Account Created
- Email: 6069llin3b@banri.xyz
- Password: papoi123
- Balance: $0.72 (risk control — cloud IP)
- Referral: FHAZMU (submitted, server rejected)
- API Key: 51 chars (saved at accounts/manual_788_key.txt)
- User ID: 6877511788

## Workflow Steps

| # | Step | Status | Deviation? |
|---|------|--------|------------|
| 1 | Navigate signup URL | ✅ | — |
| 2 | Fill form (email, pw, checkbox) | ✅ | selector: input[name='email'], bukan placeholder |
| 3 | Click Next | ✅ | — |
| 4 | reCAPTCHA | ⚠️ Manual | Audio challenge muncul tapi STT salah ("ultimately find"). Switch ke image challenge → Rafi solve manual |
| 5 | OTP page | ✅ | — |
| 6 | Get OTP from generator.email | ✅ | Code: 403438, inbox langsung show (auto-expanded) |
| 7 | Enter OTP + Submit | ✅ | — |
| 8 | Identity verification | ✅ | Click "Send" → get second code 049296 from email |
| 9 | Enter identity code + Submit | ✅ | Redirect ke account.xiaomi.com |
| 10 | Navigate MiMo balance | ✅ | — |
| 11 | **Terms dialog** | ✅ **SOLVED!** | `input[type='checkbox'].click()` WORKS! Confirm enabled! |
| 12 | Enter referral FHAZMU | ✅ | 6 input fields, Redeem enabled |
| 13 | Check balance | ✅ $0.72 | Risk control (expected dari cloud IP) |
| 14 | Create API key | ✅ | Key name: manual_788 |
| 15 | Save credentials | ✅ | 51 chars via download.saveAs |

## CRITICAL FINDING: Terms Dialog SOLVED

**Root cause of CLI failure:** Patchright uses `label.ant-checkbox-wrapper.click(force=True)` — ini visual toggle only, React state gak update.

**Working solution:** MCP Playwright `input[type='checkbox'].click()` — sends trusted click event yang React recognize, checkbox ACTUALLY checked, Confirm button enabled.

**Fix for CLI:** Replace Patchright checkbox click with native `input[type='checkbox'].click()`:
```python
# BROKEN (Patchright):
await page.locator('label.ant-checkbox-wrapper').click(force=True)
# or
await page.locator('.ant-checkbox-inner').click(force=True)

# WORKING (native Playwright):
await page.locator('input[type="checkbox"]').click()
```

The difference: Patchright's anti-detect modifications interfere with click event trust. Native Playwright sends standard trusted events that React's event system recognizes.

## Other Deviations from CLI Workflow

1. **reCAPTCHA audio unreliable** — STT returned "ultimately find" (wrong). Image challenge needed manual solve. CLI audio solver worked in Patchright but not MCP Playwright (different browser context).

2. **Identity verification detected** — New step: Xiaomi now asks for SECOND verification code after initial OTP. CLI handles this. Manual workflow handles it too.

3. **generator.email inbox** — New layout: emails auto-expand when clicked. Code visible in body without needing to click rows separately.

## Recommendations for CLI Fix

1. **Terms dialog:** Change checkbox selector from `label.ant-checkbox-wrapper` to `input[type="checkbox"]` in `handle_terms_dialog()`
2. **reCAPTCHA:** Keep audio solver as primary, manual fallback when STT fails. Consider using MCP Playwright as backend instead of Patchright.
3. **Identity verification:** Already handled in CLI — no change needed.

## Timing Estimate
Manual workflow took ~25 min (includes debugging reCAPTCHA + waiting for Rafi).
Without reCAPTCHA issues: ~8-10 min.
CLI with Terms fix: ~2-3 min (no manual intervention).
