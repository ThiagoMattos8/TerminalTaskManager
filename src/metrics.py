import psutil

# Cache to store process objects so their internal timers don't reset
_process_cache = {}

# Returns the overall CPU usage for the whole system
def get_cpu_percent() -> float:
    return psutil.cpu_percent(interval=None)

# Returns memory usage percentage for the whole system
def get_memory() -> tuple[int, int, float]:
    vm = psutil.virtual_memory()
    return vm.used, vm.total, vm.percent

# Returns CPU and Memory percentage for a specific process ID (PID)
def get_process_metrics(pid: int) -> tuple[float, float]:
    try:
        # If we haven't tracked this PID yet, create and prime the object
        if pid not in _process_cache:
            proc = psutil.Process(pid)
            proc.cpu_percent(interval=None)  # Prime the CPU tracker
            _process_cache[pid] = proc
        
        # Fetch the cached object
        proc = _process_cache[pid]
        
        # Now interval=None will properly compare against the last call!
        cpu = proc.cpu_percent(interval=None)
        mem = proc.memory_percent()
        return cpu, mem
        
    except psutil.NoSuchProcess:
        # If the process finished and closed before we check, clean the cache and return 0
        if pid in _process_cache:
            del _process_cache[pid]  
        return 0.0, 0.0