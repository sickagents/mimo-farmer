"""Parse mimo-farmer batch files into account and batch records."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, date
from io import StringIO
from pathlib import Path
from typing import Any

from mimo_farmer.config import ACCOUNTS_DIR


@dataclass
class Account:
    account_id: str
    batch_id: str
    batch_file: str
    position: str
    email: str
    password: str
    api_key: str
    referral: str
    own_referral: str
    balance: str
    balance_value: float
    risk_control: bool
    status: str
    created_at: str
    email_link: str


@dataclass
class Batch:
    batch_id: str
    filename: str
    path: str
    created_at: str
    modified_at: str
    referral_code: str
    mode: str
    total_accounts: int
    success_count: int
    fail_count: int
    is_siklus: bool
    total_balance: float


SECTION_RE = re.compile(r"^\[(?P<name>[^\]]+)\]\s*$")
KEY_RE = re.compile(r"^(?P<key>[A-Za-z][A-Za-z -]*):\s*(?P<value>.*)$")


def accounts_dir() -> Path:
    return Path(ACCOUNTS_DIR)


def list_batch_files() -> list[Path]:
    root = accounts_dir()
    if not root.exists():
        return []
    return sorted(root.glob("batch*.txt"), key=lambda p: p.stat().st_mtime, reverse=True)


def parse_all() -> tuple[list[Batch], list[Account]]:
    batches: list[Batch] = []
    accounts: list[Account] = []
    for path in list_batch_files():
        batch, batch_accounts = parse_batch_file(path)
        batches.append(batch)
        accounts.extend(batch_accounts)
    accounts.sort(key=lambda a: (a.created_at, a.batch_file, a.position), reverse=True)
    return batches, accounts


def parse_batch_file(path: Path) -> tuple[Batch, list[Account]]:
    stat = path.stat()
    created = _created_from_filename(path.name) or datetime.fromtimestamp(stat.st_ctime)
    modified = datetime.fromtimestamp(stat.st_mtime)
    batch_id = path.stem
    sections = _parse_sections(path)

    accounts: list[Account] = []
    for index, (section, data) in enumerate(sections, 1):
        email = _first(data, "mail", "email")
        if not email:
            continue
        balance = _first(data, "balance") or "$0.00"
        risk_control = _parse_bool(_first(data, "risk-control", "risk_control"))
        status = "risk_controlled" if risk_control else "active"
        account = Account(
            account_id=f"{batch_id}:{section}",
            batch_id=batch_id,
            batch_file=path.name,
            position=section,
            email=email,
            password=_first(data, "pw", "password") or "",
            api_key=_first(data, "api-key", "api_key") or "",
            referral=_clean_referral(_first(data, "referral") or ""),
            own_referral=_clean_referral(_first(data, "own-referral", "own_referral") or ""),
            balance=balance,
            balance_value=_parse_money(balance),
            risk_control=risk_control,
            status=status,
            created_at=created.strftime("%Y-%m-%d %H:%M:%S"),
            email_link=_first(data, "link", "email-link", "email_link") or f"https://generator.email/{email}",
        )
        accounts.append(account)

    referral_values = [a.referral for a in accounts if a.referral and a.referral != "-"]
    own_referral_values = [a.own_referral for a in accounts if a.own_referral and a.own_referral != "-"]
    is_siklus = bool(own_referral_values) or "siklus" in path.name.lower()
    mode = "siklus" if is_siklus else "batch"
    referral_code = referral_values[0] if referral_values else (own_referral_values[0] if own_referral_values else "")
    success_count = sum(1 for a in accounts if a.api_key and not a.risk_control)
    fail_count = max(0, len(accounts) - success_count)

    batch = Batch(
        batch_id=batch_id,
        filename=path.name,
        path=str(path),
        created_at=created.strftime("%Y-%m-%d %H:%M:%S"),
        modified_at=modified.strftime("%Y-%m-%d %H:%M:%S"),
        referral_code=referral_code,
        mode=mode,
        total_accounts=len(accounts),
        success_count=success_count,
        fail_count=fail_count,
        is_siklus=is_siklus,
        total_balance=round(sum(a.balance_value for a in accounts), 2),
    )
    return batch, accounts


def get_accounts(
    search: str = "",
    status: str = "",
    referral: str = "",
    min_balance: float | None = None,
    max_balance: float | None = None,
    date_from: str = "",
    date_to: str = "",
    sort: str = "created_at",
    direction: str = "desc",
) -> list[Account]:
    _, accounts = parse_all()
    search_lower = search.lower().strip()
    if search_lower:
        accounts = [a for a in accounts if search_lower in a.email.lower() or search_lower in a.referral.lower() or search_lower in a.own_referral.lower()]
    if status:
        accounts = [a for a in accounts if a.status == status]
    if referral:
        referral_lower = referral.lower()
        accounts = [a for a in accounts if referral_lower in a.referral.lower() or referral_lower in a.own_referral.lower()]
    if min_balance is not None:
        accounts = [a for a in accounts if a.balance_value >= min_balance]
    if max_balance is not None:
        accounts = [a for a in accounts if a.balance_value <= max_balance]
    if date_from:
        start = _parse_date(date_from)
        if start:
            accounts = [a for a in accounts if _account_date(a) >= start]
    if date_to:
        end = _parse_date(date_to)
        if end:
            accounts = [a for a in accounts if _account_date(a) <= end]

    reverse = direction.lower() != "asc"
    sort_key = sort if sort in Account.__dataclass_fields__ else "created_at"
    accounts.sort(key=lambda a: getattr(a, sort_key), reverse=reverse)
    return accounts


def get_stats() -> dict[str, Any]:
    batches, accounts = parse_all()
    today = date.today()
    total = len(accounts)
    today_count = sum(1 for a in accounts if _account_date(a) == today)
    active = sum(1 for a in accounts if a.status == "active")
    risk = sum(1 for a in accounts if a.risk_control)
    total_balance = round(sum(a.balance_value for a in accounts), 2)
    success_rate = round((active / total) * 100, 1) if total else 0.0
    recent = [asdict(a) for a in accounts[:10]]
    return {
        "total_accounts": total,
        "accounts_today": today_count,
        "total_balance": total_balance,
        "success_rate": success_rate,
        "risk_controlled": risk,
        "total_batches": len(batches),
        "recent_activity": recent,
    }


def paginate(items: list[Any], page: int, page_size: int) -> dict[str, Any]:
    page = max(1, page)
    page_size = max(1, min(200, page_size))
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": [asdict(item) if hasattr(item, "__dataclass_fields__") else item for item in items[start:end]],
        "page": page,
        "page_size": page_size,
        "total": len(items),
        "pages": (len(items) + page_size - 1) // page_size,
    }


def export_accounts(accounts: list[Account], fmt: str) -> tuple[str, str, str]:
    fmt = fmt.lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if fmt == "json":
        return json.dumps([asdict(a) for a in accounts], indent=2), f"mimo_accounts_{timestamp}.json", "application/json"
    if fmt == "csv":
        out = StringIO()
        writer = csv.DictWriter(out, fieldnames=list(Account.__dataclass_fields__.keys()))
        writer.writeheader()
        for account in accounts:
            writer.writerow(asdict(account))
        return out.getvalue(), f"mimo_accounts_{timestamp}.csv", "text/csv"
    if fmt == "txt":
        lines: list[str] = []
        for i, account in enumerate(accounts, 1):
            lines.extend([
                f"[{account.position if account.position else i}]",
                f"Mail: {account.email}",
                f"Link: {account.email_link}",
                f"Pw: {account.password}",
                f"Api-Key: {account.api_key}",
            ])
            if account.referral:
                lines.append(f"Referral: {account.referral}")
            if account.own_referral:
                lines.append(f"Own-Referral: {account.own_referral}")
            if account.balance:
                lines.append(f"Balance: {account.balance}")
            lines.append("")
        return "\n".join(lines), f"mimo_accounts_{timestamp}.txt", "text/plain"
    raise ValueError("format must be json, csv, or txt")


def _parse_sections(path: Path) -> list[tuple[str, dict[str, str]]]:
    sections: list[tuple[str, dict[str, str]]] = []
    current_name: str | None = None
    current: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        section_match = SECTION_RE.match(stripped)
        if section_match:
            if current_name is not None:
                sections.append((current_name, current))
            current_name = section_match.group("name")
            current = {}
            continue
        key_match = KEY_RE.match(stripped)
        if key_match and current_name is not None:
            key = _normalize_key(key_match.group("key"))
            current[key] = key_match.group("value").strip()
    if current_name is not None:
        sections.append((current_name, current))
    return sections


def _first(data: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = data.get(_normalize_key(key))
        if value is not None:
            return value.strip()
    return ""


def _normalize_key(key: str) -> str:
    return key.strip().lower().replace("_", "-")


def _clean_referral(value: str) -> str:
    value = value.strip()
    if value.upper() in {"N/A", "NONE", "NULL"}:
        return ""
    return value


def _parse_money(value: str) -> float:
    match = re.search(r"-?\d+(?:\.\d+)?", value or "")
    return float(match.group(0)) if match else 0.0


def _parse_bool(value: str) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "y", "risk_control", "risk_controlled"}


def _created_from_filename(filename: str) -> datetime | None:
    match = re.search(r"(20\d{6})[_-](\d{6})", filename)
    if not match:
        return None
    try:
        return datetime.strptime("".join(match.groups()), "%Y%m%d%H%M%S")
    except ValueError:
        return None


def _parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _account_date(account: Account) -> date:
    try:
        return datetime.strptime(account.created_at, "%Y-%m-%d %H:%M:%S").date()
    except ValueError:
        return date.min
