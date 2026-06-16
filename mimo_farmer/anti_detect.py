"""Anti-detection & fingerprint spoofing for Playwright/Patchright.

Provides:
1. Random User-Agent, viewport, timezone, locale per session
2. Canvas/WebGL noise injection via JS
3. Navigator.plugins/languages randomization
4. DeviceId cookie clearing
5. Human-like mouse movement (bezier curves)
6. Variable typing speed per character
"""

import math
import random
import string

# ─────────────────────────────────────────────────────────────
# User-Agent Pool (real Chrome UAs, updated periodically)
# ─────────────────────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

# Common viewports (not suspicious sizes)
VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1280, "height": 720},
    {"width": 1600, "height": 900},
    {"width": 1280, "height": 1024},
    {"width": 1680, "height": 1050},
    {"width": 1280, "height": 800},
    {"width": 1360, "height": 768},
]

# ─────────────────────────────────────────────────────────────
# Fingerprint Profiles — consistent UA + timezone + locale
# ─────────────────────────────────────────────────────────────

# Each profile: (UA, timezone, locale, webgl_vendor, webgl_renderer)
# OS-region matched so Google doesn't flag mismatched fingerprints
FINGERPRINT_PROFILES = [
    # Windows US
    {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "timezone": "America/New_York",
        "locale": "en-US",
        "webgl_vendor": "Google Inc. (NVIDIA)",
        "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0)",
    },
    {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "timezone": "America/Chicago",
        "locale": "en-US",
        "webgl_vendor": "Google Inc. (NVIDIA)",
        "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)",
    },
    {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "timezone": "America/Los_Angeles",
        "locale": "en-US",
        "webgl_vendor": "Google Inc. (Intel)",
        "webgl_renderer": "ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0)",
    },
    {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "timezone": "Europe/London",
        "locale": "en-GB",
        "webgl_vendor": "Google Inc. (NVIDIA)",
        "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1050 Ti Direct3D11 vs_5_0 ps_5_0)",
    },
    {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
        "timezone": "Europe/Berlin",
        "locale": "en-US",
        "webgl_vendor": "Google Inc. (AMD)",
        "webgl_renderer": "ANGLE (AMD, AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0)",
    },
    # macOS US
    {
        "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "timezone": "America/New_York",
        "locale": "en-US",
        "webgl_vendor": "Apple",
        "webgl_renderer": "Apple GPU",
    },
    {
        "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "timezone": "America/Los_Angeles",
        "locale": "en-US",
        "webgl_vendor": "Apple",
        "webgl_renderer": "Apple GPU",
    },
    # Windows AU
    {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "timezone": "Australia/Sydney",
        "locale": "en-AU",
        "webgl_vendor": "Google Inc. (NVIDIA)",
        "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0)",
    },
    # Linux US
    {
        "ua": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "timezone": "America/New_York",
        "locale": "en-US",
        "webgl_vendor": "Google Inc. (NVIDIA)",
        "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)",
    },
    # Windows ID (for Indonesian IP)
    {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "timezone": "Asia/Jakarta",
        "locale": "id-ID",
        "webgl_vendor": "Google Inc. (NVIDIA)",
        "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0)",
    },
    # Windows SG
    {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "timezone": "Asia/Singapore",
        "locale": "en-US",
        "webgl_vendor": "Google Inc. (Intel)",
        "webgl_renderer": "ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0)",
    },
]


def random_fingerprint() -> dict:
    """Generate random but CONSISTENT browser fingerprint settings.

    UA, timezone, locale, WebGL vendor/renderer are matched per profile
    so Google doesn't flag mismatched fingerprints (e.g., Mac + Jakarta timezone).
    """
    profile = random.choice(FINGERPRINT_PROFILES)
    viewport = random.choice(VIEWPORTS)
    return {
        "user_agent": profile["ua"],
        "viewport": viewport,
        "timezone": profile["timezone"],
        "locale": profile["locale"],
        "webgl_vendor": profile["webgl_vendor"],
        "webgl_renderer": profile["webgl_renderer"],
    }


# ─────────────────────────────────────────────────────────────
# Stealth JS — injected before every page load
# ─────────────────────────────────────────────────────────────

STEALTH_JS = """
(() => {
    // 1. Override navigator.webdriver → false
    Object.defineProperty(navigator, 'webdriver', {
        get: () => false,
        configurable: true,
    });

    // 2. Override navigator.plugins (fake non-empty plugin list)
    const fakePlugins = [
        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
        { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' },
    ];
    Object.defineProperty(navigator, 'plugins', {
        get: () => {
            const list = fakePlugins;
            list.length = fakePlugins.length;
            list.item = (i) => fakePlugins[i] || null;
            list.namedItem = (name) => fakePlugins.find(p => p.name === name) || null;
            list.refresh = () => {};
            return list;
        },
        configurable: true,
    });

    // 3. Override navigator.languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en'],
        configurable: true,
    });

    // 4. Canvas noise injection (subtle — adds ~1-3px noise per draw)
    const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(type, quality) {
        const ctx = this.getContext('2d');
        if (ctx) {
            const imageData = ctx.getImageData(0, 0, this.width, this.height);
            const data = imageData.data;
            // Add subtle noise to a random subset of pixels
            for (let i = 0; i < data.length; i += 4 * Math.floor(Math.random() * 100 + 50)) {
                data[i] = data[i] ^ (Math.random() > 0.5 ? 1 : 0);     // R
                data[i+1] = data[i+1] ^ (Math.random() > 0.5 ? 1 : 0); // G
                data[i+2] = data[i+2] ^ (Math.random() > 0.5 ? 1 : 0); // B
            }
            ctx.putImageData(imageData, 0, 0);
        }
        return origToDataURL.call(this, type, quality);
    };

    const origToBlob = HTMLCanvasElement.prototype.toBlob;
    HTMLCanvasElement.prototype.toBlob = function(callback, type, quality) {
        const ctx = this.getContext('2d');
        if (ctx) {
            const imageData = ctx.getImageData(0, 0, this.width, this.height);
            const data = imageData.data;
            for (let i = 0; i < data.length; i += 4 * Math.floor(Math.random() * 100 + 50)) {
                data[i] = data[i] ^ (Math.random() > 0.5 ? 1 : 0);
                data[i+1] = data[i+1] ^ (Math.random() > 0.5 ? 1 : 0);
                data[i+2] = data[i+2] ^ (Math.random() > 0.5 ? 1 : 0);
            }
            ctx.putImageData(imageData, 0, 0);
        }
        return origToBlob.call(this, callback, type, quality);
    };

    // 5. WebGL noise — override getParameter for vendor/renderer
    // These values are injected dynamically from the fingerprint profile
    const __WEBGL_VENDOR__ = 'VENDOR_PLACEHOLDER';
    const __WEBGL_RENDERER__ = 'RENDERER_PLACEHOLDER';
    const getParam = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(param) {
        // UNMASKED_VENDOR_WEBGL
        if (param === 0x9245) return __WEBGL_VENDOR__;
        // UNMASKED_RENDERER_WEBGL
        if (param === 0x9246) return __WEBGL_RENDERER__;
        return getParam.call(this, param);
    };

    // 6. Override chrome.runtime (headless detection)
    if (!window.chrome) window.chrome = {};
    if (!window.chrome.runtime) {
        window.chrome.runtime = {
            connect: () => {},
            sendMessage: () => {},
        };
    }

    // 7. Override permissions query (notification permission)
    const origQuery = window.navigator.permissions?.query;
    if (origQuery) {
        window.navigator.permissions.query = (params) => {
            if (params.name === 'notifications') {
                return Promise.resolve({ state: Notification.permission });
            }
            return origQuery.call(window.navigator.permissions, params);
        };
    }

    // 8. Consistent screen dimensions with viewport
    Object.defineProperty(screen, 'availWidth', { get: () => window.innerWidth });
    Object.defineProperty(screen, 'availHeight', { get: () => window.innerHeight });
})();
"""


# ─────────────────────────────────────────────────────────────
# Human-like typing — variable speed per character type
# ─────────────────────────────────────────────────────────────

def human_typing_delay(char: str) -> int:
    """Return delay in ms for typing a character. Mimics real human rhythm.

    - Letters: fast (50-120ms)
    - Numbers: medium (80-160ms)
    - Symbols/special: slow (120-250ms)
    - After shift-key chars: extra pause
    - Random bursts: occasionally type faster (20-40ms) for 2-4 chars
    """
    if char in string.ascii_letters:
        base = random.randint(50, 120)
    elif char in string.digits:
        base = random.randint(80, 160)
    elif char in '!@#$%^&*()_+{}|:<>?':
        base = random.randint(120, 250)
    else:
        base = random.randint(60, 140)

    # 15% chance of burst typing (faster)
    if random.random() < 0.15:
        base = random.randint(20, 45)

    return base


# ─────────────────────────────────────────────────────────────
# Human-like mouse movement (bezier curve)
# ─────────────────────────────────────────────────────────────

def bezier_points(start: tuple, end: tuple, steps: int = None) -> list[tuple]:
    """Generate bezier curve points from start to end for human-like mouse movement.

    Uses a cubic bezier with two random control points.
    Returns list of (x, y) tuples.
    """
    if steps is None:
        steps = random.randint(15, 35)

    x0, y0 = start
    x3, y3 = end

    # Random control points (add some curve)
    dist = math.sqrt((x3 - x0) ** 2 + (y3 - y0) ** 2)
    jitter = dist * 0.3

    x1 = x0 + (x3 - x0) * random.uniform(0.2, 0.5) + random.uniform(-jitter, jitter)
    y1 = y0 + (y3 - y0) * random.uniform(0.1, 0.4) + random.uniform(-jitter, jitter)
    x2 = x0 + (x3 - x0) * random.uniform(0.5, 0.8) + random.uniform(-jitter, jitter)
    y2 = y0 + (y3 - y0) * random.uniform(0.6, 0.9) + random.uniform(-jitter, jitter)

    points = []
    for i in range(steps + 1):
        t = i / steps
        # Ease-in-out: t' = 3t² - 2t³
        t_ease = 3 * t * t - 2 * t * t * t

        x = (1 - t_ease) ** 3 * x0 + 3 * (1 - t_ease) ** 2 * t_ease * x1 + \
            3 * (1 - t_ease) * t_ease ** 2 * x2 + t_ease ** 3 * x3
        y = (1 - t_ease) ** 3 * y0 + 3 * (1 - t_ease) ** 2 * t_ease * y1 + \
            3 * (1 - t_ease) * t_ease ** 2 * y2 + t_ease ** 3 * y3

        points.append((int(x), int(y)))

    return points


async def human_move_to(page, selector: str, box: dict = None):
    """Move mouse to element with human-like bezier curve."""
    if box is None:
        loc = page.locator(selector)
        box = await loc.bounding_box()
    if not box:
        return

    # Target: random point within element bounds (not exact center)
    target_x = box['x'] + random.uniform(box['width'] * 0.2, box['width'] * 0.8)
    target_y = box['y'] + random.uniform(box['height'] * 0.2, box['height'] * 0.8)

    # Start from random position (or current mouse pos estimate)
    start_x = random.randint(100, 800)
    start_y = random.randint(100, 600)

    points = bezier_points((start_x, start_y), (target_x, target_y))

    for px, py in points:
        await page.mouse.move(px, py)
        await asyncio.sleep(random.uniform(0.005, 0.02))


# ─────────────────────────────────────────────────────────────
# Cookie/Storage cleanup
# ─────────────────────────────────────────────────────────────

async def clear_device_cookies(context):
    """Clear Xiaomi-related cookies including deviceId."""
    try:
        cookies = await context.cookies()
        xiaomi_cookies = [c for c in cookies if 'xiaomi' in c.get('domain', '').lower()
                          or 'mimo' in c.get('domain', '').lower()]
        for cookie in xiaomi_cookies:
            await context.clear_cookies(name=cookie['name'], domain=cookie['domain'])
    except Exception:
        pass

    # Also clear via JS
    for page in context.pages:
        try:
            await page.evaluate("""
                (() => {
                    // Clear all cookies
                    document.cookie.split(';').forEach(c => {
                        const name = c.split('=')[0].trim();
                        document.cookie = name + '=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/';
                        document.cookie = name + '=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;domain=.xiaomi.com';
                        document.cookie = name + '=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;domain=.account.xiaomi.com';
                    });
                    // Clear localStorage
                    try { localStorage.clear(); } catch(e) {}
                    try { sessionStorage.clear(); } catch(e) {}
                })()
            """)
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────
# Integration helper — apply all stealth to context+page
# ─────────────────────────────────────────────────────────────

async def apply_stealth(context, page, fingerprint: dict = None):
    """Apply all anti-detection measures to a browser context and page.

    Call this right after creating context + page, BEFORE any navigation.

    Args:
        fingerprint: Optional fingerprint dict from random_fingerprint().
                     If provided, WebGL vendor/renderer are set to match the profile.
    """
    # Replace WebGL placeholders with profile-specific values
    js = STEALTH_JS
    if fingerprint:
        vendor = fingerprint.get("webgl_vendor", "Google Inc. (NVIDIA)")
        renderer = fingerprint.get("webgl_renderer", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0)")
        js = js.replace("'VENDOR_PLACEHOLDER'", repr(vendor))
        js = js.replace("'RENDERER_PLACEHOLDER'", repr(renderer))

    # Inject stealth JS before every page load
    await context.add_init_script(js)

    # Also inject on current page (in case already loaded)
    try:
        await page.evaluate(js)
    except Exception:
        pass
