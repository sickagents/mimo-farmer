"""FastAPI handlers for mimo-farmer Web UI."""

from __future__ import annotations

import asyncio
import contextlib
import io
import os
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from mimo_farmer import __version__
from mimo_farmer.config import DEFAULT_PASSWORD, DEFAULT_REFERRAL_CODE, EMAIL_DOMAINS, ACCOUNTS_DIR
from mimo_farmer.web import batch_parser
from mimo_farmer.web.ws_manager import manager

router = APIRouter(prefix="/api")


class CreateRequest(BaseModel):
    mode: str = Field(default="single", pattern="^(single|batch|continuous|parallel|siklus)$")
    referral: str = ""
    count: int = Field(default=1, ge=1, le=200)
    fast: bool = False
    parallel: int = Field(default=1, ge=1, le=10)
    password: str = ""


class SettingsRequest(BaseModel):
    default_referral: str = ""
    default_password: str = ""
    fast_default: bool = False
    ip_rotation_interval: int = Field(default=5, ge=1, le=100)
    headless: bool = False
    email_domains: list[str] = Field(default_factory=list)


@dataclass
class JobState:
    job_id: str
    mode: str
    referral: str
    count: int
    fast: bool
    parallel: int
    status: str = "pending"
    started_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    completed_at: str = ""
    error_message: str = ""
    total_created: int = 0
    total_failed: int = 0
    cancel_requested: bool = False
    logs: list[str] = field(default_factory=list)


SETTINGS: dict[str, Any] = {
    "default_referral": DEFAULT_REFERRAL_CODE,
    "default_password": DEFAULT_PASSWORD,
    "fast_default": False,
    "ip_rotation_interval": 5,
    "headless": False,
    "email_domains": list(EMAIL_DOMAINS),
}
JOB: JobState | None = None
JOB_LOCK = threading.Lock()
MAIN_LOOP: asyncio.AbstractEventLoop | None = None

STEP_NAMES = {
    1: "Signup",
    2: "Form",
    3: "CAPTCHA",
    4: "OTP Page",
    5: "OTP Fetch",
    6: "OTP Entry",
    7: "Terms",
    8: "Balance",
    9: "Referral",
    10: "Risk Control",
    11: "Balance Verify",
    12: "API Key",
    13: "Save",
    14: "Logout",
}


@router.get("/stats")
def stats() -> dict[str, Any]:
    data = batch_parser.get_stats()
    data["version"] = __version__
    data["job"] = _job_payload()
    return data


@router.get("/accounts")
def accounts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str = "",
    status: str = "",
    referral: str = "",
    min_balance: float | None = None,
    max_balance: float | None = None,
    date_from: str = "",
    date_to: str = "",
    sort: str = "created_at",
    direction: str = "desc",
) -> dict[str, Any]:
    items = batch_parser.get_accounts(search, status, referral, min_balance, max_balance, date_from, date_to, sort, direction)
    return batch_parser.paginate(items, page, page_size)


@router.get("/batches")
def batches() -> dict[str, Any]:
    batch_items, _ = batch_parser.parse_all()
    return {"items": [asdict(batch) for batch in batch_items], "total": len(batch_items)}


@router.get("/batches/{batch_id}")
def batch_detail(batch_id: str) -> dict[str, Any]:
    batch_items, account_items = batch_parser.parse_all()
    for batch in batch_items:
        if batch.batch_id == batch_id:
            return {
                "batch": asdict(batch),
                "accounts": [asdict(a) for a in account_items if a.batch_id == batch_id],
            }
    raise HTTPException(status_code=404, detail="Batch not found")


@router.post("/create")
def create(request: CreateRequest) -> dict[str, Any]:
    global JOB
    with JOB_LOCK:
        if JOB and JOB.status == "running":
            raise HTTPException(status_code=409, detail="Account creation job already running")
        referral = request.referral.strip().upper() or SETTINGS["default_referral"]
        if request.mode not in {"siklus", "single"} and not referral:
            raise HTTPException(status_code=400, detail="Referral code required")
        count = 1 if request.mode == "single" else request.count
        if request.mode == "siklus":
            count = request.count
        parallel = request.parallel if request.mode == "parallel" else 1
        JOB = JobState(
            job_id=str(uuid.uuid4()),
            mode=request.mode,
            referral=referral,
            count=count,
            fast=request.fast,
            parallel=parallel,
        )
        job = JOB

    thread = threading.Thread(target=_run_job_thread, args=(job, request.password or SETTINGS["default_password"]), daemon=True)
    thread.start()
    return {"job": asdict(job)}


@router.post("/create/cancel")
def cancel_create() -> dict[str, Any]:
    with JOB_LOCK:
        if not JOB or JOB.status not in {"pending", "running"}:
            raise HTTPException(status_code=404, detail="No running job")
        JOB.cancel_requested = True
    _broadcast_sync({"type": "job_cancel_requested", "data": _job_payload()})
    return {"job": _job_payload()}


@router.get("/job")
def job() -> dict[str, Any]:
    return {"job": _job_payload()}


@router.get("/export")
def export(
    format: str = Query("json", pattern="^(json|txt|csv)$"),
    search: str = "",
    status: str = "",
    referral: str = "",
    min_balance: float | None = None,
    max_balance: float | None = None,
    date_from: str = "",
    date_to: str = "",
) -> Response:
    items = batch_parser.get_accounts(search, status, referral, min_balance, max_balance, date_from, date_to)
    body, filename, media_type = batch_parser.export_accounts(items, format)
    return Response(
        content=body,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/settings")
def get_settings() -> dict[str, Any]:
    return {"settings": SETTINGS, "accounts_dir": ACCOUNTS_DIR, "version": __version__}


@router.put("/settings")
def update_settings(request: SettingsRequest) -> dict[str, Any]:
    SETTINGS.update({
        "default_referral": request.default_referral.strip().upper(),
        "default_password": request.default_password,
        "fast_default": request.fast_default,
        "ip_rotation_interval": request.ip_rotation_interval,
        "headless": request.headless,
        "email_domains": [d.strip() for d in request.email_domains if d.strip()],
    })
    return {"settings": SETTINGS}


def set_main_loop(loop: asyncio.AbstractEventLoop) -> None:
    global MAIN_LOOP
    MAIN_LOOP = loop


def _run_job_thread(job: JobState, password: str) -> None:
    _set_job_status(job, "running")
    _broadcast_sync({"type": "job_started", "data": asdict(job)})
    try:
        if job.mode == "siklus":
            results = _run_siklus_job(job, password)
        elif job.mode == "continuous":
            results = _run_continuous_job(job, password)
        else:
            results = _run_standard_job(job, password)
        if job.cancel_requested:
            _set_job_status(job, "cancelled")
        else:
            _set_job_status(job, "completed")
        job.total_created = sum(1 for r in results if r and not r.get("risk_control"))
        job.total_failed = sum(1 for r in results if not r or r.get("risk_control"))
        if results:
            _save_batch(results, "siklus" if job.mode == "siklus" else job.referral)
        _broadcast_sync({
            "type": "job_complete",
            "data": {"job_id": job.job_id, "total_created": job.total_created, "total_failed": job.total_failed, "status": job.status},
        })
    except Exception as exc:
        job.error_message = str(exc)
        _set_job_status(job, "failed")
        _broadcast_sync({"type": "job_error", "data": {"job_id": job.job_id, "message": str(exc)}})


def _run_standard_job(job: JobState, password: str) -> list[dict[str, Any] | None]:
    results: list[dict[str, Any] | None] = []
    for i in range(job.count):
        if job.cancel_requested:
            break
        result = _create_one(job, job.referral, password, i + 1, skip_referral=False)
        results.append(result)
        if result:
            _broadcast_sync({"type": "account_created", "data": _public_account(result)})
        if result and result.get("risk_control"):
            break
    return results


def _run_continuous_job(job: JobState, password: str) -> list[dict[str, Any] | None]:
    results: list[dict[str, Any] | None] = []
    account_num = 0
    while not job.cancel_requested:
        account_num += 1
        result = _create_one(job, job.referral, password, account_num, skip_referral=False)
        results.append(result)
        if result:
            _broadcast_sync({"type": "account_created", "data": _public_account(result)})
        if result and result.get("risk_control"):
            break
    return results


def _run_siklus_job(job: JobState, password: str) -> list[dict[str, Any] | None]:
    results: list[dict[str, Any] | None] = []
    children_per_siklus = 5
    account_num = 0
    for siklus_num in range(1, job.count + 1):
        if job.cancel_requested:
            break
        account_num += 1
        _emit_log(job, 1, f"Siklus {siklus_num}: creating main account")
        main = _create_one(job, "", password, account_num, skip_referral=True)
        results.append(main)
        if main:
            _broadcast_sync({"type": "account_created", "data": _public_account(main)})
        if not main or main.get("risk_control") or not main.get("own_referral"):
            continue
        for child in range(1, children_per_siklus + 1):
            if job.cancel_requested:
                break
            account_num += 1
            _emit_log(job, 1, f"Siklus {siklus_num}: creating child {child}/{children_per_siklus}")
            result = _create_one(job, main["own_referral"], password, account_num, skip_referral=False)
            results.append(result)
            if result:
                _broadcast_sync({"type": "account_created", "data": _public_account(result)})
            if result and result.get("risk_control"):
                break
    return results


def _create_one(job: JobState, referral: str, password: str, account_num: int, skip_referral: bool) -> dict[str, Any] | None:
    from mimo_farmer.creator import create_account

    async def run() -> dict[str, Any] | None:
        return await create_account(referral_code=referral, password=password, fast=job.fast, account_num=account_num, skip_referral=skip_referral)

    buffer = io.StringIO()
    with contextlib.redirect_stdout(_ProgressWriter(job, buffer)):
        return asyncio.run(run())


def _save_batch(results: list[dict[str, Any] | None], referral: str) -> None:
    valid = [r for r in results if r]
    if not valid:
        return
    os.makedirs(ACCOUNTS_DIR, exist_ok=True)
    path = os.path.join(ACCOUNTS_DIR, f"batch_{time.strftime('%Y%m%d_%H%M%S')}.txt")
    lines: list[str] = []
    for i, creds in enumerate(valid, 1):
        position = "MAIN" if creds.get("own_referral") else str(i)
        lines.extend([
            f"[{position}]",
            f"Mail: {creds.get('email', '')}",
            f"Link: {creds.get('email_link', 'https://generator.email/' + creds.get('email', ''))}",
            f"Pw: {creds.get('password', '')}",
            f"Api-Key: {creds.get('api_key') or ''}",
            f"Referral: {creds.get('referral', referral)}",
        ])
        if creds.get("own_referral"):
            lines.append(f"Own-Referral: {creds.get('own_referral')}")
        lines.extend([
            f"Balance: {creds.get('balance', '')}",
            f"Risk-Control: {bool(creds.get('risk_control'))}",
            "",
        ])
    with open(path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))


def _set_job_status(job: JobState, status: str) -> None:
    job.status = status
    if status in {"completed", "failed", "cancelled"}:
        job.completed_at = time.strftime("%Y-%m-%d %H:%M:%S")


def _emit_log(job: JobState, step: int, line: str) -> None:
    line = line.rstrip()
    if not line:
        return
    job.logs.append(line)
    job.logs = job.logs[-500:]
    step_number = _infer_step(line, step)
    _broadcast_sync({
        "type": "progress",
        "data": {
            "job_id": job.job_id,
            "step": step_number,
            "step_name": STEP_NAMES.get(step_number, "Progress"),
            "status": "running",
            "message": line,
            "progress_pct": max(0, min(100, round((step_number / 14) * 100))),
            "log": line,
        },
    })


def _infer_step(line: str, fallback: int) -> int:
    stripped = line.strip()
    if stripped.startswith("["):
        end = stripped.find("]")
        if end > 1 and stripped[1:end].replace(".", "").isdigit():
            try:
                number = int(float(stripped[1:end]))
                return max(1, min(14, number))
            except ValueError:
                pass
    lower = stripped.lower()
    if "captcha" in lower:
        return 3
    if "otp" in lower:
        return 5
    if "api key" in lower:
        return 12
    if "risk control" in lower:
        return 10
    if "balance" in lower:
        return 11
    if "saving" in lower:
        return 13
    if "logout" in lower:
        return 14
    return fallback


def _broadcast_sync(message: dict[str, Any]) -> None:
    if MAIN_LOOP and MAIN_LOOP.is_running():
        asyncio.run_coroutine_threadsafe(manager.broadcast(message), MAIN_LOOP)


def _job_payload() -> dict[str, Any] | None:
    with JOB_LOCK:
        return asdict(JOB) if JOB else None


def _public_account(result: dict[str, Any]) -> dict[str, Any]:
    api_key = result.get("api_key") or ""
    return {
        "email": result.get("email", ""),
        "balance": result.get("balance", ""),
        "api_key": api_key[:12] + "..." + api_key[-5:] if len(api_key) > 20 else api_key,
        "risk_control": bool(result.get("risk_control")),
    }


class _ProgressWriter(io.TextIOBase):
    def __init__(self, job: JobState, buffer: io.StringIO) -> None:
        self.job = job
        self.buffer = buffer
        self._pending = ""

    def write(self, text: str) -> int:
        self.buffer.write(text)
        self._pending += text
        while "\n" in self._pending:
            line, self._pending = self._pending.split("\n", 1)
            _emit_log(self.job, 1, line)
        return len(text)

    def flush(self) -> None:
        if self._pending.strip():
            _emit_log(self.job, 1, self._pending)
            self._pending = ""
