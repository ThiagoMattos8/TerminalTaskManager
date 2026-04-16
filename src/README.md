# OS Threading Demo

This project is a Textual-based operating systems demo. It focuses on a single-process design and compares a `Single-Threaded` workload against a `Multi-Threaded` workload in a live terminal dashboard.

## Current Scope

- Runs a `Single-Threaded` demo with one worker thread
- Runs a `Multi-Threaded` demo with four worker threads
- Keeps both demos inside one main process model
- Shows a live dashboard with:
  - system CPU and memory summary
  - tab-based demo views
  - worker state, progress, and runtime
  - average CPU and total workload memory
  - shared counter, lock owner, and waiting thread count in the multi-threaded demo
- Starts each demo only when you trigger it from the keyboard

## Project Files

- `app.py`: Textual dashboard entrypoint
- `runner.py`: demo lifecycle and live snapshot logic
- `thread_benchmark.py`: worker thread behavior and shared-state updates
- `metrics.py`: system and process metric helpers
- `process_creation.py`: legacy process-based helper from the earlier project version
- `requirements.txt`: Python dependencies

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python3 app.py
```

## Controls

- Press `1` to view the `Single-Threaded` tab
- Press `2` to view the `Multi-Threaded` tab
- Press `s` to start the current tab
- Press `r` to rerun the current tab
- Press `q` to quit the dashboard

## Notes

- The workload stays simple on purpose so the thread behavior is easier to explain in class.
- The multi-threaded demo is meant to show shared memory and synchronization behavior, not guaranteed true core pinning on macOS.
- The app no longer starts benchmarks automatically when it launches.
