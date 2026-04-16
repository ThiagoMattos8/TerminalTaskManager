from __future__ import annotations

import psutil
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Footer, Header, Static

from metrics import (
    get_cpu_percent,
    get_cpu_per_core,
    get_memory,
    get_system_info,
)
from stress_runner import StressRunner


# ── Shared helpers ────────────────────────────────────────────────────────────

def render_bar(percent: float, width: int = 28) -> str:
    filled = min(width, max(0, round((percent / 100) * width)))
    return f"[green]{'▓' * filled}[/green]{'░' * (width - filled)} {percent:5.1f}%"


def _make_bar(percent: float, width: int = 18) -> str:
    filled = min(width, max(0, round((percent / 100) * width)))
    return "▓" * filled + "░" * (width - filled)


def _core_bar(percent: float, width: int = 6) -> str:
    filled = min(width, max(0, round((percent / 100) * width)))
    return f"[green]{'▓' * filled}[/green]{'░' * (width - filled)}"


# ── System panel (always visible at the top) ──────────────────────────────────

class SystemPanel(Static):
    def render_metrics(
        self,
        cpu: float,
        mem_pct: float,
        per_core: list[float],
        sys_info: dict,
    ) -> None:
        info = (
            f"{sys_info['os']}  ·  {sys_info['cpu']}  ·  "
            f"{sys_info['cores_str']}  ·  {sys_info['ram_gb']} GB RAM"
        )
        lines = [
            f"System Monitor  │  {info}",
            f"CPU:    {render_bar(cpu)}",
            f"Memory: {render_bar(mem_pct)}",
            "",
        ]

        # Per-core bars — 4 per row, bar width 6
        n = len(per_core)
        for row_start in range(0, n, 4):
            parts = [
                f"C{i + 1:<2} {_core_bar(per_core[i])} {per_core[i]:3.0f}%"
                for i in range(row_start, min(row_start + 4, n))
            ]
            prefix = "Cores:  " if row_start == 0 else "        "
            lines.append(prefix + "  ".join(parts))

        self.update("\n".join(lines))


# ── Stress Test panel ─────────────────────────────────────────────────────────

class StressPanel(Static):
    def render_snapshot(self, snap: dict) -> None:
        status = snap["status"]
        cfg = snap["config"]

        lines = [
            f"Status: {status}   Elapsed: {snap['elapsed']:.2f}s",
        ]

        if status != "Idle":
            lines += [
                "",
                f"CPU    peak {snap['peak_cpu']:.1f}%   avg {snap['avg_cpu']:.1f}%"
                f"   ·   Memory   baseline {snap['baseline_mem_pct']:.1f}%   delta {snap['mem_delta']:+.1f}%",
            ]

        lines += [
            "",
            f"{'Process':<14} {'Progress':<25} State",
            "─" * 48,
        ]

        for w in snap["workers"]:
            bar = _make_bar(w["progress_pct"])
            state = "[cyan]Done[/cyan]   " if w["done"] else "[green]Working[/green]"
            lines.append(
                f"{w['name']:<14} {bar} {w['progress_pct']:>5.1f}%  {state}"
            )

        if status == "Complete":
            total_iters = snap["total_iterations"]
            ops_sec = snap["ops_per_sec"]
            n_workers = cfg["workers"]
            per_proc = ops_sec / n_workers if n_workers > 0 else 0.0
            lines.extend([
                "",
                f"[green]Done in {snap['elapsed']:.2f}s"
                f"   ·   {total_iters} matrix ops"
                f"   ·   {per_proc:.2f} ops/s per process[/green]",
            ])

        self.update("\n".join(lines))


# ── Main application ──────────────────────────────────────────────────────────

class OSBenchmarkApp(App):
    CSS = """
    Screen {
        layout: vertical;
        padding: 1;
    }

    #system-panel {
        height: auto;
        margin-bottom: 1;
    }

    .panel {
        border: round green;
        padding: 0 1;
        height: 1fr;
    }

    #stress-panel {
        height: 1fr;
    }
    """

    BINDINGS = [
        ("s", "start",  "Start"),
        ("r", "rerun",  "Rerun"),
        ("q", "quit",   "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.stress_runner = StressRunner()
        self._sysinfo = get_system_info()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            yield SystemPanel(classes="panel", id="system-panel")
            yield StressPanel(classes="panel", id="stress-panel")
        yield Footer()

    def on_mount(self) -> None:
        psutil.cpu_percent(interval=None)
        psutil.cpu_percent(percpu=True, interval=None)
        self.set_interval(0.25, self.refresh_dashboard)

    def action_start(self) -> None:
        self.stress_runner.start()

    def action_rerun(self) -> None:
        self.stress_runner.rerun()

    def refresh_dashboard(self) -> None:
        cpu = get_cpu_percent()
        per_core = get_cpu_per_core()
        _, _, mem_pct = get_memory()

        self.query_one(SystemPanel).render_metrics(cpu, mem_pct, per_core, self._sysinfo)

        stress_snap = self.stress_runner.poll(cpu, mem_pct)
        self.query_one(StressPanel).render_snapshot(stress_snap)


if __name__ == "__main__":
    OSBenchmarkApp().run()
