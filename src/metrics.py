import psutil


def get_cpu_percent() -> float:
    return psutil.cpu_percent(interval=None)


def get_cpu_per_core() -> list[float]:
    return psutil.cpu_percent(percpu=True, interval=None)


def get_memory() -> tuple[int, int, float]:
    vm = psutil.virtual_memory()
    return vm.used, vm.total, vm.percent


def format_bytes(value: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    current = float(value)
    for unit in units:
        if current < 1024 or unit == units[-1]:
            return f"{current:.1f} {unit}"
        current /= 1024
    return f"{current:.1f} TB"


def get_system_info() -> dict:
    """Collect static system information — call once at startup."""
    import platform
    import subprocess as _sp

    sys_name = platform.system()

    # OS name + version
    if sys_name == "Darwin":
        ver = platform.mac_ver()[0]
        os_str = f"macOS {ver}" if ver else "macOS"
    elif sys_name == "Linux":
        try:
            pretty = platform.freedesktop_os_release().get("PRETTY_NAME", "")
        except AttributeError:
            pretty = ""
        os_str = pretty or f"Linux {platform.release()[:20]}"
    else:
        os_str = f"{sys_name} {platform.release()}"

    # CPU model name — try sysctl on macOS, fall back to platform
    cpu_str = platform.processor() or platform.machine()
    if sys_name == "Darwin":
        try:
            out = _sp.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                stderr=_sp.DEVNULL, timeout=1,
            ).decode().strip()
            if out:
                cpu_str = out
        except Exception:
            pass

    # Core counts
    phys = psutil.cpu_count(logical=False) or 0
    logi = psutil.cpu_count(logical=True) or 0
    cores_str = f"{logi} cores" if phys == logi else f"{phys}p/{logi}t cores"

    return {
        "os": os_str,
        "cpu": cpu_str[:40],
        "cores_str": cores_str,
        "logical_cores": logi,
        "ram_gb": round(psutil.virtual_memory().total / (1024 ** 3), 1),
    }
