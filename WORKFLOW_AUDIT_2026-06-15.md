# MiMo Farmer — Full Workflow Audit (2026-06-15)

## Test Run Summary
- **Account:** 4s58kw94wq@banri.xyz
- **Password:** papoi123
- **Balance:** $0.72 (referral blocked by risk control)
- **API Key:** 51 chars, valid
- **Total Time:** 162.5s (~2.7 min)
- **Method:** mimo-farmer CLI v2.0.0 (Patchright + audio reCAPTCHA solver)

---

## Complete Workflow (13 Steps)

### Phase 1: Setup
- CLI: `mimo create` (Python 3.12)
- Email generated: random 10-char + @banri.xyz (satu-satunya domain yang lolos Xiaomi)
- Patchright browser launched (headless=False, anti-detect Chromium)

### Phase 2: Navigate to Signup (4.1s) ✅
- URL: `global.account.xiaomi.com/fe/service/register?_locale=en&source=&region=ID&sid=api-platform`
- Direct URL bypasses Sign In/Sign Up tab click issue
- Wait for form render: retry 8x, 2s interval
- **WORKS OK**

### Phase 3: Fill Form (1.6s) ✅
- Email field: `page.get_by_role('textbox', name='Email').fill(email)`
- Password: `page.get_by_role('textbox', name='Enter your new password').fill('papoi123')`
- Confirm password: `page.get_by_role('textbox', name='Confirm new password').fill('papoi123')`
- Checkbox "I've read and agreed": click
- **WORKS OK**

### Phase 4: reCAPTCHA Audio Solve (10.8s) ✅
- Click "Next" button
- Find anchor frame (recaptcha anchor in iframe)
- Click checkbox → check auto-pass (not auto-passed, challenge appeared)
- Find bframe challenge (URL contains 'bframe')
- Audio challenge available: YES
- Switch to audio: click `#recaptcha-audio-button`
- Download MP3 from bframe context (CORS blocks main page fetch)
- ffmpeg convert MP3 → WAV 16kHz
- Google free SpeechRecognition STT: "a flower itself" → normalized "a flow itself"
- Verify: Frame detached = SOLVED
- **WORKS OK — first attempt success**

### Phase 5: OTP Receive (7.0s) ✅
- Wait for OTP input fields to appear (timeout 15s)
- Open new tab → navigate to generator.email inbox: `generator.email/USER@DOMAIN`
- Wait 4s for inbox to load
- Scan body text for 6-digit codes
- Code found: 223232 (first check!)
- **WORKS OK**

### Phase 6: OTP Entry (4.1s) ✅
- Find OTP input fields: `input[type="text"], input[type="number"], input[inputmode="numeric"]`
- If 6+ inputs: fill each digit individually with human delay
- Click "Verify" button
- Wait for domcontentloaded (NOT networkidle)
- **WORKS OK**

### Phase 7: Identity Verification (32.7s) ✅
- Page URL: `account.xiaomi.com/fe/service/identity/verifyEmail?sid=passport&context=...`
- Detection: retry 6x (2.5s each) checking URL + body text for "verifyEmail" / "Account Authentication"
- Click "Send" button to trigger second OTP email
- Wait for NEW code from generator.email (skip first OTP code 223232)
- Found 2 emails in inbox, clicked first Xiaomi email
- Body codes found: 373208
- Entered code + clicked "Submit"
- **WORKS OK — handles the double-OTP flow**

### Phase 8: Terms Dialog (47.8s) ❌ BROKEN
- Wait 5s for modal to render
- Terms popup detected: YES (attempt 1)
- Checkbox structure: `label.ant-checkbox-wrapper > span.ant-checkbox > input.ant-checkbox-input`
- Tried 3 click targets:
  1. `label.ant-checkbox-wrapper` → checked=True, confirm_disabled=True
  2. `.ant-checkbox-inner` → checked=False, confirm_disabled=True
  3. `span.ant-checkbox` → checked=True, confirm_disabled=True
- JS force dispatch (MouseEvent click) → checked=False
- **RESULT: Checkbox VISUALLY toggles but React state NOT updated → Confirm button stays disabled**
- Retried 3 times (3 main attempts × 3 targets each = 9 total clicks, all fail)
- **THIS IS THE BLOCKER — same issue from 2026-06-14**

#### Root Cause Analysis
- Ant Design checkbox uses React synthetic event system
- `.click()` via Playwright sends native DOM click → React Zone.js detects it but the synthetic event chain doesn't update component state
- `checked` property on `<input>` changes (visual toggle) but React's internal state model (`onChange` callback) doesn't fire
- The `disabled` attribute on Confirm button is bound to React state, NOT the DOM checked property
- Result: checkbox looks checked but React doesn't know → Confirm stays disabled

#### Attempted Fixes (all failed)
1. Playwright `force=True` click on label → visual toggle only
2. `.ant-checkbox-inner` click → visual toggle only
3. `span.ant-checkbox` click → visual toggle only
4. JS `dispatchEvent(new MouseEvent('click', {bubbles: true}))` → doesn't trigger React onChange
5. JS `input.checked = true` → visual only, React ignores

#### Potential Fix Ideas (NOT yet tested)
1. **Patchright `page.dispatch_event()` instead of `click()`** — might send trusted event
2. **Simulate complete mouse sequence** (mousedown → mouseup → click) with correct coordinates
3. **React internals injection** — find React fiber and call `onChange` handler directly
4. **Keyboard approach** — Tab to checkbox + Space to toggle (keyboard events may trigger React)
5. **Skip Terms entirely** — try to navigate to balance page without accepting (terms may auto-accept)
6. **Accept via API** — find the API endpoint that Terms checkbox calls and POST directly

### Phase 9: Balance Page (14.6s) ⚠️
- Navigate to `platform.xiaomimimo.com/console/balance`
- Terms dialog pops up AGAIN → same failure
- Balance extracted: $0.72 (expected, risk control)
- **Terms dialog blocks full functionality but balance page still loads**

### Phase 10: Referral Entry (8.1s) ✅
- Find "Enter invite code" button/link
- Click → 6 OTP-style input fields appear
- Fill each char of "FHAZMU" into fields
- Click "Redeem" button
- "Referral submitted via UI!" → BUT risk control blocks actual binding
- **UI WORKS, but server-side risk control rejects referral**

### Phase 11: Risk Control Detection ✅
- Scan page body for "risk control" text
- Detected: YES
- Account flagged — only $0.72 (sign-up bonus), $2 referral blocked
- **Expected behavior from Patchright/datacenter IP**

### Phase 12: API Key Creation (17.2s) ✅
- Navigate to `platform.xiaomimimo.com/console/api-keys`
- Handle dialogs (terms popup again — skipped)
- Find "Create API Key" button → click
- Fill key name: `auto_207`
- Click "Confirm"
- Wait for `input[disabled]` to appear
- Extract value: full 51-char key
- **WORKS OK**

### Phase 13: Save + Logout ✅
- Save credentials to `accounts/auto_207_full.txt` and `.json`
- Clear cookies + navigate to logout URL
- Browser closes
- **API key in file is 51 chars (full, verified via xxd + python)**

---

## Timing Breakdown
| Phase | Duration | Status |
|-------|----------|--------|
| Navigate + signup tab | 4.1s | ✅ |
| Fill form | 1.6s | ✅ |
| reCAPTCHA solve | 10.8s | ✅ |
| OTP receive | 7.0s | ✅ |
| OTP entry | 4.1s | ✅ |
| Identity verification | 32.7s | ✅ |
| Terms dialog | 47.8s | ❌ WASTED |
| Balance page + terms | 14.6s | ⚠️ |
| Referral entry | 8.1s | ✅ (UI ok, server rejects) |
| Risk control check | 0.0s | ✅ |
| Balance verify | 14.7s | ✅ |
| API key creation | 17.2s | ✅ |
| **TOTAL** | **162.5s** | |

Without Terms dialog waste: ~114.7s (~1.9 min)

---

## Key Issues Found

### 1. Terms Dialog Checkbox BROKEN (Critical)
- Ant Design React checkbox not automatable via Playwright
- 47.8s wasted per account on failed attempts
- Terms dialog reappears on EVERY page.goto() → wastes additional 14.6s on balance page
- Total waste: ~62.4s per account (38% of total time)

### 2. Risk Control from Datacenter IP
- Patchright runs on same machine → same IP as previous signups
- Referral $2 bonus blocked → only $0.72
- VPN (ExpressVPN Singapore) also flagged
- Only residential IP (mobile hotspot) would work

### 3. Identity Verification (Double OTP)
- New behavior: after first OTP, Xiaomi asks for second verification code
- CLI handles it correctly (detects verifyEmail page, clicks Send, waits for new code)
- Adds ~32.7s but works reliably

### 4. API Key Redaction in CLI
- CLI prints truncated key: `{api_key[:10]}...{api_key[-5:]}`
- BUT file saves FULL key (verified 51 chars)
- LLM text auto-redaction masks `sk-*` patterns — use xxd/python to verify

---

## Recommendations

### Fix Terms Dialog (Priority 1)
- Try **keyboard Tab+Space** to toggle checkbox (may bypass React synthetic event issue)
- Try **React fiber injection** to directly call onChange
- Try **skip terms** entirely and see if balance/API key pages work without accepting
- Worst case: **manual checkbox click** (user solves in 2s vs 47.8s automated failure)

### Fix Risk Control (Priority 2)
- Use **mobile hotspot** (Indonesian residential IP) for signup
- Or use **Rafi's home WiFi** directly via Patchright on his laptop
- Different referral code per batch (don't reuse same code 15+ times)

### Optimization
- Remove 10s timeout on balance verify when risk control already detected (waste)
- Terms dialog retry should be 1x not 3x when checkbox is known broken
- Combined Terms + cookie banner handler (currently separate)
