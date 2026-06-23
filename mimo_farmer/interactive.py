"""Interactive CLI wizard for mimo-farmer."""

from __future__ import annotations

from argparse import Namespace


try:
    from InquirerPy import inquirer
except Exception:  # pragma: no cover - fallback for missing optional dep
    inquirer = None


def _select(message: str, choices: list[str], default: str | None = None) -> str:
    if inquirer:
        return inquirer.select(message=message, choices=choices, default=default or choices[0]).execute()
    print(f"\n{message}")
    for i, choice in enumerate(choices, 1):
        marker = "*" if choice == default else " "
        print(f"  {i}. {choice} {marker}")
    while True:
        raw = input("Choose: ").strip()
        if not raw and default:
            return default
        try:
            return choices[int(raw) - 1]
        except Exception:
            print("Invalid choice")


def _text(message: str, default: str = "") -> str:
    if inquirer:
        return inquirer.text(message=message, default=default).execute()
    raw = input(f"{message} [{default}]: ").strip()
    return raw or default


def _confirm(message: str, default: bool = True) -> bool:
    if inquirer:
        return inquirer.confirm(message=message, default=default).execute()
    suffix = "Y/n" if default else "y/N"
    raw = input(f"{message} [{suffix}]: ").strip().lower()
    if not raw:
        return default
    return raw in {"y", "yes", "ya"}


def _run_create(**kwargs) -> int:
    from mimo_farmer.cli import cmd_create

    args = Namespace(
        command="create",
        count=kwargs.get("count"),
        referral=kwargs.get("referral"),
        captcha=kwargs.get("captcha", "manual"),
        proxy=kwargs.get("proxy", False),
        ip_rotate=kwargs.get("ip_rotate"),
        cdp_url=kwargs.get("cdp_url", "http://localhost:9222"),
        no_cdp=kwargs.get("no_cdp", False),
        platform_signup=kwargs.get("platform_signup", False),
        parallel=kwargs.get("parallel", 1),
        continuous=kwargs.get("continuous", False),
        siklus=kwargs.get("siklus", False),
        target_balance=kwargs.get("target_balance"),
    )
    return cmd_create(args)


def _auto_farm() -> int:
    target = float(_text("Target balance", "42"))
    captcha = _select("Captcha mode", ["manual", "auto", "semi-auto"], "manual")
    browser = _select("Browser mode", ["CDP (real Chrome)", "Patchright (--no-cdp)"], "CDP (real Chrome)")
    platform_signup = _confirm("Start from platform.xiaomimimo.com first?", False)
    ip_choice = _select("IP rotation", ["manual VPN/hotspot", "ADB airplane", "ADB data", "free proxy"], "manual VPN/hotspot")

    no_cdp = browser.startswith("Patchright")
    ip_rotate = None
    proxy = False
    if ip_choice == "ADB airplane":
        ip_rotate = "adb"
    elif ip_choice == "ADB data":
        ip_rotate = "data"
    elif ip_choice == "free proxy":
        proxy = True

    print("\nCommand equivalent:")
    parts = ["mimo create", f"--target-balance {target:g}", f"--captcha {captcha}"]
    if no_cdp:
        parts.append("--no-cdp")
    if platform_signup:
        parts.append("--platform-signup")
    if ip_rotate:
        parts.append(f"--ip-rotate {ip_rotate}")
    if proxy:
        parts.append("--proxy")
    print(" ".join(parts))

    if not _confirm("Start now?", True):
        return 0
    return _run_create(
        target_balance=target,
        captcha=captcha,
        no_cdp=no_cdp,
        platform_signup=platform_signup,
        ip_rotate=ip_rotate,
        proxy=proxy,
    )


def _single_or_multi() -> int:
    referral = _text("Referral code", "M57JCH").strip().upper()
    count = int(_text("Account count", "1"))
    captcha = _select("Captcha mode", ["manual", "auto", "semi-auto"], "manual")
    browser = _select("Browser mode", ["CDP (real Chrome)", "Patchright (--no-cdp)"], "CDP (real Chrome)")
    platform_signup = _confirm("Start from platform.xiaomimimo.com first?", False)
    if not _confirm("Start now?", True):
        return 0
    return _run_create(
        referral=referral,
        count=count,
        captcha=captcha,
        no_cdp=browser.startswith("Patchright"),
        platform_signup=platform_signup,
    )


def _siklus() -> int:
    count = int(_text("Siklus count", "1"))
    captcha = _select("Captcha mode", ["manual", "auto", "semi-auto"], "manual")
    browser = _select("Browser mode", ["CDP (real Chrome)", "Patchright (--no-cdp)"], "CDP (real Chrome)")
    if not _confirm("Start now?", True):
        return 0
    return _run_create(
        siklus=True,
        count=count,
        captcha=captcha,
        no_cdp=browser.startswith("Patchright"),
    )


def run_interactive() -> int:
    print("\nMiMo Farmer Interactive\n")
    while True:
        mode = _select(
            "Mode",
            [
                "Auto-farm target balance",
                "Single / multiple accounts",
                "Siklus",
                "Accounts list",
                "Export accounts",
                "Exit",
            ],
            "Auto-farm target balance",
        )
        if mode == "Auto-farm target balance":
            return _auto_farm()
        if mode == "Single / multiple accounts":
            return _single_or_multi()
        if mode == "Siklus":
            return _siklus()
        if mode == "Accounts list":
            from mimo_farmer.cli import cmd_accounts
            return cmd_accounts(Namespace())
        if mode == "Export accounts":
            from mimo_farmer.cli import cmd_export
            return cmd_export(Namespace(format="json", output=None))
        return 0
