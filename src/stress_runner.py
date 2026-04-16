from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from metrics import get_memory

# Each worker allocates two 4096×4096 float64 matrices (≈128 MB each)
STRESS_CONFIG = {
    "workers": 4,
    "matrix_size": 4096,   # side length — memory per matrix = side² × 8 bytes
    "duration_s": 15,      # how long each worker runs
}

# A + B + result C are all in RAM at the same time during each multiply.
WORKER_MEMORY_MB = int(STRESS_CONFIG["matrix_size"] ** 2 * 8 * 3 / (1024 ** 2))


# ── Worker script (runs in a child subprocess) ────────────────────────────────
# subprocess.Popen avoids multiprocessing's resource tracker, which cannot
# start its own subprocess inside Textual's asyncio event loop.
# Each worker writes its final iteration count to result_path on exit so the
# parent can read it for the comparison metric without any live IPC.

def _worker_script(matrix_size: int, duration_s: float, result_path: str) -> str:
    return (
        "import numpy as np, time\n"
        f"A = np.random.rand({matrix_size}, {matrix_size})\n"
        f"B = np.random.rand({matrix_size}, {matrix_size})\n"
        "start = time.perf_counter()\n"
        "iters = 0\n"
        f"while time.perf_counter() - start < {duration_s}:\n"
        "    C = A @ B\n"
        "    m = C.max()\n"
        "    if m > 0: A = C / m\n"
        "    iters += 1\n"
        f"open({repr(result_path)}, 'w').write(str(iters))\n"
    )


def _iter_path(worker_idx: int) -> Path:
    return Path(tempfile.gettempdir()) / f"os_tui_w{worker_idx}.txt"


# ── Snapshot dataclass ────────────────────────────────────────────────────────

@dataclass
class StressSnapshot:
    status: str = "Idle"
    started_at: float = 0.0
    finished_at: float | None = None
    worker_count: int = STRESS_CONFIG["workers"]
    duration_s: float = STRESS_CONFIG["duration_s"]
    baseline_mem_pct: float = 0.0
    cpu_samples: list[float] = field(default_factory=list)
    mem_samples: list[float] = field(default_factory=list)
    current_cpu: float = 0.0
    current_mem: float = 0.0
    iteration_counts: list[int] = field(default_factory=list)

    @property
    def elapsed(self) -> float:
        if not self.started_at:
            return 0.0
        end = self.finished_at or time.perf_counter()
        return max(0.0, end - self.started_at)

    @property
    def peak_cpu(self) -> float:
        return max(self.cpu_samples) if self.cpu_samples else 0.0

    @property
    def avg_cpu(self) -> float:
        return sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0.0

    @property
    def peak_mem(self) -> float:
        return max(self.mem_samples) if self.mem_samples else 0.0

    @property
    def total_iterations(self) -> int:
        return sum(self.iteration_counts)

    @property
    def ops_per_sec(self) -> float:
        elapsed = self.elapsed
        return self.total_iterations / elapsed if elapsed > 0 else 0.0


# ── Runner ────────────────────────────────────────────────────────────────────

class StressRunner:
    def __init__(self) -> None:
        self.snapshot = StressSnapshot()
        self._processes: list[subprocess.Popen] = []

    @property
    def is_running(self) -> bool:
        return self.snapshot.status == "Running"

    def start(self) -> None:
        if self.is_running:
            return

        _, _, mem_pct = get_memory()
        cfg = STRESS_CONFIG
        n = cfg["workers"]
        self.snapshot = StressSnapshot(
            status="Running",
            started_at=time.perf_counter(),
            baseline_mem_pct=mem_pct,
            worker_count=n,
            duration_s=cfg["duration_s"],
        )

        # Clear any stale iteration files from a previous run.
        for i in range(n):
            _iter_path(i).unlink(missing_ok=True)

        self._processes = [
            subprocess.Popen(
                [sys.executable, "-c",
                 _worker_script(cfg["matrix_size"], cfg["duration_s"], str(_iter_path(i)))],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            for i in range(n)
        ]

    def rerun(self) -> None:
        if self.is_running:
            return
        for p in self._processes:
            if p.poll() is None:
                p.terminate()
        self.start()

    def poll(self, cpu: float, mem_pct: float) -> dict:
        if self.snapshot.status == "Running":
            self._sample_metrics(cpu, mem_pct)
            if self._processes and all(p.poll() is not None for p in self._processes) and self.snapshot.finished_at is None:
                self.snapshot.finished_at = time.perf_counter()
                self.snapshot.iteration_counts = self._read_iterations()
                self.snapshot.status = "Complete"
        return self._build_snapshot()

    def _sample_metrics(self, cpu: float, mem_pct: float) -> None:
        self.snapshot.current_cpu = cpu
        self.snapshot.current_mem = mem_pct
        if cpu > 0:
            self.snapshot.cpu_samples.append(cpu)
        self.snapshot.mem_samples.append(mem_pct)

    def _read_iterations(self) -> list[int]:
        counts = []
        for i in range(self.snapshot.worker_count):
            path = _iter_path(i)
            try:
                counts.append(int(path.read_text().strip()))
                path.unlink(missing_ok=True)
            except (OSError, ValueError):
                counts.append(0)
        return counts

    def _build_snapshot(self) -> dict:
        s = self.snapshot
        progress_pct = min(s.elapsed / s.duration_s * 100, 100.0) if s.duration_s > 0 else 0.0
        workers_out = [
            {
                "worker_id": i + 1,
                "name": f"Process {i + 1}",
                "progress_pct": 100.0 if p.poll() is not None else progress_pct,
                "done": p.poll() is not None,
            }
            for i, p in enumerate(self._processes)
        ]
        return {
            "status": s.status,
            "elapsed": s.elapsed,
            "config": STRESS_CONFIG,
            "worker_memory_mb": WORKER_MEMORY_MB,
            "workers": workers_out,
            "baseline_mem_pct": s.baseline_mem_pct,
            "current_cpu": s.current_cpu,
            "current_mem": s.current_mem,
            "peak_cpu": s.peak_cpu,
            "avg_cpu": s.avg_cpu,
            "peak_mem": s.peak_mem,
            "mem_delta": round(s.peak_mem - s.baseline_mem_pct, 1),
            "total_iterations": s.total_iterations,
            "ops_per_sec": round(s.ops_per_sec, 2),
        }
