"""Free public CLI for MiMo account creation.

Only exposes referral + count flow:
  mimo create --referral CODE --count N
  mimo create --referral CODE --count N --workers 20
"""

from __future__ import annotations

import argparse
import asyncio
import os
import random
import time

from mimo_farmer import __version__
from mimo_farmer.config import ACCOUNTS_DIR, CAPTCHA_MODE_DEFAULT


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mimo",
        description="MiMo free CLI — create accounts with referral + count",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  mimo create --referral ABC123 --count 5
  mimo create -r ABC123 -n 5
  mimo create -r ABC123 -n 30 --workers 20    # parallel mode
""",
    )
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")

    sub = parser.add_subparsers(dest="command", help="command to run")
    p_create = sub.add_parser(
        "create",
        help="Create MiMo accounts",
        description="Create accounts using one referral code and account count",
    )
    p_create.add_argument(
        "--referral",
        "-r",
        type=str,
        default=None,
        metavar="CODE",
        help="Referral code to use",
    )
    p_create.add_argument(
        "--count",
        "-n",
        type=int,
        default=None,
        metavar="N",
        help="Number of accounts to create",
    )
    p_create.add_argument(
        "--workers",
        "-w",
        type=int,
        default=1,
        metavar="W",
        help="Number of parallel workers (default: 1, max: 50). "
             "Each worker gets own browser + proxy. "
             "Recommended: 20-30 for 160 vCPU VPS.",
    )
    return parser


def cmd_create(args) -> int:
    referral = args.referral
    count = args.count
    workers = max(1, min(args.workers, 50))

    if not referral:
        while True:
            referral = input("Kode referral: ").strip().upper()
            if referral:
                break
            print("  [!] Kode referral wajib diisi!")
    else:
        referral = referral.strip().upper()

    if not count or count < 1:
        while True:
            user_input = input("Mau bikin berapa akun? ").strip()
            try:
                count = int(user_input)
                if count > 0:
                    break
                print("  [!] Minimal 1 akun!")
            except ValueError:
                print("  [!] Masukkan angka yang valid!")

    print(f"\nMiMo CLI v{__version__}")
    print(f"Creating {count} account(s) | Referral: {referral}")
    if workers > 1:
        print(f"Parallel mode: {workers} workers")
    print()

    if workers > 1:
        return _run_parallel(count, referral, workers)
    return _run_sequential(count, referral)


def _run_sequential(count: int, referral: str) -> int:
    from mimo_farmer.creator import create_account_with_retry

    results = []
    for i in range(count):
        if i > 0:
            cooldown = random.randint(1, 10)
            print(f"\n  Cooldown {cooldown}s between accounts...")
            time.sleep(cooldown)

        if count > 1:
            print(f"\n{'#' * 60}")
            print(f"  Account {i + 1}/{count}")
            print(f"{'#' * 60}\n")

        try:
            result = asyncio.run(
                create_account_with_retry(
                    referral_code=referral,
                    captcha_mode=CAPTCHA_MODE_DEFAULT,
                    account_num=i + 1,
                )
            )
            results.append(result)
        except Exception as exc:
            print(f"  [!] Error: {exc}")
            results.append(None)
            break

        if result and (result.get("risk_control") or result.get("ip_blocked")):
            reason = "risk control" if result.get("risk_control") else "IP blocked (automated queries)"
            print(f"\n  [!] {reason.upper()} detected on account {i + 1}!")
            print("  [!] Stop. Change IP/referral before retry.")
            break

        if result is None:
            print(f"\n  [!] Account {i + 1} failed — stopping batch.")
            break

    success = sum(1 for r in results if r is not None and r.get("api_key"))
    _save_combined(results)
    print(f"\n{'=' * 60}")
    print(f"  Summary: {success}/{count} accounts created")
    print(f"{'=' * 60}")
    return 0 if success > 0 else 1


def _run_parallel(count: int, referral: str, workers: int) -> int:
    """Run account creation in parallel using asyncio.gather().

    Each worker gets own browser + proxy. Semaphore limits concurrency.
    One worker failure does not stop others.
    """
    from mimo_farmer.parallel import ParallelWorkerPool

    # Cap concurrency to workers count (don't spawn more semaphores than workers)
    max_concurrent = min(workers, count)

    pool = ParallelWorkerPool(
        num_workers=workers,
        referral_code=referral,
        captcha_mode=CAPTCHA_MODE_DEFAULT,
        max_concurrent=max_concurrent,
    )

    print(f"  Launching {workers} parallel workers for {count} accounts...")
    print(f"  Max concurrent browsers: {max_concurrent}")

    results_raw = asyncio.run(pool.run(count))

    # Convert WorkerResult to dict format compatible with _save_combined
    results = []
    for wr in results_raw:
        if wr.success and wr.data:
            results.append(wr.data)
        else:
            results.append(wr.data)  # May be None or partial

    print(pool.summary())

    success = sum(1 for r in results if r is not None and r.get("api_key"))
    _save_combined(results)
    print(f"\n{'=' * 60}")
    print(f"  Summary: {success}/{count} accounts created")
    print(f"{'=' * 60}")
    return 0 if success > 0 else 1


def _save_combined(results: list) -> None:
    valid = [r for r in results if r is not None and r.get("balance") and r.get("api_key")]
    if not valid:
        return

    os.makedirs(ACCOUNTS_DIR, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = os.path.join(ACCOUNTS_DIR, f"batch_{ts}.txt")
    date_str = time.strftime("%d/%m/%Y")

    lines = []
    total_balance = 0.0
    for i, creds in enumerate(valid, 1):
        balance = creds.get("balance", "$0.00")
        try:
            total_balance += float(str(balance).replace("$", "").strip() or 0)
        except ValueError:
            pass

        lines.extend(
            [
                f"[{i}] | {date_str}",
                f"Mail: {creds['email']}",
                f"Link: https://generator.email/{creds['email']}",
                f"Pw: {creds['password']}",
                f"Api-Key: {creds.get('api_key', 'N/A')}",
                f"Balance: {balance}",
                "",
            ]
        )

    lines.append(f"Total Balance: ${total_balance:.2f}")
    lines.extend(["", "Apikey:"])
    lines.extend(str(creds.get("api_key", "N/A")) for creds in valid)

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n  Combined credentials saved: {path}")
    _save_apikeys(valid)


def _save_apikeys(valid: list) -> None:
    """Save only API keys, one per line, to apikey.txt."""
    apikeys = [str(r.get("api_key", "")) for r in valid if r.get("api_key")]
    if not apikeys:
        return

    os.makedirs(ACCOUNTS_DIR, exist_ok=True)
    path = os.path.join(ACCOUNTS_DIR, "apikey.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(apikeys) + "\n")

    print(f"  API keys saved: {path} ({len(apikeys)} keys)")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "create":
        return cmd_create(args)

    parser.print_help()
    return 0
