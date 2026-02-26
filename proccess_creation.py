# Creates multiple single threaded processess that run in parallel 
# While the processes run, it'll get CPU% and Memory% every 0.2 seconds.

import os
import time
import multiprocessing as mp

import psutil

# This function runs inside a child process (not the main program). It performs a loop and produces a checksum to prove it ran.
def create_process(name, work_units, operation, output_queue):
    """
    Parameters:
      name: a label like "proccess1-add"
      work_units: how many loop iterations to run
      operation: "add", "sub", "mul", or "div"
      output_queue: a multiprocessing Queue used to send results back
    """
    pid = os.getpid()              # OS process ID
    start_time = time.perf_counter()

    # x is the running value (checksum-like)
    x = 1
    MOD = 1_000_000_007

    if operation == "add":
        for i in range(work_units):
            x = (x + i) % MOD

    elif operation == "sub":
        for i in range(work_units):
            x = (x - i) % MOD

    elif operation == "mul":
        for i in range(work_units):
            x = (x * (i + 1)) % MOD

    elif operation == "div":
        # Avoid floats to keep it more consistent
        for i in range(work_units):
            x = (x // 2) + (i % 97)
            x = x % MOD

    else:
        # If passed a bad operation like string, we stop.
        raise ValueError("Unknown operation: " + str(operation))

    end_time = time.perf_counter()
    seconds = end_time - start_time

    # Send results back to the parent process
    # It sends name, pid, how long it took, and checksum
    output_queue.put((name, pid, seconds, int(x)))

# Runs the benchmark with multiple processes in parallel.
def run_cpu_benchmark(num_procs=4, work_units=1_000_000, sample_interval=0.2):
    """
    Returns a dictionary with:
      - elapsed time
      - avg/max cpu percent, avg/max mem percent
      - per-process results
      - time series samples
    """

    # Assigns each process a different operation:
    operations = ["add", "sub", "mul", "div"]

    # Create a queue that child processes can write to
    output_queue = mp.Queue()

    processes = []

    # psutil.cpu_percent() sometimes needs a first call to "prime" it
    psutil.cpu_percent(interval=None)

    start_run = time.perf_counter()

    # Start all processes
    for i in range(num_procs):
        op = operations[i % len(operations)]
        name = "proccess" + str(i + 1) + "-" + op

        p = mp.Process(
            target=create_process,
            args=(name, work_units, op, output_queue),
            daemon=True
        )
        p.start()
        processes.append(p)

    # Sample CPU and memory while processes are alive
    samples = []  # each element will be (t, cpu, mem)

    while True:
        # Check if any process is still running
        any_alive = False
        for p in processes:
            if p.is_alive():
                any_alive = True
                break

        if not any_alive:
            break

        t = time.perf_counter() - start_run
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent

        samples.append((t, cpu, mem))

        time.sleep(sample_interval)

    # 3) Join processes to exit
    for p in processes:
        p.join()

    elapsed = time.perf_counter() - start_run

    # 4) Collect process results from the queue
    proc_results = []
    while not output_queue.empty():
        name, pid, seconds, checksum = output_queue.get()
        proc_results.append({
            "name": name,
            "pid": pid,
            "seconds": seconds,
            "checksum": checksum,
        })

    # Sort results so they appear in a nice order
    proc_results.sort(key=lambda r: r["name"])

    # 5) Compute averages and maximums
    if len(samples) == 0:
        avg_cpu = 0.0
        max_cpu = 0.0
        avg_mem = 0.0
        max_mem = 0.0
    else:
        cpu_values = [s[1] for s in samples]
        mem_values = [s[2] for s in samples]

        avg_cpu = sum(cpu_values) / len(cpu_values)
        max_cpu = max(cpu_values)

        avg_mem = sum(mem_values) / len(mem_values)
        max_mem = max(mem_values)

    # Return everything as a dictionarys
    return {
        "elapsed_s": elapsed,
        "avg_cpu": avg_cpu,
        "max_cpu": max_cpu,
        "avg_mem": avg_mem,
        "max_mem": max_mem,
        "proc_results": proc_results,
        "samples": samples,
        "num_procs": num_procs,
        "work_units": work_units,
        "sample_interval": sample_interval,
    }