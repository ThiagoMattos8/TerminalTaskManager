# Creates multiple single threaded processess that run in parallel.
import multiprocessing as mp
import psutil
import time

# This will run inside each child process. It performs simple CPU-heavy math.
def worker(work_units, operation):
    x = 1

    if operation == "add":
        for i in range(work_units):
            x += i

    elif operation == "sub":
        for i in range(work_units):
            x -= i

    elif operation == "mul":
        for i in range(work_units):
            x *= (i + 1)
            x %= 1_000_000_007  # prevents the number from growing too big

    elif operation == "div":
        for i in range(work_units):
            x //= 2
            x += i % 10

    else:
        raise ValueError("Unknown operation: " + str(operation))


def spawn_workers():
    num_procs = 4
    work_units = 80_000_000  
    operations = ["add", "sub", "mul", "div"]
    processes = []

    # Start the clock to measure how fast the OS can create the processes
    start_time = time.perf_counter()

    for i in range(num_procs):
        p = mp.Process(
            target=worker,
            args=(work_units, operations[i]),
            name=f"Worker-{operations[i]}"
        )
        p.start()
        processes.append(p)
        
        # Prime the CPU reading
        try:
            psutil.Process(p.pid).cpu_percent(interval=None)
        except psutil.NoSuchProcess:
            pass

    # Stop the boot clock right after the last process starts
    boot_time = time.perf_counter() - start_time

    return processes, start_time, boot_time