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
    """Click on Xiaomi email rows to read body, return new code if found.

    generator.email shows email body INLINE when row is clicked (not navigation).
    Multiple click strategies: row, subject cell, JS click, link inside row.
    """
    try:
        # First get a snapshot of current page text to compare later
        before_text = await email_page.evaluate("document.body?.innerText || ''")

        rows = email_page.locator('table tr')
        count = await rows.count()
        print(f"  [otp] Found {count} table rows")

        for i in range(count):
            row = rows.nth(i)
            try:
                row_text = await row.inner_text()
            except Exception:
                continue

            # Skip header row
            if 'From' in row_text and 'Subject' in row_text:
                continue

            # Only process rows from Xiaomi
            if 'xiaomi' not in row_text.lower():
                continue

            print(f"  [otp] Row {i}: {row_text.strip()[:80]}")

            # Strategy 1: click the row directly
            # Strategy 2: click subject cell (2nd td)
            # Strategy 3: JS click on row
            # Strategy 4: click any link/a tag inside row
            clicked = False
            for strategy_name, click_fn in [
                ("row.click", lambda: row.click(timeout=3000)),
                ("subject td", lambda: row.locator('td').nth(1).click(timeout=3000)),
                ("JS click", email_page.evaluate(f"""
                    () => {{
                        const rows = document.querySelectorAll('table tr');
                        if (rows[{i}]) rows[{i}].click();
                    }}
                """)),
                ("link in row", lambda: row.locator('a, td:nth-child(2)').first.click(timeout=3000)),
            ]:
                try:
                    await click_fn()
                    await asyncio.sleep(2)
                    clicked = True

                    # Check if page content changed
                    after_text = await email_page.evaluate("document.body?.innerText || ''")
                    if after_text != before_text:
                        print(f"  [otp] Page changed after {strategy_name}!")

                    # Extract codes from page
                    body_codes = await _extract_codes_from_page(email_page)
                    print(f"  [otp] Found codes on page: {body_codes}")

                    new_codes = [c for c in body_codes if not c.startswith('20') and c not in skip_codes]
                    if new_codes:
                        return new_codes[0]

                    print(f"  [otp] No new codes via {strategy_name}")
                except Exception as e:
                    print(f"  [otp] Strategy '{strategy_name}' failed: {str(e)[:60]}")
                    continue

            # After trying all strategies for this row, go back to inbox
            try:
                current_url = email_page.url
                if current_url != inbox_url:
                    await email_page.goto(inbox_url, wait_until='domcontentloaded')
                else:
                    await email_page.reload(wait_until='domcontentloaded')
                await asyncio.sleep(2)
                before_text = await email_page.evaluate("document.body?.innerText || ''")
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
