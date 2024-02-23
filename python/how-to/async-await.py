import asyncio
from datetime import datetime

RESET = "\033[0m"
GREEN = "\033[32m"
PURPLE = "\033[35m"


async def say(text: str, COLOR: str, repetitions: int):
    for _ in range(repetitions):
        print(f"{COLOR}{text}{RESET}")
        await asyncio.sleep(0)


async def main():
    start = datetime.now().timestamp()
    await asyncio.gather(say("Foo", GREEN, 2), say("Bar", PURPLE, 3))
    print(f"Execution time: {(datetime.now().timestamp() - start) * 1000} ms")

    task1 = asyncio.create_task(say("Bar", PURPLE, 3))
    task2 = asyncio.create_task(say("Foo", GREEN, 2))

    await task1
    await task2


if __name__ == "__main__":
    asyncio.run(main())
