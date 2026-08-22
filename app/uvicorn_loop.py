import asyncio
import selectors


def create_event_loop(
    use_subprocess: bool = False,
) -> asyncio.AbstractEventLoop:
    del use_subprocess

    return asyncio.SelectorEventLoop(
        selectors.SelectSelector()
    )
