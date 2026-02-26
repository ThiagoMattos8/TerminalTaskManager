import psutil

# Returns the overall CPU usage for the whole system
def get_cpu_percent() -> float:
    return psutil.cpu_percent(interval=None)

# Returns memory usage percentage for the whole system
def get_memory() -> tuple[int, int, float]:
    vm = psutil.virtual_memory()
    return vm.used, vm.total, vm.percent
