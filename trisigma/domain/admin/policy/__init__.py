import functools
import asyncio
import logging.config

def aio_raised_graceful_exit(*signals):
    """Cancels all tasks when one of given signals is received"""
    async def sig_handler(sig, _):
        logging.critical(f"Caught signal {sig}, starting graceful shutdown")
        tasks = [
            t for t in asyncio.all_tasks() if t is not
            asyncio.current_task()]
        [task.cancel() for task in tasks]
        await asyncio.gather(*tasks, return_exceptions=True)
        loop.stop()
        exit(0)
    loop = asyncio.get_event_loop()
    for sig in signals:
        loop.add_signal_handler(
            sig,
            functools.partial(
                asyncio.ensure_future,
                sig_handler(sig, loop)))

def aio_timed_resource_control(duration):
    """Blocks the event loop for the given duration in each iteration"""
    async def resource_control():
        while True:
            time.sleep(0.1)
            await asyncio.sleep(0)
    loop = asyncio.get_event_loop()
    loop.create_task(resource_control())


def logger_notification_on_root():
    FILENAME = 'config/logging.toml'
    try:
        logging.config.fileConfig(FILENAME)
    except FileNotFoundError:
        print(f"File {FILENAME} not found")
    except Exception as e:
        print(f"Error while reading {FILENAME}: {e}")

