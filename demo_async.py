"""Demo using async progress bar features."""
import asyncio
import sys
import os

# Ensure we can import zobar if running from source
sys.path.insert(0, os.path.abspath("src"))

from zobar import AnimatedProgressBar, async_progress_bar


async def async_generator(n: int):
    """Simple async generator for demo."""
    for i in range(n):
        await asyncio.sleep(0.02)
        yield i


async def demo_async_context_manager():
    """Demo async context manager."""
    print("\n\033[1m🔄 Async Context Manager Demo\033[0m\n")

    total = 50
    async with AnimatedProgressBar(total=total, desc="Async Processing", color='cyan') as pbar:
        for i in range(total):
            await asyncio.sleep(0.05)
            pbar.update(1)
            if i % 10 == 0:
                pbar.set_suffix(f"step={i}")

    print("✓ Async context manager demo complete\n")


async def demo_async_iterator():
    """Demo async iterator wrapper."""
    print("\033[1m🔄 Async Iterator Demo\033[0m\n")

    # Note: async generators don't support __len__, so we must pass total
    async for item in async_progress_bar(async_generator(100), total=100, desc="Async Items", color='green'):
        # Simulate async processing
        await asyncio.sleep(0.03)

    print("✓ Async iterator demo complete\n")


async def demo_multiple_tasks():
    """Demo multiple concurrent async tasks."""
    print("\033[1m🔄 Multiple Async Tasks Demo\033[0m\n")

    async def task(name: str, count: int, delay: float):
        async with AnimatedProgressBar(total=count, desc=name, color='blue') as pbar:
            for i in range(count):
                await asyncio.sleep(delay)
                pbar.update(1)

    # Run multiple tasks concurrently
    await asyncio.gather(
        task("Task A", 30, 0.03),
        task("Task B", 20, 0.05),
        task("Task C", 40, 0.02),
    )

    print("✓ Multiple async tasks demo complete\n")


async def run_all_demos():
    """Run all async demos."""
    print("\n\033[1m🚀 Zobar Async Demo\033[0m - Async/await support\n")

    await demo_async_context_manager()
    await demo_async_iterator()
    await demo_multiple_tasks()

    print("\n✨ \033[1mAll async demos complete!\033[0m\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_all_demos())
    except KeyboardInterrupt:
        sys.stdout.write("\033[?25h\n")
        print("Demo cancelled.")
