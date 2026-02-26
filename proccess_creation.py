# Creates multiple single threaded processess that run in parallel 
# While the processes run, it'll get CPU% and Memory% every 0.2 seconds.

import multiprocessing as mp
import time
import psutil

#  This will run inside each child process. It performs simple CPU-heavy math.
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


def run_cpu_benchmark():
    num_procs = 4
    work_units = 20_000_000  # How many times the operation will run, change if its too fast or too slow
    operations = ["add", "sub", "mul", "div"]

    processes = []

    # Prime CPU reading
    psutil.cpu_percent(interval=None)

    start_time = time.perf_counter()

    # Start processes
    for i in range(num_procs):
        p = mp.Process(
            target=worker,
            args=(work_units, operations[i])
        )
        p.start()
        processes.append(p)

    # While processes run, keep sampling CPU and memory
    last_cpu = 0.0
    last_mem = 0.0

    for p in processes:
        while p.is_alive():
            last_cpu = psutil.cpu_percent(interval=None)
            last_mem = psutil.virtual_memory().percent
            time.sleep(0.2)

    # Wait for all to finish
    for p in processes:
        p.join()

    elapsed = time.perf_counter() - start_time

    return elapsed, last_cpu, last_mem