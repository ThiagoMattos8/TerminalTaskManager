import time
import os
from metrics import get_cpu_percent, get_memory, get_process_metrics
from proccess_creation import spawn_workers

def fmt_bytes(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    x = float(n)
    for u in units:
        if x < 1024 or u == units[-1]:
            return f"{x:.1f} {u}"
        x /= 1024
    return f"{x:.1f} TB"

def run_terminal_monitor():
    print("Starting OS Benchmark...")
    
    # Unpack the processes and our new timers
    processes, start_time, boot_time = spawn_workers()

    all_done = False
    
    # Keep looping and refreshing the screen until all workers finish
    while not all_done:
        # Clears the terminal screen
        os.system('cls' if os.name == 'nt' else 'clear')

        sys_cpu = get_cpu_percent()
        used, total, pct = get_memory()

        print("=== System Baseline ===")
        print(f"System CPU:    {sys_cpu:10.1f} %")
        print(f"System Memory: {fmt_bytes(used)} / {fmt_bytes(total)}  ({pct:10.1f}%)")
        print(f"Process Boot Time: {boot_time:.4f} seconds\n")
        
        print("=== Active Workers ===")
        
        all_done = True
        for p in processes:
            if p.is_alive():
                # If even one process is alive, we keep the main loop going
                all_done = False
                p_cpu, p_mem = get_process_metrics(p.pid)
                print(f"[{p.pid}] {p.name:<12} - CPU: {p_cpu:10.1f}% | Mem: {p_mem:10.1f}%")
            else:
                print(f"[{p.pid}] {p.name:<12} - FINISHED")

        # Wait 0.1 seconds before drawing the next frame
        time.sleep(0.1)

    # Calculate total execution time once the loop breaks
    total_time = time.perf_counter() - start_time
    print(f"\nBenchmark Complete! Total execution time: {total_time:.4f} seconds.")

if __name__ == "__main__":
    run_terminal_monitor()