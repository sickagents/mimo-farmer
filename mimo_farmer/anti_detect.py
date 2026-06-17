"""Anti-detection & fingerprint spoofing for Playwright/Patchright.

Provides:
1. Random User-Agent, viewport, timezone, locale per session
2. Canvas noise injection — SEEDDED deterministic per profile (consistent hash)
3. WebGL full parameter spoofing (not just vendor/renderer)
4. Navigator.plugins/languages randomization (Chrome 127+ aware)
5. hardwareConcurrency / deviceMemory override per profile
6. AudioContext fingerprint evasion (deterministic buffer spoofing)
7. DeviceId cookie clearing
8. Human-like mouse movement (bezier curves)
9. Variable typing speed per character
"""

import hashlib
import json as _json
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

# Each profile: (UA, timezone, locale, webgl_vendor, webgl_renderer,
#                hardware_concurrency, device_memory, chrome_version, gpu_params)
# OS-region matched so Google doesn't flag mismatched fingerprints
#
# chrome_version: Used to determine if plugins should be spoofed (Chrome 127+ = empty)
# hardware_concurrency: navigator.hardwareConcurrency (CPU logical cores)
# device_memory: navigator.deviceMemory (GB)
# gpu_params: dict of WebGL parameter overrides matching the claimed GPU

def _gpu_params_nvidia_gtx1650():
    """WebGL params matching NVIDIA GeForce GTX 1650 (Direct3D11)."""
    return {
        "MAX_TEXTURE_SIZE": 16384,
        "MAX_VIEWPORT_DIMS": [16384, 16384],
        "MAX_RENDERBUFFER_SIZE": 16384,
        "ALIASED_LINE_WIDTH_RANGE": [1, 1],
        "ALIASED_POINT_SIZE_RANGE": [1, 1024],
        "MAX_VERTEX_ATTRIBS": 16,
        "MAX_VERTEX_UNIFORM_VECTORS": 4096,
        "MAX_VARYING_VECTORS": 30,
        "MAX_VERTEX_TEXTURE_IMAGE_UNITS": 16,
        "MAX_TEXTURE_IMAGE_UNITS": 16,
        "MAX_FRAGMENT_UNIFORM_VECTORS": 1024,
        "MAX_COMBINED_TEXTURE_IMAGE_UNITS": 32,
        "MAX_CUBE_MAP_TEXTURE_SIZE": 16384,
    }

def _gpu_params_nvidia_rtx3060():
    """WebGL params matching NVIDIA GeForce RTX 3060 (Direct3D11)."""
    return {
        "MAX_TEXTURE_SIZE": 32768,
        "MAX_VIEWPORT_DIMS": [32768, 32768],
        "MAX_RENDERBUFFER_SIZE": 32768,
        "ALIASED_LINE_WIDTH_RANGE": [1, 1],
        "ALIASED_POINT_SIZE_RANGE": [1, 1024],
        "MAX_VERTEX_ATTRIBS": 16,
        "MAX_VERTEX_UNIFORM_VECTORS": 4096,
        "MAX_VARYING_VECTORS": 30,
        "MAX_VERTEX_TEXTURE_IMAGE_UNITS": 16,
        "MAX_TEXTURE_IMAGE_UNITS": 16,
        "MAX_FRAGMENT_UNIFORM_VECTORS": 1024,
        "MAX_COMBINED_TEXTURE_IMAGE_UNITS": 32,
        "MAX_CUBE_MAP_TEXTURE_SIZE": 32768,
    }

def _gpu_params_intel_uhd():
    """WebGL params matching Intel UHD Graphics (Direct3D11)."""
    return {
        "MAX_TEXTURE_SIZE": 16384,
        "MAX_VIEWPORT_DIMS": [16384, 16384],
        "MAX_RENDERBUFFER_SIZE": 16384,
        "ALIASED_LINE_WIDTH_RANGE": [1, 1],
        "ALIASED_POINT_SIZE_RANGE": [1, 256],
        "MAX_VERTEX_ATTRIBS": 16,
        "MAX_VERTEX_UNIFORM_VECTORS": 4096,
        "MAX_VARYING_VECTORS": 30,
        "MAX_VERTEX_TEXTURE_IMAGE_UNITS": 16,
        "MAX_TEXTURE_IMAGE_UNITS": 16,
        "MAX_FRAGMENT_UNIFORM_VECTORS": 1024,
        "MAX_COMBINED_TEXTURE_IMAGE_UNITS": 32,
        "MAX_CUBE_MAP_TEXTURE_SIZE": 16384,
    }

def _gpu_params_nvidia_gtx1050ti():
    """WebGL params matching NVIDIA GeForce GTX 1050 Ti (Direct3D11)."""
    return {
        "MAX_TEXTURE_SIZE": 16384,
        "MAX_VIEWPORT_DIMS": [16384, 16384],
        "MAX_RENDERBUFFER_SIZE": 16384,
        "ALIASED_LINE_WIDTH_RANGE": [1, 1],
        "ALIASED_POINT_SIZE_RANGE": [1, 1024],
        "MAX_VERTEX_ATTRIBS": 16,
        "MAX_VERTEX_UNIFORM_VECTORS": 4096,
        "MAX_VARYING_VECTORS": 30,
        "MAX_VERTEX_TEXTURE_IMAGE_UNITS": 16,
        "MAX_TEXTURE_IMAGE_UNITS": 16,
        "MAX_FRAGMENT_UNIFORM_VECTORS": 1024,
        "MAX_COMBINED_TEXTURE_IMAGE_UNITS": 32,
        "MAX_CUBE_MAP_TEXTURE_SIZE": 16384,
    }

def _gpu_params_amd_rx580():
    """WebGL params matching AMD Radeon RX 580 (Direct3D11)."""
    return {
        "MAX_TEXTURE_SIZE": 16384,
        "MAX_VIEWPORT_DIMS": [16384, 16384],
        "MAX_RENDERBUFFER_SIZE": 16384,
        "ALIASED_LINE_WIDTH_RANGE": [1, 1],
        "ALIASED_POINT_SIZE_RANGE": [1, 1024],
        "MAX_VERTEX_ATTRIBS": 16,
        "MAX_VERTEX_UNIFORM_VECTORS": 4096,
        "MAX_VARYING_VECTORS": 30,
        "MAX_VERTEX_TEXTURE_IMAGE_UNITS": 16,
        "MAX_TEXTURE_IMAGE_UNITS": 16,
        "MAX_FRAGMENT_UNIFORM_VECTORS": 1024,
        "MAX_COMBINED_TEXTURE_IMAGE_UNITS": 32,
        "MAX_CUBE_MAP_TEXTURE_SIZE": 16384,
    }

def _gpu_params_apple():
    """WebGL params matching Apple GPU (Metal)."""
    return {
        "MAX_TEXTURE_SIZE": 16384,
        "MAX_VIEWPORT_DIMS": [16384, 16384],
        "MAX_RENDERBUFFER_SIZE": 16384,
        "ALIASED_LINE_WIDTH_RANGE": [1, 1],
        "ALIASED_POINT_SIZE_RANGE": [1, 511],
        "MAX_VERTEX_ATTRIBS": 16,
        "MAX_VERTEX_UNIFORM_VECTORS": 4096,
        "MAX_VARYING_VECTORS": 30,
        "MAX_VERTEX_TEXTURE_IMAGE_UNITS": 16,
        "MAX_TEXTURE_IMAGE_UNITS": 16,
        "MAX_FRAGMENT_UNIFORM_VECTORS": 1024,
        "MAX_COMBINED_TEXTURE_IMAGE_UNITS": 32,
        "MAX_CUBE_MAP_TEXTURE_SIZE": 16384,
    }

FINGERPRINT_PROFILES = [
    # Windows US
    {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "timezone": "America/New_York",
        "locale": "en-US",
        "webgl_vendor": "Google Inc. (NVIDIA)",
        "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0)",
        "hardware_concurrency": 8,
        "device_memory": 8,
        "chrome_version": 131,
        "gpu_params_fn": _gpu_params_nvidia_gtx1650,
        "platform": "Windows",
    },
    {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "timezone": "America/Chicago",
        "locale": "en-US",
        "webgl_vendor": "Google Inc. (NVIDIA)",
        "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)",
        "hardware_concurrency": 16,
        "device_memory": 16,
        "chrome_version": 130,
        "gpu_params_fn": _gpu_params_nvidia_rtx3060,
        "platform": "Windows",
    },
    {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "timezone": "America/Los_Angeles",
        "locale": "en-US",
        "webgl_vendor": "Google Inc. (Intel)",
        "webgl_renderer": "ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0)",
        "hardware_concurrency": 8,
        "device_memory": 8,
        "chrome_version": 129,
        "gpu_params_fn": _gpu_params_intel_uhd,
        "platform": "Windows",
    },
    {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "timezone": "Europe/London",
        "locale": "en-GB",
        "webgl_vendor": "Google Inc. (NVIDIA)",
        "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1050 Ti Direct3D11 vs_5_0 ps_5_0)",
        "hardware_concurrency": 8,
        "device_memory": 8,
        "chrome_version": 128,
        "gpu_params_fn": _gpu_params_nvidia_gtx1050ti,
        "platform": "Windows",
    },
    {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
        "timezone": "Europe/Berlin",
        "locale": "en-US",
        "webgl_vendor": "Google Inc. (AMD)",
        "webgl_renderer": "ANGLE (AMD, AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0)",
        "hardware_concurrency": 12,
        "device_memory": 16,
        "chrome_version": 131,
        "gpu_params_fn": _gpu_params_amd_rx580,
        "platform": "Windows",
    },
    # macOS US
    {
        "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "timezone": "America/New_York",
        "locale": "en-US",
        "webgl_vendor": "Apple",
        "webgl_renderer": "Apple GPU",
        "hardware_concurrency": 10,
        "device_memory": 16,
        "chrome_version": 131,
        "gpu_params_fn": _gpu_params_apple,
        "platform": "macOS",
    },
    {
        "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "timezone": "America/Los_Angeles",
        "locale": "en-US",
        "webgl_vendor": "Apple",
        "webgl_renderer": "Apple GPU",
        "hardware_concurrency": 8,
        "device_memory": 8,
        "chrome_version": 130,
        "gpu_params_fn": _gpu_params_apple,
        "platform": "macOS",
    },
    # Windows AU
    {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "timezone": "Australia/Sydney",
        "locale": "en-AU",
        "webgl_vendor": "Google Inc. (NVIDIA)",
        "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0)",
        "hardware_concurrency": 8,
        "device_memory": 8,
        "chrome_version": 127,
        "gpu_params_fn": _gpu_params_nvidia_gtx1650,
        "platform": "Windows",
    },
    # Linux US
    {
        "ua": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "timezone": "America/New_York",
        "locale": "en-US",
        "webgl_vendor": "Google Inc. (NVIDIA)",
        "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)",
        "hardware_concurrency": 16,
        "device_memory": 32,
        "chrome_version": 131,
        "gpu_params_fn": _gpu_params_nvidia_rtx3060,
        "platform": "Linux",
    },
    # Windows ID (for Indonesian IP)
    {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "timezone": "Asia/Jakarta",
        "locale": "id-ID",
        "webgl_vendor": "Google Inc. (NVIDIA)",
        "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0)",
        "hardware_concurrency": 8,
        "device_memory": 8,
        "chrome_version": 131,
        "gpu_params_fn": _gpu_params_nvidia_gtx1650,
        "platform": "Windows",
    },
    # Windows SG
    {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "timezone": "Asia/Singapore",
        "locale": "en-US",
        "webgl_vendor": "Google Inc. (Intel)",
        "webgl_renderer": "ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0)",
        "hardware_concurrency": 8,
        "device_memory": 8,
        "chrome_version": 130,
        "gpu_params_fn": _gpu_params_intel_uhd,
        "platform": "Windows",
    },
]


def random_fingerprint() -> dict:
    """Generate random but CONSISTENT browser fingerprint settings.

    UA, timezone, locale, WebGL vendor/renderer, hardware_concurrency,
    device_memory, chrome_version, and gpu_params are matched per profile
    so Google doesn't flag mismatched fingerprints (e.g., Mac + Jakarta timezone).
    """
    profile = random.choice(FINGERPRINT_PROFILES)
    viewport = random.choice(VIEWPORTS)
    # Derive a deterministic canvas seed from profile identity
    canvas_seed = int(hashlib.sha256(
        (profile["ua"] + profile["timezone"] + profile["webgl_renderer"]).encode()
    ).hexdigest()[:8], 16)
    return {
        "user_agent": profile["ua"],
        "viewport": viewport,
        "timezone": profile["timezone"],
        "locale": profile["locale"],
        "webgl_vendor": profile["webgl_vendor"],
        "webgl_renderer": profile["webgl_renderer"],
        "hardware_concurrency": profile["hardware_concurrency"],
        "device_memory": profile["device_memory"],
        "chrome_version": profile["chrome_version"],
        "gpu_params": profile["gpu_params_fn"](),
        "canvas_seed": canvas_seed,
        "platform": profile["platform"],
    }


# ─────────────────────────────────────────────────────────────
# Stealth JS — injected before every page load
# Placeholders replaced at injection time from fingerprint profile
# ─────────────────────────────────────────────────────────────

STEALTH_JS = """
(() => {
    // ── 0. Seeded PRNG for deterministic noise (canvas, audio) ──
    // Uses mulberry32 — fast, 32-bit, deterministic from seed
    function __seeded_rng(seed) {
        return function() {
            seed |= 0; seed = seed + 0x6D2B79F5 | 0;
            let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
            t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
            return ((t ^ t >>> 14) >>> 0) / 4294967296;
        };
    }
    const __rng = __seeded_rng(__CANVAS_SEED__);
    // Reset RNG before each canvas draw for consistency
    let __canvasRng = __rng;

    // ── 1. navigator.webdriver → false ──
    Object.defineProperty(navigator, 'webdriver', {
        get: () => false,
        configurable: true,
    });

    // ── 2. navigator.plugins (Chrome 127+ version-aware) ──
    // Chrome 127+ deprecated plugins → empty array.
    // Spoofing non-empty on 127+ = over-spoof detection.
    const __chromeVersion = __CHROME_VERSION__;
    if (__chromeVersion < 127) {
        // Pre-127: fake non-empty plugin list
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
    }
    // Chrome 127+ → leave plugins as-is (empty array, correct behavior)

    // ── 3. navigator.languages ──
    Object.defineProperty(navigator, 'languages', {
        get: () => __LOCALE__,
        configurable: true,
    });

    // ── 4. navigator.hardwareConcurrency ──
    Object.defineProperty(navigator, 'hardwareConcurrency', {
        get: () => __HW_CONCURRENCY__,
        configurable: true,
    });

    // ── 5. navigator.deviceMemory ──
    Object.defineProperty(navigator, 'deviceMemory', {
        get: () => __DEVICE_MEMORY__,
        configurable: true,
    });

    // ── 6. Canvas noise — SEEDED deterministic per profile ──
    // Same profile always produces same canvas hash.
    // Anti-bot detects random noise because hash changes between calls.
    // Seeded noise = same browser, same modified pixels, same hash.
    const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(type, quality) {
        const ctx = this.getContext('2d');
        if (ctx) {
            // Reset PRNG so same seed → same noise pattern
            __canvasRng = __seeded_rng(__CANVAS_SEED__);
            const imageData = ctx.getImageData(0, 0, this.width, this.height);
            const data = imageData.data;
            // Deterministic: pick pixels and noise values from seeded RNG
            const step = Math.floor(__canvasRng() * 80) + 50; // 50-130
            for (let i = 0; i < data.length; i += 4 * step) {
                data[i]   = data[i]   ^ (__canvasRng() > 0.5 ? 1 : 0);   // R
                data[i+1] = data[i+1] ^ (__canvasRng() > 0.5 ? 1 : 0);   // G
                data[i+2] = data[i+2] ^ (__canvasRng() > 0.5 ? 1 : 0);   // B
            }
            ctx.putImageData(imageData, 0, 0);
        }
        return origToDataURL.call(this, type, quality);
    };

    const origToBlob = HTMLCanvasElement.prototype.toBlob;
    HTMLCanvasElement.prototype.toBlob = function(callback, type, quality) {
        const ctx = this.getContext('2d');
        if (ctx) {
            __canvasRng = __seeded_rng(__CANVAS_SEED__);
            const imageData = ctx.getImageData(0, 0, this.width, this.height);
            const data = imageData.data;
            const step = Math.floor(__canvasRng() * 80) + 50;
            for (let i = 0; i < data.length; i += 4 * step) {
                data[i]   = data[i]   ^ (__canvasRng() > 0.5 ? 1 : 0);
                data[i+1] = data[i+1] ^ (__canvasRng() > 0.5 ? 1 : 0);
                data[i+2] = data[i+2] ^ (__canvasRng() > 0.5 ? 1 : 0);
            }
            ctx.putImageData(imageData, 0, 0);
        }
        return origToBlob.call(this, callback, type, quality);
    };

    // ── 7. WebGL full parameter spoofing ──
    // Not just vendor/renderer — spoof all GL parameters to match claimed GPU.
    // Anti-bot cross-checks MAX_TEXTURE_SIZE etc. against renderer string.
    const __WEBGL_VENDOR__ = 'VENDOR_PLACEHOLDER';
    const __WEBGL_RENDERER__ = 'RENDERER_PLACEHOLDER';
    const __GPU_PARAMS__ = GPU_PARAMS_PLACEHOLDER;

    // GL constant → param name mapping
    const __GL_CONSTANTS = {
        0x0D33: 'MAX_TEXTURE_SIZE',
        0x0D3A: 'MAX_VIEWPORT_DIMS',
        0x84E8: 'MAX_RENDERBUFFER_SIZE',
        0x846D: 'ALIASED_LINE_WIDTH_RANGE',
        0x8460: 'ALIASED_POINT_SIZE_RANGE',
        0x8869: 'MAX_VERTEX_ATTRIBS',
        0x8DFB: 'MAX_VERTEX_UNIFORM_VECTORS',
        0x8DFC: 'MAX_VARYING_VECTORS',
        0x8B4C: 'MAX_VERTEX_TEXTURE_IMAGE_UNITS',
        0x8872: 'MAX_TEXTURE_IMAGE_UNITS',
        0x8DFD: 'MAX_FRAGMENT_UNIFORM_VECTORS',
        0x8B4D: 'MAX_COMBINED_TEXTURE_IMAGE_UNITS',
        0x851C: 'MAX_CUBE_MAP_TEXTURE_SIZE',
    };

    const getParam = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(param) {
        // Vendor/renderer
        if (param === 0x9245) return __WEBGL_VENDOR__;
        if (param === 0x9246) return __WEBGL_RENDERER__;
        // Full GPU params spoofing
        const name = __GL_CONSTANTS[param];
        if (name && __GPU_PARAMS__[name] !== undefined) {
            return __GPU_PARAMS__[name];
        }
        return getParam.call(this, param);
    };

    // Also override WebGL2 if available
    if (typeof WebGL2RenderingContext !== 'undefined') {
        const getParam2 = WebGL2RenderingContext.prototype.getParameter;
        WebGL2RenderingContext.prototype.getParameter = function(param) {
            if (param === 0x9245) return __WEBGL_VENDOR__;
            if (param === 0x9246) return __WEBGL_RENDERER__;
            const name = __GL_CONSTANTS[param];
            if (name && __GPU_PARAMS__[name] !== undefined) {
                return __GPU_PARAMS__[name];
            }
            return getParam2.call(this, param);
        };
    }

    // ── 8. AudioContext fingerprint evasion ──
    // Headless Chrome produces different audio output than real Chrome.
    // Deterministic buffer spoofing: same seed → same audio hash.
    // Intercepts OfflineAudioContext.startRendering to return consistent buffer.
    if (window.OfflineAudioContext) {
        const origStartRendering = OfflineAudioContext.prototype.startRendering;
        OfflineAudioContext.prototype.startRendering = function() {
            return origStartRendering.call(this).then(buffer => {
                // Add deterministic micro-noise to channel data
                const audioRng = __seeded_rng(__CANVAS_SEED__ + 777);
                for (let ch = 0; ch < buffer.numberOfChannels; ch++) {
                    const data = buffer.getChannelData(ch);
                    // Modify ~0.1% of samples with tiny noise
                    for (let i = 0; i < data.length; i += Math.floor(audioRng() * 1000) + 500) {
                        data[i] += (audioRng() - 0.5) * 1e-7; // imperceptible noise
                    }
                }
                return buffer;
            });
        };
    }

    // ── 9. chrome.runtime (headless detection) ──
    if (!window.chrome) window.chrome = {};
    if (!window.chrome.runtime) {
        window.chrome.runtime = {
            connect: () => {},
            sendMessage: () => {},
        };
    }

    // ── 10. Permissions API (notification) ──
    const origQuery = window.navigator.permissions?.query;
    if (origQuery) {
        window.navigator.permissions.query = (params) => {
            if (params.name === 'notifications') {
                return Promise.resolve({ state: Notification.permission });
            }
            return origQuery.call(window.navigator.permissions, params);
        };
    }

    // ── 11. Screen dimensions ──
    Object.defineProperty(screen, 'availWidth', { get: () => window.innerWidth });
    Object.defineProperty(screen, 'availHeight', { get: () => window.innerHeight });

    // ── 12. Font fingerprint evasion ──
    // Anti-bot enumerates installed fonts via CSS measurement.
    // Windows has Segoe UI, Tahoma, Consolas, etc.
    // macOS has San Francisco, Helvetica Neue, Avenir, Menlo, etc.
    // If we spoof Mac but have Windows fonts = detected.
    // Override document.fonts API to filter fonts by claimed platform.
    const __PLATFORM__ = '__PLATFORM_VAL__';
    const __PLATFORM_FONTS__ = {
        'Windows': new Set([
            'Arial', 'Arial Black', 'Calibri', 'Cambria', 'Candara', 'Comic Sans MS',
            'Consolas', 'Constantia', 'Corbel', 'Courier New', 'Georgia', 'Impact',
            'Lucida Console', 'Lucida Sans Unicode', 'Microsoft Sans Serif', 'Palatino Linotype',
            'Segoe UI', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Tahoma', 'Times New Roman',
            'Trebuchet MS', 'Verdana', 'Wingdings',
        ]),
        'macOS': new Set([
            'American Typewriter', 'Apple Chancery', 'Arial', 'Arial Black', 'Avenir',
            'Avenir Next', 'Baskerville', 'Big Caslon', 'Brush Script MT', 'Chalkboard',
            'Cochin', 'Comic Sans MS', 'Copperplate', 'Courier New', 'Didot',
            'Futura', 'Geneva', 'Georgia', 'Gill Sans', 'Helvetica', 'Helvetica Neue',
            'Hoefler Text', 'Impact', 'Lucida Grande', 'Marker Felt', 'Menlo',
            'Monaco', 'Optima', 'Palatino', 'Papyrus', 'Phosphate', 'Rockwell',
            'SF Pro', 'Skia', 'Times New Roman', 'Trebuchet MS', 'Verdana',
        ]),
        'Linux': new Set([
            'Arial', 'Bitstream Charter', 'Century Schoolbook L', 'Comic Sans MS',
            'Courier New', 'DejaVu Sans', 'DejaVu Sans Mono', 'DejaVu Serif',
            'Droid Sans', 'FreeMono', 'FreeSans', 'FreeSerif', 'Garuda',
            'Georgia', 'Impact', 'Liberation Mono', 'Liberation Sans', 'Liberation Serif',
            'Linux Biolinum', 'Linux Libertine', 'Loma', 'Noto Sans', 'Noto Serif',
            'Noto Sans CJK', 'OpenSymbol', 'Oxygen-Sans', 'Roboto', 'Symbol',
            'Times New Roman', 'Trebuchet MS', 'Ubuntu', 'Verdana',
        ]),
    };
    const __allowedFonts = __PLATFORM_FONTS__[__PLATFORM__] || __PLATFORM_FONTS__['Windows'];

    // Override document.fonts.values() / entries() / forEach() / keys()
    const origFontsValues = Document.prototype.fonts;
    if (origFontsValues) {
        const filterFontSet = (fontSet) => {
            try {
                const filtered = [];
                fontSet.forEach(f => {
                    if (__allowedFonts.has(f.family.replace(/["']/g, ''))) {
                        filtered.push(f);
                    }
                });
                return filtered;
            } catch(e) { return Array.from(fontSet); }
        };

        // Override the FontFaceSet iteration
        const origForEach = FontFaceSet.prototype.forEach;
        FontFaceSet.prototype.forEach = function(callback, thisArg) {
            return origForEach.call(this, function(value, key, set) {
                if (__allowedFonts.has(value.family.replace(/["']/g, ''))) {
                    callback.call(thisArg, value, key, set);
                }
            }, thisArg);
        };

        // Override document.fonts.size to reflect filtered count
        try {
            const origSize = Object.getOwnPropertyDescriptor(FontFaceSet.prototype, 'size');
            // Can't always override size, but try
        } catch(e) {}
    }
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
                     If provided, WebGL vendor/renderer, canvas seed,
                     hardware_concurrency, device_memory, chrome_version,
                     gpu_params, locale, platform are set to match the profile.
    """
    js = STEALTH_JS
    if fingerprint:
        vendor = fingerprint.get("webgl_vendor", "Google Inc. (NVIDIA)")
        renderer = fingerprint.get("webgl_renderer", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0)")
        canvas_seed = fingerprint.get("canvas_seed", 12345)
        hw_concurrency = fingerprint.get("hardware_concurrency", 8)
        device_memory = fingerprint.get("device_memory", 8)
        chrome_version = fingerprint.get("chrome_version", 131)
        gpu_params = fingerprint.get("gpu_params", {})
        locale = fingerprint.get("locale", "en-US")
        platform = fingerprint.get("platform", "Windows")
        # Build locale array: en-US → ['en-US', 'en']
        lang_base = locale.split("-")[0]
        locale_arr = f"['{locale}', '{lang_base}']"

        js = js.replace("'VENDOR_PLACEHOLDER'", repr(vendor))
        js = js.replace("'RENDERER_PLACEHOLDER'", repr(renderer))
        js = js.replace("GPU_PARAMS_PLACEHOLDER", _json.dumps(gpu_params))
        js = js.replace("__CANVAS_SEED__", str(canvas_seed))
        js = js.replace("__HW_CONCURRENCY__", str(hw_concurrency))
        js = js.replace("__DEVICE_MEMORY__", str(device_memory))
        js = js.replace("__CHROME_VERSION__", str(chrome_version))
        js = js.replace("__LOCALE__", locale_arr)
        js = js.replace("'__PLATFORM_VAL__'", f"'{platform}'")

        # ── Client Hints headers (sec-ch-ua-*) ──
        # These must match the UA string. Server cross-checks them.
        # Only Chrome/Edge 89+ send these. Firefox doesn't support.
        is_edge = "Edg/" in fingerprint.get("user_agent", "")
        brand = '"Microsoft Edge"' if is_edge else '"Google Chrome"'
        brand_chromium = '"Chromium"'
        brand_not = '"Not_A Brand";v="24"'

        # Generate realistic full version (major.0.XXXX.XX)
        # Derive patch version from canvas_seed for consistency
        patch1 = (canvas_seed % 9000) + 1000
        patch2 = (canvas_seed % 90) + 10
        full_version = f"{chrome_version}.0.{patch1}.{patch2}"

        # Platform version
        if platform == "Windows":
            platform_version = "15.0.0"
        elif platform == "macOS":
            platform_version = "14.5.0"
        else:
            platform_version = "6.6.0"

        ch_headers = {
            "sec-ch-ua": f"{brand};v=\"{chrome_version}\", {brand_chromium};v=\"{chrome_version}\", {brand_not}",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": f'"{platform}"',
            "sec-ch-ua-platform-version": f'"{platform_version}"',
            "sec-ch-ua-full-version-list": f'{brand};v="{full_version}", {brand_chromium};v="{full_version}", {brand_not};v="24.0.0.0"',
            "sec-ch-ua-arch": '"x86"',
            "sec-ch-ua-bitness": '"64"',
            "sec-ch-ua-model": '""',
        }

        try:
            await context.set_extra_http_headers(ch_headers)
        except Exception:
            pass

    # Inject stealth JS before every page load
    await context.add_init_script(js)

    # Also inject on current page (in case already loaded)
    try:
        await page.evaluate(js)
    except Exception:
        pass
