from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Static, Header, Footer
from textual.reactive import reactive

from metrics import get_cpu_percent, get_memory


def fmt_bytes(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    x = float(n)
    for u in units:
        if x < 1024 or u == units[-1]:
            return f"{x:.1f} {u}"
        x /= 1024
    return f"{x:.1f} TB"


class MetricsView(Static):
    cpu = reactive(0.0)
    mem_used = reactive(0)
    mem_total = reactive(0)
    mem_pct = reactive(0.0)

    def on_mount(self) -> None:
        self.set_interval(0.2, self.update_metrics)

    def update_metrics(self) -> None:
        self.cpu = get_cpu_percent()
        used, total, pct = get_memory()
        self.mem_used, self.mem_total, self.mem_pct = used, total, pct

        self.update(
            "\n".join(
                [
                    f"CPU:    {self.cpu:10.1f} %",
                    f"Memory: {fmt_bytes(self.mem_used)} / {fmt_bytes(self.mem_total)}  ({self.mem_pct:10.1f}%)",
                ]
            )
        )


class TaskManagerTUI(App):
    CSS = """
    Screen { padding: 1; }
    MetricsView {
        border: round $primary;
        padding: 1 2;
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield MetricsView()
        yield Footer()


if __name__ == "__main__":
    TaskManagerTUI().run()
