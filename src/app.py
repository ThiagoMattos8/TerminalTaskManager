from proccess_creation import run_cpu_benchmark


def main():
    print("Starting benchmark (4 parallel processes)...\n")

    elapsed, last_cpu, last_mem = run_cpu_benchmark()

    print("=== Benchmark Finished ===")
    print(f"Total time: {elapsed:.3f} seconds")
    print(f"CPU% (last observed): {last_cpu:.1f}%")
    print(f"Memory% (last observed): {last_mem:.1f}%")
    print("\nDone.")


if __name__ == "__main__":
    main()