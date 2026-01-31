"""Demo thread-safe multi-threaded progress tracking."""
import sys
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure we can import zobar if running from source
sys.path.insert(0, os.path.abspath("src"))

from zobar import AnimatedProgressBar, ProgressBarGroup


def worker_task(pbar: AnimatedProgressBar, worker_id: int, items: int):
    """Simulate a worker processing items.

    Args:
        pbar: Thread-safe progress bar to update.
        worker_id: Worker identifier.
        items: Number of items to process.
    """
    for i in range(items):
        time.sleep(0.01)  # Simulate work
        pbar.update(1)


def run_demo():
    """Demo thread-safe progress tracking."""
    print("\n\033[1m🚀 Zobar Thread-Safe Demo\033[0m")
    print("Multiple threads updating the same progress bar safely\n")

    # Demo 1: Single progress bar with multiple threads
    print("\033[1m1. Single progress bar, multiple workers\033[0m")
    print("4 workers processing 100 items total:\n")

    # Create a thread-safe progress bar
    total_items = 100
    with AnimatedProgressBar(total=total_items, desc="Processing", thread_safe=True) as pbar:
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            items_per_worker = total_items // 4
            for i in range(4):
                future = executor.submit(worker_task, pbar, i, items_per_worker)
                futures.append(future)
            # Wait for all to complete
            for future in as_completed(futures):
                future.result()

    print()

    # Demo 2: Multiple progress bars with multiple threads
    print("\033[1m2. Multiple progress bars with separate workers\033[0m")
    print("3 independent tasks running in parallel:\n")

    def task_worker(pbar, task_id, count, delay):
        for i in range(count):
            time.sleep(delay)
            pbar.update(1)
            pbar.set_suffix(f"worker {task_id}")

    with ProgressBarGroup() as group:
        bar1 = group.add_bar(total=50, desc="Task A", color='cyan', thread_safe=True)
        bar2 = group.add_bar(total=30, desc="Task B", color='green', thread_safe=True)
        bar3 = group.add_bar(total=40, desc="Task C", color='magenta', thread_safe=True)

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(task_worker, bar1, "A", 50, 0.02),
                executor.submit(task_worker, bar2, "B", 30, 0.03),
                executor.submit(task_worker, bar3, "C", 40, 0.015),
            ]
            for future in as_completed(futures):
                future.result()

    print("\n✨ \033[1mThread-safe demo complete!\033[0m\n")


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        sys.stdout.write("\n")
        print("Demo cancelled.")
