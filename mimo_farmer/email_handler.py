"""Email generator and OTP polling via generator.email."""

import asyncio
import random
import re
import string
import time

from mimo_farmer.config import EMAIL_DOMAINS, OTP_TIMEOUT_SECONDS, OTP_POLL_INTERVAL_SECONDS


def random_email() -> tuple[str, str, str]:
    """Generate random email address for generator.email.

    Returns:
        (full_email, username, domain)
    """
    user = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    domain = random.choice(EMAIL_DOMAINS)
    return f"{user}@{domain}", user, domain


async def _extract_codes_from_page(email_page) -> list[str]:
    """Extract all 6-digit codes visible on the page (inbox + email body)."""
    codes = set()
    try:
        body = await email_page.evaluate("document.body?.innerText || ''")
        found = re.findall(r'\b(\d{6})\b', body)
        codes.update(found)
    except Exception:
        pass
    return list(codes)


async def _click_latest_email(email_page) -> bool:
    """Click on the latest (first) email row to open its body.

    Returns True if an email was clicked.
    """
    try:
        # generator.email inbox table: rows with onclick or links
        rows = email_page.locator('table tr, .email_row, tr[onclick], a[href*="inbox"]')
        count = await rows.count()
        if count > 0:
            # Click the first data row (skip header)
            for i in range(count):
                row = rows.nth(i)
                text = await row.inner_text()
                # Skip header rows
                if 'From' in text and 'Subject' in text:
                    continue
                if 'xiaomi' in text.lower() or 'verification' in text.lower():
                    await row.click(timeout=3000)
                    await asyncio.sleep(2)
                    return True
            # Fallback: click first non-header row
            if count > 1:
                await rows.nth(1).click(timeout=3000)
                await asyncio.sleep(2)
                return True
    except Exception:
        pass

    # Fallback: try clicking by text content
    try:
        link = email_page.locator('a:has-text("verification"), td:has-text("xiaomi")')
        if await link.count() > 0:
            await link.first.click(timeout=3000)
            await asyncio.sleep(2)
            return True
    except Exception:
        pass

    return False


async def _go_back_to_inbox(email_page, inbox_url: str):
    """Navigate back to inbox view."""
    try:
        back = email_page.locator('a:has-text("Back"), a:has-text("Inbox"), button:has-text("Back")')
        if await back.count() > 0:
            await back.first.click(timeout=3000)
            await asyncio.sleep(2)
            return
    except Exception:
        pass
    try:
        await email_page.goto(inbox_url, wait_until='domcontentloaded')
        await asyncio.sleep(2)
    except Exception:
        pass


async def wait_for_otp(page, user: str, domain: str, timeout: int = OTP_TIMEOUT_SECONDS, skip_codes: list = None) -> str | None:
    """Poll generator.email inbox for 6-digit OTP code.

    Opens new tab in same browser context, polls until code found or timeout.
    If skip_codes provided, those codes are ignored (for identity verification).

    Strategy:
    1. Scan inbox body text for 6-digit codes
    2. If codes found but all in skip_codes, click latest email to read body
    3. Repeat until new code found or timeout

    Args:
        page: Playwright page object (used to open new tab in same context)
        user: Email username part
        domain: Email domain part
        timeout: Max seconds to wait
        skip_codes: List of codes to skip (already used)

    Returns:
        6-digit OTP string or None
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
            # Step 1: Scan inbox body for codes
            codes = await _extract_codes_from_page(email_page)
            if codes:
                otp_codes = [c for c in codes if not c.startswith('20') and c not in skip_codes]
                if otp_codes:
                    code = otp_codes[0]
                    print(f"  [otp] Found code: {code} (check #{check_count})")
                    break

                # All found codes are in skip_codes — try clicking latest email
                if skip_codes and check_count > 2:
                    print(f"  [otp] All codes in skip list, clicking latest email...")
                    clicked = await _click_latest_email(email_page)
                    if clicked:
                        body_codes = await _extract_codes_from_page(email_page)
                        new_codes = [c for c in body_codes if not c.startswith('20') and c not in skip_codes]
                        if new_codes:
                            code = new_codes[0]
                            print(f"  [otp] Found new code in email body: {code}")
                            break
                        # Go back to inbox
                        await _go_back_to_inbox(email_page, inbox_url)

            if check_count % 5 == 0:
                print(f"  [otp] Still waiting... ({int(time.time() - start)}s)")
        except Exception as e:
            if check_count <= 3:
                print(f"  [otp] Check error: {e}")

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
