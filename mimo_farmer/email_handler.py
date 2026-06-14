"""Email generator and OTP polling via generator.email."""

import asyncio
import random
import re
import string
import time

from mimo_farmer.config import EMAIL_DOMAINS, OTP_TIMEOUT_SECONDS, OTP_POLL_INTERVAL_SECONDS


def random_email() -> tuple[str, str, str]:
    """Generate random email address for generator.email."""
    user = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    domain = random.choice(EMAIL_DOMAINS)
    return f"{user}@{domain}", user, domain


async def _extract_codes_from_page(email_page) -> list[str]:
    """Extract all 6-digit codes visible on the page."""
    codes = set()
    try:
        body = await email_page.evaluate("document.body?.innerText || ''")
        found = re.findall(r'\b(\d{6})\b', body)
        codes.update(found)
    except Exception:
        pass
    return list(codes)


async def _click_email_and_get_code(email_page, skip_codes: set, inbox_url: str) -> str | None:
    """Click on ALL Xiaomi email rows to read body, return new code if found.

    generator.email inbox shows subjects but NOT email bodies.
    Must click each row to open and read the 6-digit code from body.
    Checks ALL Xiaomi emails (signup OTP + identity verification) — returns first NEW code.
    """
    try:
        rows = email_page.locator('table tr')
        count = await rows.count()

        for i in range(count):
            row = rows.nth(i)
            try:
                row_text = await row.inner_text()
            except Exception:
                continue

            # Skip header row
            if 'From' in row_text and 'Subject' in row_text:
                continue

            # Only click rows from Xiaomi
            if 'xiaomi' not in row_text.lower():
                continue

            print(f"  [otp] Clicking email: {row_text.strip()[:60]}...")
            try:
                await row.click(timeout=3000)
                await asyncio.sleep(2)

                # Read body content for codes
                body_codes = await _extract_codes_from_page(email_page)
                new_codes = [c for c in body_codes if not c.startswith('20') and c not in skip_codes]
                if new_codes:
                    return new_codes[0]

                print(f"  [otp] No new codes in this email, going back...")

                # Go back to inbox
                back_btn = email_page.locator('a:has-text("Back"), a:has-text("Inbox"), a:has-text("←")')
                if await back_btn.count() > 0:
                    await back_btn.first.click(timeout=3000)
                else:
                    await email_page.goto(inbox_url, wait_until='domcontentloaded')
                await asyncio.sleep(2)
            except Exception as e:
                print(f"  [otp] Click email error: {e}")
                try:
                    await email_page.goto(inbox_url, wait_until='domcontentloaded')
                    await asyncio.sleep(2)
                except Exception:
                    pass

    except Exception as e:
        print(f"  [otp] Email click scan error: {e}")

    return None


async def wait_for_otp(page, user: str, domain: str, timeout: int = OTP_TIMEOUT_SECONDS, skip_codes: list = None) -> str | None:
    """Poll generator.email inbox for 6-digit OTP code.

    Strategy:
    1. Scan inbox body text for 6-digit codes
    2. If all found codes are in skip_codes, click email rows to read body
    3. Repeat until new code found or timeout
    """
    print(f"  [otp] Waiting for email to {user}@{domain} (timeout {timeout}s)...")

    email_page = await page.context.new_page()
    inbox_url = f"https://generator.email/{user}@{domain}"
    await email_page.goto(inbox_url, wait_until='domcontentloaded')
    await asyncio.sleep(4)

    start = time.time()
    code = None
    check_count = 0
    if skip_codes is None:
        skip_codes = set()
    else:
        skip_codes = set(skip_codes)

    while time.time() - start < timeout:
        check_count += 1
        try:
            # Step 1: Scan inbox body for codes (might find codes in previews)
            codes = await _extract_codes_from_page(email_page)

            if codes:
                otp_codes = [c for c in codes if not c.startswith('20') and c not in skip_codes]
                if otp_codes:
                    code = otp_codes[0]
                    print(f"  [otp] Found code: {code} (check #{check_count})")
                    break

            # Step 2: Click email rows to read bodies
            # Trigger when: (a) all codes in skip list, OR (b) no codes visible on page
            should_click = False
            if codes and skip_codes and check_count >= 2:
                print(f"  [otp] All codes in skip list, clicking email rows...")
                should_click = True
            elif not codes and check_count >= 2:
                print(f"  [otp] No codes visible on inbox, clicking email rows...")
                should_click = True

            if should_click:
                new_code = await _click_email_and_get_code(email_page, skip_codes, inbox_url)
                if new_code:
                    code = new_code
                    print(f"  [otp] Found code in email body: {code}")
                    break

            if check_count % 5 == 0:
                print(f"  [otp] Still waiting... ({int(time.time() - start)}s)")
        except Exception as e:
            if check_count <= 3:
                print(f"  [otp] Check error: {e}")

        # Refresh inbox
        try:
            await email_page.reload(wait_until='domcontentloaded')
            await asyncio.sleep(OTP_POLL_INTERVAL_SECONDS)
        except Exception:
            try:
                await email_page.goto(inbox_url, wait_until='domcontentloaded')
                await asyncio.sleep(OTP_POLL_INTERVAL_SECONDS)
            except Exception:
                pass

        await asyncio.sleep(1.5)

    await email_page.close()
    return code
