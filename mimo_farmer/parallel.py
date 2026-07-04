"""Parallel worker pool for high-CPU VPS account creation.

Uses asyncio.gather() with Semaphore to limit concurrent browser instances.
Each worker gets independent browser + proxy + captcha solver.
"""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import Any

from mimo_farmer.proxy_manager import fetch_all_proxies, get_n_proxies, check_proxy


@dataclass
class WorkerResult:
    """Result from a single worker."""
    worker_id: int
    account_num: int
    success: bool
    data: dict | None = None
    error: str | None = None
    elapsed: float = 0.0


@dataclass
class WorkerPoolStats:
    """Thread-safe progress tracking."""
    total: int = 0
    completed: int = 0
    succeeded: int = 0
    failed: int = 0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def record_success(self):
        async with self._lock:
            self.completed += 1
            self.succeeded += 1

    async def record_failure(self):
        async with self._lock:
            self.completed += 1
            self.failed += 1

    @property
    def remaining(self) -> int:
        return self.total - self.completed


class ParallelWorkerPool:
    """Manages parallel account creation workers.

    Each worker:
    - Own Playwright browser instance
    - Own proxy (round-robin from pool)
    - Own captcha solver session
    - Independent error handling (one fail ≠ all fail)
    """

    def __init__(
        self,
        num_workers: int,
        referral_code: str,
        captcha_mode: str = "auto",
        max_concurrent: int = 0,
    ):
        self.num_workers = num_workers
        self.referral_code = referral_code
        self.captcha_mode = captcha_mode
        # Semaphore limits concurrent browsers to prevent OOM
        # Default: min(num_workers, 10) to be safe
        self.max_concurrent = max_concurrent or min(num_workers, 10)
        self.semaphore: asyncio.Semaphore | None = None
        self.stats = WorkerPoolStats()
        self.results: list[WorkerResult] = []
        self._proxies: list[str] = []

    async def _fetch_proxies(self) -> list[str]:
        """Fetch and validate enough proxies for all workers."""
        print(f"  [pool] Fetching proxies for {self.num_workers} workers...")
        proxies = get_n_proxies(self.num_workers, timeout=15)
        if len(proxies) < self.num_workers:
            print(
                f"  [pool] WARNING: Only {len(proxies)}/{self.num_workers} "
                f"working proxies available. Some workers will share IPs."
            )
        else:
            print(f"  [pool] Got {len(proxies)} working proxies")
        return proxies

    def _get_proxy_for_worker(self, worker_id: int) -> dict | None:
        """Assign proxy to worker via round-robin."""
        if not self._proxies:
            return None
        proxy_str = self._proxies[worker_id % len(self._proxies)]
        return {"server": f"http://{proxy_str}"}

    async def _run_single_worker(
        self,
        worker_id: int,
        account_num: int,
    ) -> WorkerResult:
        """Run single account creation with own browser + proxy."""
        async with self.semaphore:
            proxy_config = self._get_proxy_for_worker(worker_id)
            proxy_label = proxy_config["server"].split("//")[1] if proxy_config else "none"
            print(
                f"\n  [worker-{worker_id}] Starting account #{account_num} "
                f"(proxy: {proxy_label})"
            )

            start = time.time()
            try:
                from mimo_farmer.creator import create_account_with_retry

                result = await create_account_with_retry(
                    referral_code=self.referral_code,
                    captcha_mode=self.captcha_mode,
                    account_num=account_num,
                    proxy=proxy_config,
                )
                elapsed = time.time() - start

                if result and result.get("api_key"):
                    await self.stats.record_success()
                    print(
                        f"  [worker-{worker_id}] ✓ Account #{account_num} "
                        f"created ({elapsed:.0f}s)"
                    )
                    return WorkerResult(
                        worker_id=worker_id,
                        account_num=account_num,
                        success=True,
                        data=result,
                        elapsed=elapsed,
                    )
                else:
                    reason = "unknown"
                    if result:
                        if result.get("risk_control"):
                            reason = "risk control"
                        elif result.get("ip_blocked"):
                            reason = "IP blocked"
                        elif result.get("domain_flagged"):
                            reason = "domain flagged"
                        elif result.get("unsafe_email"):
                            reason = "unsafe email"
                    await self.stats.record_failure()
                    print(
                        f"  [worker-{worker_id}] ✗ Account #{account_num} "
                        f"failed: {reason} ({elapsed:.0f}s)"
                    )
                    return WorkerResult(
                        worker_id=worker_id,
                        account_num=account_num,
                        success=False,
                        data=result,
                        error=reason,
                        elapsed=elapsed,
                    )

            except Exception as exc:
                elapsed = time.time() - start
                await self.stats.record_failure()
                print(
                    f"  [worker-{worker_id}] ✗ Account #{account_num} "
                    f"exception: {exc} ({elapsed:.0f}s)"
                )
                return WorkerResult(
                    worker_id=worker_id,
                    account_num=account_num,
                    success=False,
                    error=str(exc),
                    elapsed=elapsed,
                )

    async def run(self, count: int) -> list[WorkerResult]:
        """Run parallel account creation.

        Args:
            count: Total accounts to create

        Returns:
            List of WorkerResult (all results, success and failure)
        """
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        self.stats = WorkerPoolStats(total=count)

        # Fetch proxies
        self._proxies = await self._fetch_proxies()
        if not self._proxies:
            print("  [pool] ERROR: No proxies available. Cannot run parallel mode.")
            return []

        # Stagger worker starts slightly to avoid thundering herd
        tasks = []
        for i in range(count):
            worker_id = i % self.num_workers
            task = asyncio.create_task(
                self._run_single_worker(worker_id, account_num=i + 1)
            )
            tasks.append(task)
            # Small stagger between task launches
            if i < self.num_workers:
                await asyncio.sleep(0.5)

        # Wait for all tasks — one failure doesn't stop others
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results, converting exceptions to failures
        self.results = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                self.results.append(
                    WorkerResult(
                        worker_id=i % self.num_workers,
                        account_num=i + 1,
                        success=False,
                        error=str(r),
                    )
                )
            else:
                self.results.append(r)

        return self.results

    def summary(self) -> str:
        """Return human-readable summary."""
        total = len(self.results)
        success = sum(1 for r in self.results if r.success)
        failed = total - success
        total_time = sum(r.elapsed for r in self.results)
        avg_time = total_time / total if total > 0 else 0

        lines = [
            f"\n{'=' * 60}",
            f"  Parallel Execution Summary",
            f"  Workers: {self.num_workers} | Concurrency: {self.max_concurrent}",
            f"  Total: {total} | Success: {success} | Failed: {failed}",
            f"  Total time: {total_time:.0f}s | Avg per account: {avg_time:.0f}s",
            f"{'=' * 60}",
        ]
        return "\n".join(lines)
