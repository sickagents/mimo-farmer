"""Free proxy rotation from multiple sources."""

import random
import socket
import requests


# --- Proxy Sources ---

SOURCES = [
    {
        "name": "proxifly",
        "url": "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",
        "format": "lines",  # ip:port per line
    },
    {
        "name": "monosans",
        "url": "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "format": "lines",
    },
    {
        "name": "openproxylist",
        "url": "https://api.openproxylist.xyz/http.txt",
        "format": "lines",
    },
    {
        "name": "geonode",
        "url": "https://proxylist.geonode.com/api/proxy-list?protocols=http&limit=150&page=1&sort_by=lastChecked&sort_type=desc",
        "format": "json",  # {"data": [{"ip": "...", "port": "..."}, ...]}
    },
    {
        "name": "thespeedx",
        "url": "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "format": "lines",
    },
    {
        "name": "proxyscrape_v4",
        "url": "https://api.proxyscrape.com/v4/free-proxy-list/get",
        "params": {
            "request": "display_proxies",
            "proxy_format": "ipport",
            "format": "text",
            "protocol": "http",
            "timeout": 10000,
        },
        "format": "lines",
    },
    {
        "name": "proxyscrape_v2",
        "url": "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
        "format": "lines",
    },
]


def _fetch_source(source: dict, timeout: int = 15) -> list[str]:
    """Fetch proxies from a single source."""
    try:
        url = source["url"]
        params = source.get("params")
        r = requests.get(url, params=params, timeout=timeout)
        r.raise_for_status()

        if source["format"] == "json":
            data = r.json()
            entries = data.get("data", [])
            return [f"{e['ip']}:{e['port']}" for e in entries if "ip" in e and "port" in e]
        else:
            return [p.strip().replace("http://", "").replace("https://", "") for p in r.text.strip().split('\n') if p.strip() and ':' in p]
    except Exception as e:
        print(f"  [proxy] {source['name']}: {e}")
        return []


def fetch_all_proxies(timeout: int = 15) -> list[str]:
    """Fetch proxies from all sources, deduplicate, shuffle."""
    all_proxies = []
    for src in SOURCES:
        proxies = _fetch_source(src, timeout)
        print(f"  [proxy] {src['name']}: {len(proxies)} proxies")
        all_proxies.extend(proxies)

    # Deduplicate
    seen = set()
    unique = []
    for p in all_proxies:
        if p not in seen:
            seen.add(p)
            unique.append(p)

    random.shuffle(unique)
    return unique


def check_proxy(proxy: str, timeout: int = 5) -> bool:
    """Quick socket connectivity check."""
    try:
        host, port = proxy.split(':')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, int(port)))
        sock.close()
        return result == 0
    except Exception:
        return False


def get_working_proxy(proxies: list[str], max_attempts: int = 20) -> str | None:
    """Pick random proxy and verify socket connectivity."""
    random.shuffle(proxies)
    for proxy in proxies[:max_attempts]:
        if check_proxy(proxy):
            return proxy
    return None


def get_proxy_for_browser(timeout: int = 15) -> dict | None:
    """Get proxy dict for Patchright launch: {"server": "http://ip:port"}."""
    proxies = fetch_all_proxies(timeout)
    if not proxies:
        return None

    working = get_working_proxy(proxies)
    if not working:
        return None

    proxy_url = f"http://{working}"
    print(f"  [proxy] Using: {working}")
    return {"server": proxy_url}


def check_proxy_health(proxy: str, timeout: int = 5) -> bool:
    """Full proxy health check — socket connectivity + HTTP test."""
    if not check_proxy(proxy, timeout):
        return False
    try:
        r = requests.get(
            "http://httpbin.org/ip",
            proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"},
            timeout=timeout + 3,
        )
        return r.status_code == 200
    except Exception:
        # Socket OK but HTTP failed — still usable, many free proxies
        # pass socket but fail HTTP. Accept socket-only check.
        return True


def get_n_proxies(n: int, timeout: int = 15) -> list[str]:
    """Fetch proxies and return up to N working ones.

    Used by parallel worker pool to assign one proxy per worker.
    Returns list of "ip:port" strings (working only).
    """
    all_proxies = fetch_all_proxies(timeout)
    if not all_proxies:
        return []

    working: list[str] = []
    # Shuffle for randomness, then check connectivity
    random.shuffle(all_proxies)
    for proxy in all_proxies:
        if len(working) >= n:
            break
        if check_proxy(proxy, timeout=5):
            working.append(proxy)

    return working
